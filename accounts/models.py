from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username


class MailVerification(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hash_code = models.CharField(max_length=200, null=True, blank=True)
    mail_id = models.CharField(max_length=200)
    time_limit = models.DateField(null=True)
    mail_type = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username

    # Mail Types:
    # 1. 0 --> User registration verification
    # 2. 1 --> User Forgot password
    # 3. 2 --> User email change


class MobileVerification(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    created_time = models.DateTimeField(default=timezone.now())
    status = models.BooleanField(default=False)
    mobile = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return self.user.username


class AdminLink(models.Model):
    link = models.CharField(max_length=200)
    created_time = models.DateTimeField(default=timezone.now())
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)



