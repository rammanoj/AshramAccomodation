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
    room_no = models.CharField(max_length=20, unique=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE)
    floor = models.IntegerField(default=0)
    capacity = models.IntegerField(default=1)
    room_type = models.CharField(choices=ROOM_TYPES, max_length=5, default='N-AC')
    available = models.BooleanField(default=True)

    # Avialable values:
    # True --> Not blocked, the user can apply
    # False --> Blocked by admin for some purpose, should not be appeared in the search.

    class Meta:
        unique_together=(('room_no', 'block'),)

    def __str__(self):
        return self.room_no + " -- " + self.block.name


class Bookings(models.Model):
    reference = models.CharField(max_length=250, null=True, blank=True)
    rooms = models.ManyToManyField(Room, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    booked_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    booking_type = models.BooleanField(default=False)
    user_booked = models.CharField(max_length=40, null=True, blank=True)
    proof = models.FileField(upload_to='uploads/id_proofs', blank=True, null=True)
    checkedin = models.BooleanField(default=False)

    def __str__(self):
        return self.reference


class BlockedRooms(models.Model):
    room_no = models.ForeignKey(Room, on_delete=models.CASCADE, unique=True)
    blocked_by = models.ForeignKey(User, on_delete=models.CASCADE)
    blocked_on = models.DateTimeField()

    def __str__(self):
        return self.room_no.__str__()
