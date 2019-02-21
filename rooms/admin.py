from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Block)
admin.site.register(models.Room)
admin.site.register(models.BookedUsers)
admin.site.register(models.Booking)
admin.site.register(models.BookingPayment)
