import datetime, random, string
from _sha256 import sha256
from json import loads
from django.contrib.auth import authenticate, login
from django.core.validators import validate_email
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from knox.views import LoginView, LogoutView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, filters
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from rest_framework.views import APIView
from accounts import models, serializers, mails, sendsms
from knox.models import AuthToken


# User LoginView
class UserLoginView(LoginView):
    http_method_names = ['post']
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        s = serializers.LoginSerializer(data=self.request.data)
        s.is_valid(raise_exception=True)
        username_or_email = s.validated_data.get('user', None)
        password = s.validated_data.get('password', None)
        remember_me = s.validated_data.get('remember_me', 0)
        user = None

        # Validate if user provided username or password.
        try:
            validate_email(username_or_email)
            username = User.objects.filter(email=username_or_email)
            getUser = username
            if username.exists():
                username_or_email = username[0].username
        except ValidationError:
            getUser = User.objects.filter(username=username_or_email)

        if getUser.exists() and getUser[0].check_password(password):
            user = getUser[0]
            mail_verify = models.MailVerification.objects.filter(Q(user=user), Q(mail_type=0))
            if mail_verify.exists():
                mail = mail_verify[0]
                mail.time_limit = timezone.now() + datetime.timedelta(days=1)
                mail.hash_code = sha256((str(random.getrandbits(256)) + user.email).encode('utf-8')).hexdigest()
                mail.save()
                args, kwargs = [], {'mail_type': 1, 'id': mail.hash_code}
                mails.main(to_mail=user.email, *args, **kwargs)
                return Response({'message': 'Your mail Not verified, A verification mail sent to your mail, confirm it',
                                 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

            mobile_verify = models.MobileVerification.objects.filter(user=user)
            if mobile_verify.exists():
                mobile = mobile_verify[0]
                mobile.created_time = timezone.now() + datetime.timedelta(minutes=10)
                mobile.code = random.randint(100001, 999999)
                mobile.save()
                sendsms.sendsms(mobile=mobile.mobile, code=mobile.code)
                return Response({'message': mobile.mobile, 'error': -1}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username_or_email, password=password)
        if user is None:
            return Response({'message': 'No user found as per given credentials', 'error': 1},
                            status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        context = {}
        if remember_me == 0:
            context['token'] = AuthToken.objects.create(user=user, expires=datetime.timedelta(days=7))
        else:
            context['token'] = AuthToken.objects.create(user=user, expires=datetime.timedelta(days=90))
        context['error'] = 0
        context['user_id'] = user.pk
        context['user'] = user.groups.all()[0].name

        return Response(context, status=status.HTTP_200_OK)


# Logout User
class UserLogoutView(LogoutView):
    http_method_names = ['post']

    def post(self, request, format=None):
        super(UserLogoutView, self).post(request, format=None)
        return Response({'message': 'successfully logged out', 'error': 0})


# Register Devotee
class UserCreateView(CreateAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        if request.data['user_type'] == 'Admin':
            return Response({'message': "permission denied", 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        super(UserCreateView, self).create(request, *args, **kwargs)
        return Response({'message': 'Confirm your mobile along with the mail', 'error': 0})


class ValidateAdminLink(APIView):
    authentication_classes = []
    permission_classes = []
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        try:
            link = request.data['link']
        except KeyError:
            return Response({'error': 1})

        l = models.AdminLink.objects.filter(link=link)
        if (l.exists()) and (l[0].created_time + datetime.timedelta(minutes=30) > timezone.now()):
            return Response({'error': 0}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 1}, status=status.HTTP_400_BAD_REQUEST)


class GenerateAdminLink(APIView):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        request.data['link'] = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(60))
        s = serializers.AdminRegisterLinkGenerateSerializer(data=request.data)
        s.is_valid(raise_exception=False)
        s.validated_data['created_time'] = timezone.now()
        s.validated_data['created_by'] = request.user
        s.save()
        return Response({'link': s.validated_data['link']}, status=status.HTTP_200_OK)


# Register Admin
class AdminCreateView(CreateAPIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        try:
            if request.data['user_type'] != 'Admin':
                return Response({'message': "permission denied", 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            return Response({'message': 'Permission Denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

        link = get_object_or_404(models.AdminLink, link=self.kwargs['link'])
        if link.created_time + datetime.timedelta(minutes=30) > timezone.now():
            super(AdminCreateView, self).create(request, *args, **kwargs)
            link.delete()
            return Response({'message': 'Verify your mail and mobile', 'error': 0})
        else:
            link.delete()
            return Response({'message': 'Link Expired', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)



@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def MailVerificationView(request, id):
    mail_verify = models.MailVerification.objects.filter(hash_code=id)
    if (not mail_verify.exists()) or (mail_verify.exists() and mail_verify[0].mail_type != 0):
        context = {'message': 'Already verified mail', 'title': 'Mail Verification', 'error': 1}
        return render(request, 'accounts/mail_handle.html', context)
    if mail_verify[0].time_limit < timezone.now().date():
        context = {'message': 'Your time limit exceeded, please perform the operation again', 'error': 1,
                   'title': 'Mail Verification'}
        return render(request, 'accounts/mail_handle.html', context)

    context = {'message': 'Your mail successfully verified', 'error': 0}
    if not mail_verify[0].user.is_active:
        if not models.MobileVerification.objects.filter(user=mail_verify[0].user).exists():
            user = mail_verify[0].user
            user.is_active = True
            user.save()
    mail_verify.delete()
    return render(request, 'accounts/mail_handle.html', context)


class send(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        # refer link(https://stackoverflow.com/questions/51046730/django-post-data-query-dict-is-empty)
        email = loads(request.body.decode('utf-8'))['email']
        try:
            validate_email(email)
        except ValidationError:
            return Response({'message': 'Enter a valid email', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

        if not User.objects.filter(email=email).exists():
            return Response({'message': 'Entered mail is not found on our server!', 'error': 1},
                            status=status.HTTP_400_BAD_REQUEST)
        kwargs, get_mail = {}, models.MailVerification.objects.filter(Q(mail_id=email) & Q(mail_type=0))
        if not get_mail.exists():
            return Response({'message': 'Your mail is already verified!', 'error': 1},
                            status=status.HTTP_400_BAD_REQUEST)
        if get_mail[0].time_limit > timezone.now().date():
            return Response({'message': 'your account is already under verification, confirm your mail', 'error': 1},
                            status=status.HTTP_400_BAD_REQUEST)
        mail = models.MailVerification.objects.get(Q(mail_id=email), Q(mail_type=0))
        mail.time_limit = timezone.now().date() + datetime.timedelta(days=1)
        mail.save()
        kwargs = {'mail_type': 0, 'id': mail.hash_code}
        mails.main(to_mail=mail.mail_id, **kwargs)
        return Response({'message': 'Verification mail sent to your account', 'error': 0},
                        status=status.HTTP_202_ACCEPTED)


# Resend mobile verification
class ResendMobileVerify(APIView):
    http_method_names = ['post']
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            mobile = request.data['mobile']
        except KeyError:
            return Response({'message': 'Mobile number needed!!', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        query = models.MobileVerification.objects.filter(mobile=mobile)
        if not query.exists():
            return Response({'message': 'Mobile number not found!!', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        verify = query[0]
        verify.created_time = timezone.now() + datetime.timedelta(minutes=10)
        verify.code = random.randint(100001, 999999)
        verify.save()
        sendsms.sendsms(mobile, verify.code)
        return Response({'message': 'Message sent', 'error': 0}, status=status.HTTP_200_OK)


# mobile Verification.
class MobileVerifyView(APIView):
    authentication_classes = []
    http_method_names = ['post']
    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            mobile = request.data['mobile']
            code = request.data['code']
        except KeyError:
            return Response({'message': 'Enter the OTP', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        verify = models.MobileVerification.objects.filter(Q(code=code), Q(mobile=mobile))
        if verify.exists():
            if verify[0].created_time > timezone.now():
                user = verify[0].user
                user.profile.mobile = verify[0].mobile
                user.profile.save()

                if not verify[0].user.is_active:
                    if not models.MailVerification.objects.filter(user=verify[0].user).exists():
                        user = verify[0].user
                        user.is_active = True
                        user.save()
                verify.delete()
                return Response({'message': 'Successfully verified', 'error': 0}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'OTP time expired', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        else:
                return Response({'message': 'Invalid OTP', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)


class UserUpdateView(RetrieveUpdateAPIView):
    serializer_class = serializers.UserSettingSerializer

    def get_queryset(self):
        return User.objects.filter(pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        if self.get_object() != request.user and request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        context = super(UserUpdateView, self).get(request, *args, **kwargs)
        return context

    def patch(self, request, *args, **kwargs):
        if self.get_object() != request.user:
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        mobile_change, email_change = 0, 0

        try:
            state = request.data['profile']['state']
            if state != request.user.profile.state:
                request.data['profile']['state'] = request.user.profile.state
        except KeyError:
            pass

        try:
            email = request.data['email']
            try:
                validate_email(email)
            except ValidationError:
                return Response({'message': 'enter a valid data', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
            email_change, mobile_change = 0, 0
            if email != request.user.email:
                # user has changed the email, append the context
                email_change = 1
        except KeyError:
            pass

        try:
            mobile = request.data['profile']['mobile']
            request.data['profile']['mobile'] = request.user.profile.mobile
            if mobile != request.user.profile.mobile:
                # User has changed the mobile.
                mobile_change = 1
        except KeyError:
            pass

        if mobile_change == 1:
            s = serializers.ProfileSerializer(data={'mobile': mobile})
            s.is_valid(raise_exception=True)
            # mobile number is updated, send a OTP
            time, code = timezone.now() + datetime.timedelta(minutes=10), random.randint(100000, 999999)
            mobile_verify = models.MobileVerification.objects.filter(user=request.user)
            if mobile_verify.exists():
                mobile_verify = mobile_verify[0]
                mobile_verify.code = code
                mobile_verify.created_time = time
                mobile_verify.mobile = mobile
                mobile_verify.save()
            else:
                models.MobileVerification.objects.create(user=request.user, code=code, created_time=time, mobile=mobile)
            sendsms.sendsms(mobile=mobile, code=code)
        context = super(UserUpdateView, self).patch(request, *args, **kwargs)
        if email_change == 1 and mobile_change == 1:
            context.data['message'] = 'A validation message is sent to your mobile and email'
        elif email_change == 1:
            context.data['message'] = 'A validation message is sent to your email'
        elif mobile_change == 1:
            context.data['message'] = 'An OTP sent to mobile'
        else:
            context.data['message'] = 'Profile successfully updated!'

        return context


class UserPasswordUpdateView(UpdateAPIView):
    serializer_class = serializers.UserPasswordUpdateSerializer

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        if not request.user.check_password(s.validated_data['password']):
            return Response({'message': 'Enter correct current password', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        user = self.get_object()
        user.set_password(s.validated_data['new_password'])
        user.save()

        # delete all the login instances of the user (except current one) --will be updated soon.
        return Response({'message': 'Password successfully updated', 'error': 0})


# User Password Forgot operations.
class ForgotUserPasswordUpdateView(UpdateAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = serializers
    http_method_names = ['get', 'post']

    def get_queryset(self):
        return models.MailVerification.objects.filter(hash_code=self.kwargs['id'])

    def get_object(self):
        return get_object_or_404(self.get_queryset()).user

    def get(self, request, *args, **kwargs):
        if not self.get_queryset().exists():
            context = {'message': 'No Link Found as per given requirement', 'error': 1, 'title': 'Password Updation'}
            return render(request, 'accounts/mail_handle.html', context=context)
        if self.get_queryset()[0].time_limit < timezone.now().date():
            return render(request, 'accounts/mail_handle.html', {
                'message': 'Link expired, please perform the operation again',
                'error': 1,
                'title': 'Password Updation'})

        return render(request, 'accounts/password_update.html', {'mail_code': self.kwargs['id']})

    def post(self, request, *args, **kwargs):
        self.get_object()
        if request.data['password1'] == '' or request.data['password2'] == '':
            context = {'message': 'Fill the form completely', 'error': 1, 'title': 'Password updation', 'mail_code':
                       self.kwargs['id']}
            return render(request, 'accounts/password_update.html', context)
        if len(request.data['password1']) < 8:
            context = {'message': 'Min password length is 8', 'error': 1, 'title': 'Password Updation', 'mail_code':
                self.kwargs['id']}
            return render(request, 'accounts/password_update.html', context)
        if request.data['password1'] != request.data['password2']:
            context = {'message': 'Fill the same passwords both the times', 'error': 1, 'title': 'Password updation',
                       'mail_code': self.kwargs['id']}
            return render(request, 'accounts/password_update.html', context)
        # update user
        user = self.get_object()
        user.set_password(request.data['password1'])
        user.save()
        # delete all the user logged-in instances
        AuthToken.objects.filter(user=self.get_object()).delete()
        # delete mail verification
        self.get_queryset().delete()
        context = {'message': 'Password successfully updated', 'error': 0, 'title': 'Password Updation'}
        return render(request, 'accounts/mail_handle.html', context)


# User Password Forgot operations.
@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def password_forgot(request):
    email = loads(request.body.decode('utf-8'))['email']
    try:
        validate_email(email)
    except ValidationError:
        return Response({'message': 'Enter the valid mail', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
    if not User.objects.filter(email=email).exists():
        return Response({'message': 'No user exists with such email', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
    verify = models.MailVerification.objects.filter(user=User.objects.get(email=email), mail_type=2)
    if verify.exists():
        mail = verify[:1].get()
        mail.time_limit = timezone.now() + datetime.timedelta(days=1)
        hash_code = mail.hash_code
        mail.save()
    else:
        hash_code = sha256((str(random.getrandbits(256)) + email).encode('utf-8')).hexdigest()
        models.MailVerification(user=User.objects.get(email=email), hash_code=hash_code, mail_id=email,
                        time_limit=(datetime.datetime.now().date() + datetime.timedelta(days=1)), mail_type=2).save()
    kwargs = {'mail_type': 2, 'id': hash_code}
    mails.main(to_mail=email, **kwargs)
    return Response({'message': 'Verification mail sent, confirm it.', 'error': 0}, status=status.HTTP_200_OK)


class EmailChangeVerifyView(APIView):
    authentication_classes = []
    permission_classes = []

    def get_object(self):
        verify = models.MailVerification.objects.filter(hash_code=self.kwargs['id'])
        if verify.exists():
            return verify[0]
        else:
            return None

    def get(self, request, *args, **kwargs):
        mail = self.get_object()
        if mail is None:
            context = {'message': 'Email verification failed, please try again', 'error': 1,
                       'title': 'Email Updation'}
            return render(request, 'accounts/mail_handle.html', context)
        else:
                if mail.time_limit < timezone.now().date():
                    context = {'message': 'The one day time limit for the verification reached,'
                            ' perform the operation again', 'error': 1, 'title': 'Email Updation' }
                    return render(request, 'accounts/mail_handle.html', context)
                mail.user.email = mail.mail_id
                mail.user.save()
                mail.delete()
                context = {'message': 'Email successfully updated', 'error': 0, 'title': 'Email Updation'}
                return render(request, 'accounts/mail_handle.html', context)


class UserListView(ListAPIView):
    serializer_class = serializers.UserListSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('username',)

    def get_queryset(self):
            return User.objects.all()

    def get(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        return super(UserListView, self).get(request, *args, **kwargs)


class UserDetailView(DestroyAPIView):
    serializer_class = serializers
    http_method_names = ['delete']

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['user_id'])

    def delete(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

        if request.user == self.get_object():
            return Response({'message': 'You can\'t delete yourself'})

        super(UserDetailView, self).delete(request, *args, **kwargs)
        return Response({'message': 'Successfully deleted the user', 'error': 0}, status=status.HTTP_200_OK)