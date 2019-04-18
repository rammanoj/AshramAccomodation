import json
import string
import sys
from random import choice
from django.db import transaction
import datetime
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts import mails
from accounts import sendsms
from . import serializers, models
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, CreateAPIView, \
    DestroyAPIView


# Notifies the user
def notifyuser(booking, type):
    if booking.booking_type is False:
        return 0

    email, mobile, args, kwargs = booking.booked_by.email, booking.booked_by.profile.mobile, [], {}
    kwargs['reference'] = booking.reference
    kwargs['rooms'] = ''.join(str(i.room_no)+',' for i in booking.rooms.all())[:-1]
    l = list(set(i.block.name for i in booking.rooms.all()))
    kwargs['blocks'] = ''.join(str(j) + "," for j in l)[:-1]
    kwargs['start_date'] = booking.start_date.strftime("%Y %M %d %H:%m")
    kwargs['end_date'] = booking.end_date.strftime("%Y %M %d %H:%m")
    kwargs['proof'] = booking.proof
    kwargs['mail_type'] = type + 2
    mails.main(to_mail=email, *args, **kwargs)

    if type == 3:
        return 0
    else:
        pass
        sendsms.sendsms(mobile, '', type)
    return 0


# Checking function
def checkRoomAvialability(start_date, end_date, rooms):
    rv_rooms = rooms[:]
    blocked_rooms = []
    block = models.BlockedRooms.objects.all()
    for i in block:
        blocked_rooms.append(i.room_no.room_no)

    # Exclude the blocked rooms from the list
    for i in blocked_rooms:
        try:
            rv_rooms.remove(i)
        except ValueError:
            pass

    # Exclude the booked rooms from the list
    bookings = models.Bookings.objects.filter(rooms__room_no__in=rooms).distinct()
    if bookings.exists():
        for i in bookings:

            if not i.rooms.all().exists():
                continue

            if (i.start_date < start_date and i.end_date < start_date) or \
                    (i.start_date > end_date and i.end_date > end_date):
                pass
            else:
                for j in i.rooms.all():
                    try:
                        rv_rooms.remove(j.room_no)
                    except ValueError:
                        pass
    return rv_rooms


