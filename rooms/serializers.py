import random

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
import math
from . import models
from rest_framework import serializers


class BlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Block
        fields = ['pk', 'name']
        read_only_fields = ['pk']


class RoomListSerializer(serializers.ModelSerializer):
    block = BlockSerializer()
    blocked = serializers.SerializerMethodField()

    def get_blocked(self, obj):
        blocked = models.BlockedRooms.objects.filter(room_no=obj)
        if blocked.exists():
            return True
        else:
            return False

    class Meta:
        model = models.Room
        fields = ['pk', 'room_no', 'block', 'blocked', 'capacity']


class UserBookingSerializer(serializers.ModelSerializer):
    rooms = RoomListSerializer(many=True)
    upload_new_proof = serializers.SerializerMethodField()
    booked_by = serializers.SerializerMethodField()

    def get_booked_by(self, obj):
        return obj.booked_by.username

    def get_upload_new_proof(self, obj):
        user = self.context['request'].user
        if user == obj.booked_by:
            return True
        else:
            return False

    class Meta:
        model = models.Bookings
        fields = ['pk', 'reference', 'rooms', 'start_date', 'end_date', 'booked_by', 'booking_type',
                  'proof', 'user_booked', 'checkedin', 'upload_new_proof']


class RoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Room
        fields = '__all__'
        read_only_fields = ['pk']
