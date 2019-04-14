import datetime
import random
from _sha256 import sha256
from django.contrib.auth.models import User, Group
from django.core.validators import validate_email
from django.db.models import Q
from django.utils import timezone

from . import sendsms
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from accounts import models, mails


def password_check(password):
    if password is None:
        raise serializers.ValidationError('Fill the form completely!')
    if len(password) < 8:
        raise serializers.ValidationError('Password must have min length of 8.')
    return password


# User Login
class LoginSerializer(serializers.Serializer):
        user = serializers.CharField(required=True, max_length=50)
        password = serializers.CharField(required=True, max_length=50, validators=[password_check])
        remember_me = serializers.IntegerField(default=0)

        def validate_user(self, user):
            if user is None:
                raise serializers.ValidationError('Fill the form completely!')
            return user


# User signup
class UserSerializer(serializers.ModelSerializer):

    confirm_password = serializers.CharField(max_length=50, required=True, validators=[password_check], write_only=True)
    password = serializers.CharField(max_length=50, required=True, validators=[password_check])
    mobile = serializers.CharField(max_length=100, required=False, allow_blank=True)
    user_type = serializers.CharField(max_length=30, required=True, write_only=True)
    email = serializers.EmailField(required=True)

    def validate_username(self, username):
        if User.objects.filter(username=username):
            raise serializers.ValidationError('Username already chosen!')

        if len(username) < 8:
            raise serializers.ValidationError('Username min length is 8')
        return username

    def validate_email(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError('Enter a valid email')

        if User.objects.filter(email=email):
            raise serializers.ValidationError('Email already chosen!')
        return email

    def validate_mobile(self, mobile):
        if len(mobile) < 10:
            raise serializers.ValidationError('Mobile number has to be at least 10 digits!')

        if models.Profile.objects.filter(mobile=mobile).exists():
            raise serializers.ValidationError('Mobile number is already chosen!!')

        return mobile

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError('Enter same passwords both the times!')

        if attrs['user_type'] not in ['Admin', 'Devotee']:
            raise serializers.ValidationError('Enter a valid userId')
        return attrs

    def create(self, validated_data):

        # create the user
        user = User.objects.create(username=validated_data['username'], email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.save()

        g = Group.objects.get(name=validated_data['user_type'])
        g.user_set.add(user)

        # Add profile to the user
        profile = models.Profile.objects.create(user=user, mobile=validated_data['mobile'])
        profile.save()

        # Save the MailVerification instance
        hash_code = sha256((str(random.getrandbits(256)) + validated_data['email']).encode('utf-8')).hexdigest()
        mail = models.MailVerification(user=user, hash_code=hash_code, mail_id=validated_data['email'],
                                       time_limit=(datetime.datetime.now().date() + datetime.timedelta(days=1)), mail_type=0)
        mail.save()

        code = int(random.random()*1000000)
        mobile = models.MobileVerification(user=user, code=code, created_time=timezone.now() + datetime.timedelta(minutes=10),
                                           mobile=validated_data['mobile'])
        mobile.save()

        # send verification mail to the user (presently not using celery, so send the mail directly)
        kwargs = {'mail_type': 0, 'id': hash_code}
        mails.main(to_mail=validated_data['email'], **kwargs)
        sendsms.sendsms(mobile=validated_data['mobile'], code=code)
        return user

    class Meta:
        model = User
        fields = ('pk', 'username', 'password', 'email', 'confirm_password', 'mobile', 'user_type')
        read_only_fields = ('pk',)


class ProfileSerializer(serializers.ModelSerializer):

    def validate_mobile(self, mobile):
        if len(mobile) < 10:
            raise serializers.ValidationError('Mobile number does not meet the requirements')
        if models.Profile.objects.filter(mobile=mobile).exists():
            raise serializers.ValidationError('Mobile number already chosen!')
        return mobile

    class Meta:
        model = models.Profile
        fields = ('pk', 'mobile')


class UserListSerializer(serializers.ModelSerializer):
    mobile = serializers.SerializerMethodField()
    disabled = serializers.SerializerMethodField()

    def get_disabled(self, obj):
        return not obj.is_active

    def get_mobile(self, obj):
        return obj.profile.mobile

    class Meta:
        model = User
        fields = ('username', 'pk', 'email', 'mobile', 'disabled')
        read_only_fields = ('pk',)


class UserSettingSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        return obj.groups.all()[0].name

    def validate_username(self, username):
        if User.objects.filter(username=username).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError('Username already exists!')
        if len(username) < 8:
            raise serializers.ValidationError('Username min length is 8')
        return username

    def validate_email(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise serializers.ValidationError('Enter a valid email')
        if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError('email already exists!')
        if models.MailVerification.objects.filter(Q(mail_id=email), Q(mail_type=0)):
            raise serializers.ValidationError('Verify the current mail first!!')
        return email

    def update(self, instance, validated_data):
        # email is changed, send a verification mail
        try:
            if instance.email != validated_data['email']:
                verify = models.MailVerification.objects.filter(Q(user=instance) & Q(mail_type=2))
                if verify.exists():
                    mail = verify[:1].get()
                    mail.email = validated_data['email']
                    mail.time_limit = datetime.datetime.now().date() + datetime.timedelta(days=1)
                    mail.save()
                    hash_code = mail.hash_code
                else:
                    hash_code = sha256(
                        (str(random.getrandbits(256)) + validated_data['email']).encode('utf-8')).hexdigest()
                    mail = models.MailVerification(user=instance, hash_code=hash_code, mail_id=validated_data['email'],
                                                   time_limit=(datetime.datetime.now().date() + datetime.timedelta(
                                                       days=1)), mail_type=2)
                    mail.save()
                kwargs = {'mail_type': 1, 'id': hash_code}
                mails.main(to_mail=validated_data['email'], **kwargs)
                validated_data['email'] = instance.email
        except KeyError:
            pass
        return super(UserSettingSerializer, self).update(instance, validated_data)

    class Meta:
        model = User
        fields = ('pk', 'username', 'email', 'profile', 'role')
        read_only_fields = ('pk',)


class UserPasswordUpdateSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if len(attrs['new_password']) < 8:
            raise serializers.ValidationError('Password length can\'t be less than 8')
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError('Confirm your password correctly')
        return attrs

    class Meta:
        model = User
        fields = ('password', 'confirm_password', 'new_password')


class ForgotPasswordUpdateView(serializers.Serializer):
    password1 = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)


class AdminRegisterLinkGenerateSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(required=False)
    created_time = serializers.DateTimeField(required=False)

    class Meta:
        model = models.AdminLink
        fields = ['pk', 'link', 'created_time', 'created_by']
        read_only_fields = ('pk',)