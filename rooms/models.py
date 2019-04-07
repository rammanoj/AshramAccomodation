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
    room_type = models.CharField(choices=ROOM_TYPES, max_length=5, default='N-AC')
    available = models.BooleanField(default=True)

    # Avialable values:
    # True --> Not blocked, the user can apply
    # False --> Blocked by admin for some purpose, should not be appeared in the search.

    class Meta:
        unique_together=(('room_no', 'block'),)

    def __str__(self):
        return self.room_no + " -- " + self.block.name


class BookedUsers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=None, blank=True)
    username = models.CharField(max_length=40, null=True, blank=True)
    id_proof = models.FileField(upload_to='uploads/id_proofs/')
    booked_date = models.DateTimeField(default=timezone.now())


# In a single booking a user can book multiple rooms with different check_in and check_out dates with the below model.
class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    # All the bookings to the room will be deleted, if the room is deleted

    check_in = models.DateTimeField()
    check_out = models.DateTimeField()
    status = models.IntegerField(default=1)
    # Three values for attribute 'status'
    # -1 => Room is cancelled by the users. -->room is free for availability
    # 0 => Room is not yet taken or empty out -->room is busy on those dates
    # 1 => Room is currently under usage. -->room is busy on those dates

    reference = models.CharField(max_length=200)
    booked_by = models.ForeignKey(BookedUsers, on_delete=models.CASCADE)

    def __str__(self):
        return self.room.room_no + " " + self.booked_by.user.username


class BookingPayment(models.Model):
    reference = models.ForeignKey(BookedUsers, on_delete=models.CASCADE)
    amount = models.CharField(max_length=20)
    payment_method = models.CharField(max_length=40)
    status = models.BooleanField(default=False)


#     cases in booking rooms:
# 1. either the room is booked and living -- -1, cancelled -- 1
# 2. if the room is free