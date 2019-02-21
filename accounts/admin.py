from django.contrib import admin
from . import models

# Register your models here.

admin.site.register(models.Profile)
admin.site.register(models.MailVerification)
admin.site.register(models.MobileVerification)
admin.site.register(models.AdminLink)
