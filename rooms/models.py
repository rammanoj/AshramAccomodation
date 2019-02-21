from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.


class Block(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Room(models.Model):
    ROOM_TYPES = (
        ('AC', 'AC Rooms'),
        ('N-AC', 'Non-AC Rooms')
    )
    room_no = models.CharField(max_length=20)
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    floor = models.IntegerField(default=0)
    capacity = models.IntegerField(default=1)
    room_type = models.CharField(choices=ROOM_TYPES, max_length=3, default='N-AC')
    available= models.BooleanField(default=True)

    def __str__(self):
        return self.room_no


class BookedUsers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True)
    username = models.CharField(max_length=40, default=None,blank=True)
    id_proof = models.FileField(upload_to='uploads/id_proofs/')
    booked_date = models.DateTimeField(default=timezone.now())


class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    # All the bookings to the room will be deleted, if the room is deleted

    check_in = models.DateTimeField()
    check_out = models.DateTimeField()
    status = models.IntegerField(default=1)
    # Three values for attribute'status'
    # -1 => Room is canceled by the users in past
    # 0 => Room is not avilable (2 cases: 1. blocked, 2. Checked to room)
    # 1 => Room is currently under usage.

    reference = models.CharField(max_length=200)
    booked_by = models.ForeignKey(BookedUsers, on_delete=models.CASCADE)

    def __str__(self):
        return self.room.room_no + " " + self.booked_by.user.username


class BookingPayment(models.Model):
    reference = models.ForeignKey(BookedUsers, on_delete=models.CASCADE)
    amount = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=40)
    status = models.BooleanField(default=False)

