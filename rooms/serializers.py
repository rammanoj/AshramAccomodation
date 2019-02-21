from . import models
from rest_framework import serializers


class BookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Booking
        fields = ['pk', 'room', 'check_in', 'booked_date', 'check_out', 'reference']
        read_only_fields = ['pk']


class BookedUsers(serializers.ModelSerializer):
    rooms = BookingSerializer(many=True)

    class Meta:
        model = models.BookedUsers
        fields = ['pk', 'user', 'username', 'id_proof', 'rooms']


class BlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Block
        fields = ['pk', 'name']
        read_only_fields = ['pk']