class RoomBlockView(APIView):

    def post(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rooms = request.data['rooms']
            rooms = models.Room.objects.filter(room_no__in=rooms)
            for i in rooms:
                blocked = models.BlockedRooms.objects.filter(room_no=i)
                if blocked.exists():
                    # Unblock the Room
                    blocked.delete()
                else:
                    # Block the Rooms
                    models.BlockedRooms.objects.create(room_no=i, blocked_by=request.user, blocked_on=timezone.now())
        except KeyError:
            return Response({'message': 'Enter all the details', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Successfully performed', 'error': 0})

# Block Views


class BlockListCreateView(ListCreateAPIView):
    serializer_class = serializers.BlockSerializer

    def get_queryset(self):
        if self.request.user.groups.all()[0].name == 'Admin':
            return models.Block.objects.all()
        else:
            return models.Block.objects.none()

    def post(self, request, *args, **kwargs):
        if self.request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return super(BlockListCreateView, self).post(request, *args, **kwargs)


class BlockRetrieveUpdateDesroyView(RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.BlockSerializer

    def get_queryset(self):
        if self.request.user.groups.all()[0].name == 'Admin':
            return models.Block.objects.all()
        else:
            return models.Block.objects.none()

    def delete(self, request, *args, **kwargs):
        super(BlockRetrieveUpdateDesroyView, self).delete(request, *args, **kwargs)
        return Response({'message': 'Successfully deleted', 'error': 0}, status=status.HTTP_200_OK)

# End of Block Views.


# Room Views

class RoomListView(ListAPIView):
    serializer_class = serializers.RoomListSerializer

    def get_queryset(self):
        data = self.request.GET.get('search', None)
        if data is None:
            return models.Room.objects.all()
        else:
            return models.Room.objects.filter(room_no__contains=data)

    def get(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

        context = super(RoomListView, self).get(request, *args, **kwargs)
        now = timezone.now()
        avialable = checkRoomAvialability(now, now + datetime.timedelta(days=1),
                                          list(self.get_queryset().values_list('room_no', flat=True)))

        for i in context.data['results']:
            if i['room_no'] in avialable:
                i['avialable'] = True
            else:
                i['avialable'] = False

        return context


class RoomCreateView(CreateAPIView):
    serializer_class = serializers.RoomSerializer

    def post(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        super(RoomCreateView, self).post(request, *args, **kwargs)
        return Response({'message': 'Successfully created room', 'error': 0}, status=status.HTTP_200_OK)


class RoomRetrieveUpdateDeleteView(RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.RoomSerializer
    queryset = models.Room.objects.all()

    def update(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        return super(RoomRetrieveUpdateDeleteView, self).update(request, *args, **kwargs)


class RoomDeleteView(DestroyAPIView):

    def delete(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        try:
            models.Room.objects.filter(room_no__in=request.data['rooms']).delete()
        except KeyError:
            return Response({'message': 'Please select room to delete', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Successfully Deleted!', 'error': 0}, status=status.HTTP_200_OK)

# End of Room Views


# Bookings views.

@csrf_exempt
@api_view(('POST',))
def RoomBookingView(request):
    try:
        rooms = request.POST.getlist('rooms[]')
        if all(room == '' for room in rooms):
            rooms = []

        if request.data['members'] != '':
            members = int(request.data['members'])
        else:
            members = request.data['members']

        start_date = datetime.datetime.strptime(request.data['start_date'], "%Y/%m/%d %I:%M %p")
        end_date = datetime.datetime.strptime(request.data['end_date'], "%Y/%m/%d %I:%M %p")
        booked_by = request.user
        booking_type = request.data['booking_type']
        proof = request.data['proof']
    except KeyError:
        return Response({'message': 'Fill the form completely', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

    if booking_type == 'Offline' and request.user.groups.all()[0].name != 'Admin':
        return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

    if len(rooms) != 0:
        avialable = checkRoomAvialability(start_date, end_date, rooms)

        if len(list(set(rooms) - set(avialable))) == 0:
            # Through above statement all the elements present in 'rooms' will be in 'avialable'
            reference = ''.join([choice(string.ascii_letters + string.digits) for i in range(22)])
            with transaction.atomic():
                booking = models.Bookings.objects.create(reference=reference, start_date=start_date,
                                                         end_date=end_date, booked_by=booked_by, proof=proof)
                if booking_type == 'Online':
                    booking.booking_type = True
                else:
                    booking.booking_type = False
                    booking.user_booked = request.data['user_booked']

                for i in rooms:
                    room = models.Room.objects.get(room_no=i)
                    booking.rooms.add(room)

                booking.save()
                notifyuser(booking, 1)
            return Response({'message': 'Booked rooms successfully!!!', 'error': 0})
        else:
            return Response({'message': 'room ' + list(set(rooms) - set(avialable))[0] + ' is already booked', 'error': 1},
                            status=status.HTTP_400_BAD_REQUEST)
    else:
        rooms = list(models.Room.objects.all().values_list('room_no', flat=True))
        avialable = checkRoomAvialability(start_date, end_date, rooms)
        avialable_rooms = []
        for i in avialable:
                avialable_rooms.append(get_object_or_404(models.Room, room_no=i))

        avialable_rooms.sort(key=lambda x: x.capacity, reverse=True)

        capacity, rv_rooms, remove_rooms = members, [], []
        for i in avialable_rooms:
            capacity = capacity - i.capacity
            if capacity < 0:
                capacity = capacity + i.capacity
                try:
                    new_avialable = list(set(avialable_rooms) - set(remove_rooms))
                    v = min(new_avialable, key=lambda x: (x.capacity - capacity)
                            if (x.capacity - capacity) >= 0 else sys.maxsize)
                    capacity = capacity - v.capacity
                    rv_rooms.append(v)
                except ValueError:
                    pass
                break
            rv_rooms.append(i)
            remove_rooms.append(i)

        if (len(avialable_rooms) == 0 and capacity > 0) or capacity > 0:
            return Response({'message': 'Rooms not avialable for specified constraints', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

        reference = ''.join([choice(string.ascii_letters + string.digits) for i in range(22)])
        with transaction.atomic():
            booking = models.Bookings.objects.create(reference=reference, start_date=start_date,
                                                     end_date=end_date, booked_by=booked_by, proof=proof)
            if booking_type == 'Online':
                booking.booking_type = True
            else:
                booking.booking_type = False
                booking.user_booked = request.data['user_booked']

            for i in rv_rooms:
                booking.rooms.add(i)

            booking.save()
            notifyuser(booking, 1)
        return Response({'message': 'Booked rooms successfully!!!', 'error': 0})


@csrf_exempt
@api_view(('PATCH',))
def RoomBookingUpdateView(request, pk):
    try:
        start_date = datetime.datetime.strptime(request.data['start_date'], "%Y/%m/%d %I:%M %p")
        end_date = datetime.datetime.strptime(request.data['end_date'], "%Y/%m/%d %I:%M %p")
        proof = request.data['proof']
    except KeyError:
        return Response({'message': 'Fill the form completely', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

    if start_date < timezone.now() or end_date < timezone.now():
        return Response({'message': 'Invalid dates provided', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

    if end_date < start_date:
        return Response({'message': 'End date can not be greater to start date.', 'error': 1},
                        status=status.HTTP_400_BAD_REQUEST)

    booking = get_object_or_404(models.Bookings, pk=pk)

    if booking.start_date == start_date and booking.end_date == end_date and proof != '':
        booking.proof = proof
        booking.save()
        notifyuser(booking, 2)
        return Response({'message': 'Successfully updated booking', 'error': 0})
    elif booking.start_date == start_date and booking.end_date == end_date:
        notifyuser(booking, 2)
        return Response({'message': 'Successfully updated booking', 'error': 0})

    # Check if proof is updated.
    if proof != '' and request.user != booking.booked_by:
        return Response({'message': "Permission denied"})

    # Get the Avialable rooms excluding the current one.
    rooms = list(models.Room.objects.all().values_list('room_no', flat=True))
    error = -1
    try:
        with transaction.atomic():
            # Remove the rooms in the booking.
            capacity = sum(i.capacity for i in booking.rooms.all())
            booking.rooms.set([])
            # get the avialable rooms.
            avialable = checkRoomAvialability(start_date, end_date, rooms)
            avialable_rooms = []

            for i in avialable:
                    avialable_rooms.append(get_object_or_404(models.Room, room_no=i))

            avialable_rooms.sort(key=lambda x: x.capacity, reverse=True)

            rv_rooms, remove_rooms = [], []
            for i in avialable_rooms:
                capacity = capacity - i.capacity
                if capacity < 0:
                    capacity = capacity + i.capacity
                    try:
                        new_avialable = list(set(avialable_rooms) - set(remove_rooms))
                        v = min(new_avialable, key=lambda x: (x.capacity - capacity)
                        if (x.capacity - capacity) >= 0 else sys.maxsize)
                        capacity = capacity - v.capacity
                        rv_rooms.append(v)
                    except ValueError:
                        pass
                    break
                rv_rooms.append(i)
                remove_rooms.append(i)

            if (len(avialable_rooms) == 0 and capacity > 0) or capacity > 0:
                error = 1
                raise InterruptedError

            booking.start_date = start_date
            booking.end_date = end_date
            if proof != '':
                booking.proof = proof

            booking.rooms.set(rv_rooms)
            booking.save()
    except InterruptedError:
        if error is 1:
            return Response({'message': 'Rooms not avialable for specified constraints', 'error': 1},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            pass
    notifyuser(booking, 2)
    return Response({'message': 'Booked rooms successfully!!!', 'error': 0})


class RoomStatusUpdateAPIView(APIView):

    def post(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

        booking = get_object_or_404(models.Bookings, pk=self.kwargs['pk'])
        booking.checkedin = True
        booking.save()

        return Response({'message': 'User successfully checked In', 'error': 0})




@csrf_exempt
@api_view(('POST',))
@authentication_classes([])
@permission_classes([])
def searchRooms(request):
    if request.method == "POST":
        try:
            # Converting Bytes like object to String
            data = json.loads(request.body.decode('utf-8'))
            start_datetime = datetime.datetime.strptime(data['start_date'], "%Y/%m/%d %I:%M %p")
            end_datetime = datetime.datetime.strptime(data['end_date'], "%Y/%m/%d %I:%M %p")
            rooms = list(models.Room.objects.all().values_list('room_no', flat=True))
            avialable = checkRoomAvialability(start_datetime, end_datetime, rooms)
            rv = []
            for i in avialable:
                room = get_object_or_404(models.Room, room_no=i)
                rv.append({"room": room.room_no, "capacity": room.capacity, "block": room.block.name})

            return Response({"rooms": rv})
        except KeyError:
            return Response({'message': 'fill form completely'}, status=status.HTTP_400_BAD_REQUEST)


class UserBookingsView(ListAPIView):
    serializer_class = serializers.UserBookingSerializer

    def get_queryset(self):
        user_type = self.request.user.groups.all()[0].name
        data = self.request.GET.get('search', None)
        if user_type == 'Admin':
            queryset = models.Bookings.objects.all().order_by('start_date')
        else:
            queryset = models.Bookings.objects.filter(booked_by=self.request.user).order_by('start_date')

        if data is None:
            return queryset
        else:
            return queryset.filter(reference__contains=data)


class UserBookingDeleteView(DestroyAPIView):

    def get_object(self):
        print("came here")
        return get_object_or_404(models.Bookings, pk=self.kwargs['pk'])

    def delete(self, request, *args, **kwargs):
        print(request.user.groups.all()[0].name)
        if request.user.groups.all()[0].name != 'Admin':
            if request.user != self.get_object().booked_by:
                return Response({'message': 'Permission Denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

        if self.get_object().start_date > timezone.now():
            self.get_object().delete()
            return Response({'message': 'Successfully canceled the booking', 'error': 0})
        else:
            return Response({'message': 'You can not cancel the booking after the from date', 'error': 1},
                            status=status.HTTP_200_OK)
