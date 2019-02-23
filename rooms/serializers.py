import random

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
import math
from . import models
from rest_framework import serializers


class BookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Booking
        fields = ['pk', 'room', 'check_in', 'booked_date', 'check_out', 'reference']
        read_only_fields = ['pk']


class BookedUsers(serializers.ModelSerializer):
    rooms = BookingSerializer(many=True)

    def update(self, instance, validated_data):
        room = validated_data.get('rooms', None)
        pass

    class Meta:
        model = models.BookedUsers
        fields = ['pk', 'user', 'username', 'id_proof', 'rooms']


class BlockSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Block
        fields = ['pk', 'name']
        read_only_fields = ['pk']


class RoomListSerializer(serializers.ModelSerializer):

    class Meta:
        model=models.Room
        fields=['pk', 'room_no', 'block', 'avialable']


class RoomSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Room
        fields = '__all__'
        read_only_fields = ['pk']


class RoomBookingSerializer(serializers.Serializer):
    from_date = serializers.DateTimeField(required=True)
    to_date = serializers.DateTimeField(required=True)
    rooms = serializers.ListField(required=False)
    capacity=serializers.IntegerField(required=True)
    room_type = serializers.CharField(required=False, max_length=10)
    id_proof = serializers.FileField(required=True)
    expected_room_members = serializers.IntegerField(required=False)

    def validate_from_date(self, from_date):
        if from_date < timezone.now().date():
            raise serializers.ValidationError('From date has to be prior to today!!')
        return from_date

    def validate_to_date(self, to_date):
        if to_date < timezone.now().date():
            raise serializers.ValidationError('Check out date has to be prior to today')
        return to_date

    def validate(self, attrs):
        if attrs['from_date'] >= attrs['to_date']:
            raise serializers.ValidationError('Checkout date has to be prior to checkin date')

        # Check if room ia avialable
        try:
            rooms = models.Room.objects.filter(room_no__in=attrs['room'])
            total_capacity = sum([i.capacity for i in rooms])
            if total_capacity < attrs['capacity']:
                raise serializers.ValidationError('There are no rooms avilable for the given dates')
        except KeyError:
            booked_rooms = models.Room.objects.filter(Q(booking__status=0), Q(booking__status=1))
            free_rooms = booked_rooms.filter(Q(Q(booking__check_in__gt=attrs['from_date']), Q(booking__check_in__gt=attrs['to_date']))
                                | Q(booking__check_in__lt=attrs['from_date']), Q(booking__check_out__lt=attrs['to_date']))
            booked_rooms = booked_rooms.exclude(free_rooms)
            rooms = models.Room.objects.all().exclude(booked_rooms)
            rooms = rooms.filter(capacity=attrs['exp_capacity'])
            if len(rooms) < math.ceil(attrs['capacity']/attrs['exp_capacity']):
                raise serializers.ValidationError('There are no rooms for the given dates!')
            else:
                attrs['rooms'] = rooms[0:math.ceil(attrs['capacity']/attrs['exp_capacity'])]
        return attrs

    def create(self, validated_data):
        try:
            username = validated_data['username']
        except KeyError:
            username = None

        reference = str(random.randint(100000000000, 1000000000000))
        with transaction.atomic():
            if username is None:
                booking = models.BookedUsers.objects.create(user=validated_data['user'], username=username, id_proof=validated_data['id_proof'],
                                                  booked_date=timezone.now().date())
            else:
                booking = models.BookedUsers.objects.create(user=None, username=username,
                                                  id_proof=validated_data['id_proof'],
                                                  booked_date=timezone.now().date())
            for i in validated_data['rooms']:
                models.Booking.objects.create(room=i, check_in=validated_data['attrs'], check_out=validated_data['attrs'],
                                              status=0, reference=reference, booked_by=self.context['request'].user)
        return booking

    def update(self, instance, validated_data):
        pass


    class Meta:
        fields = ('from_date', 'to_date', 'rooms', 'capacity', 'room_type', 'id_proof', 'exp_capacity', 'username', 'user')
