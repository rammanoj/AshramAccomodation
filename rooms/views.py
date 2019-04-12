import json
import string
import sys
from random import choice
from django.db import transaction
from django.db.models import Q
import datetime

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import renderer_classes, api_view, authentication_classes, permission_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from . import serializers, models
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView, CreateAPIView, \
    DestroyAPIView


# Checking function
def checkRoomAvialability(start_date, end_date, rooms):
    include = [True] * len(rooms)
    blocked_rooms = list(models.BlockedRooms.objects.all().values_list('room_no'))

    # Exclude the blocked rooms from the list
    for i in blocked_rooms:
        if i in rooms:
            include[rooms.index(i)] = False

    # Exclude the booked rooms from the list
    booked_rooms = models.Bookings.objects.filter(rooms__room_no__in=rooms)
    if booked_rooms.exists():
        for i in booked_rooms:
            if i.rooms is None:
                continue
            bookedroom = list(i.rooms.values_list('room_no', flat=True))
            rooms_booked = list(set(rooms).intersection(bookedroom))
            if len(rooms_booked) != 0:
                for j in rooms_booked:
                    if (i.start_date < start_date and i.end_date < start_date) or (i.start_date > end_date
                                                                                   and i.end_date > end_date):
                        pass
                    else:
                        include[rooms.index(j)] = False
    return include


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
    queryset = models.Room.objects.all()

    def get(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        context = super(RoomListView, self).get(request, *args, **kwargs)
        for i in context.data['results']:
            i['blocked'] = models.BlockedRooms.objects.filter(room_no=i['room_no']).exists()
        return context

    def post(self, request, *args, **kwargs):
        rooms = models.Room.objects.all()
        try:
            start_date = timezone.make_aware(datetime.datetime.strptime(request.data['start_date'], '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.datetime.strptime(request.data['end_date'], '%Y-%m-%d'))
            if start_date + datetime.timedelta(days=1) <= timezone.now() or end_date < timezone.now():
                return Response({'message': 'Enter valid dates!!', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

            booked_rooms = models.Room.objects.filter(Q(booking__status=0) | Q(booking__status=1)).exclude(Q
                                            (Q(booking__check_in__gt=start_date), Q(booking__check_in__gt=end_date))
                                            | Q(Q(booking__check_out__lt=end_date), Q(booking__check_out__lt=start_date)))

            rooms = rooms.difference(booked_rooms)
        except KeyError:
            return Response({'message': 'Fill the form completely!!', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        self.queryset = rooms
        return super(RoomListView, self).get(request, *args, **kwargs)


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

    def delete(self, request, *args, **kwargs):
        if request.user.groups.all()[0].name != 'Admin':
            return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
        super(RoomRetrieveUpdateDeleteView, self).delete(request, *args, **kwargs)
        return Response({'message': 'Successfully Deleted!', 'error': 1}, status=status.HTTP_200_OK)

# End of Room Views


# Bookings views.

@csrf_exempt
@api_view(('POST',))
def RoomBookingView(request):
    try:
        rooms = request.data['rooms']
        members = request.data['members']
        start_date = datetime.datetime.strptime(request.data['start_date'], "%Y/%m/%d %I:%M %p")
        end_date = datetime.datetime.strptime(request.data['end_date'], "%Y/%m/%d %I:%M %p")
        booked_by = request.user
        booking_type = request.data['booking_type']
    except KeyError:
        return Response({'message': 'Fill the form completely', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

    if booking_type == 'Offline' and request.user.groups.all()[0].name != 'Admin':
        return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

    if len(rooms) != 0:
        avialable = checkRoomAvialability(start_date, end_date, rooms)

        if all(i is True for i in avialable):
            reference = ''.join([choice(string.ascii_letters + string.digits) for i in range(22)])
            with transaction.atomic():
                booking = models.Bookings.objects.create(reference=reference, start_date=start_date,
                                                         end_date=end_date, booked_by=booked_by)
                if booking_type == 'Online':
                    booking.booking_type = True
                else:
                    booking.booking_type = False
                    booking.user_booked = request.data['user_booked']

                for i in rooms:
                    room = models.Room.objects.get(room_no=i)
                    booking.rooms.add(room)

                booking.save()
            return Response({'message': 'Booked rooms successfully!!!', 'error': 0})
        else:
            return Response({'message': 'room ' + rooms[avialable.index(False)] + ' is already booked', 'error': 1},
                            status=status.HTTP_400_BAD_REQUEST)
    else:
        rooms = list(models.Room.objects.all().values_list('room_no', flat=True))
        avialable = checkRoomAvialability(start_date, end_date, rooms)
        avialable_rooms = []
        for i in range(0, len(rooms)):
            if avialable[i] is True:
                avialable_rooms.append(models.Room.objects.get(room_no=rooms[i]))

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
                                                     end_date=end_date, booked_by=booked_by)
            if booking_type == 'Online':
                booking.booking_type = True
            else:
                booking.booking_type = False
                booking.user_booked = request.data['user_booked']

            for i in rv_rooms:
                booking.rooms.add(i)

            booking.save()
        return Response({'message': 'Booked rooms successfully!!!', 'error': 0})


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
            for i in range(0, len(rooms)):
                if avialable[i] is True:
                    room = models.Room.objects.get(room_no=rooms[i])
                    rv.append({"room": room.room_no, "capacity": room.capacity, "block": room.block.name})

            return Response({"rooms": rv})
        except KeyError:
            return Response({'message': 'fill form completely'}, status=status.HTTP_400_BAD_REQUEST)


class UserBookingsView(ListAPIView):
    serializer_class = serializers.UserBookingSerializer

    def get_queryset(self):
        user_type = self.request.user.groups.all()[0].name
        if user_type == 'Admin':
            return models.Bookings.objects.all().order_by('start_date')
        else:
            return models.Bookings.objects.filter(booked_by=self.request.user).order_by('start_date')


class UserBookingDeleteView(DestroyAPIView):

    def delete(self, request, *args, **kwargs):
        if request.user != "Admin":
            booking = models.Bookings.objects.filter(pk=self.kwargs['pk'])
            if booking.exists():
                if booking[0].booked_by != request.user:
                    return Response({'message': 'Permission Denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)

        models.Bookings.objects.filter(pk=self.kwargs['pk']).delete()
        return Response({'message': 'successfully deleted', 'error': 0})


# class RoomBookingListCreateView(ListCreateAPIView):
#     serializer_class = serializers.RoomBookingSerializer
#
#     def get_queryset(self):
#         if self.request.user.groups.all()[0].name == 'Admin':
#             return models.BookedUsers.objects.order_by('booked_date')
#         else:
#             return models.BookedUsers.objects.filter(Q(user=self.request.user)).order_by('booked_date')
#
#     def post(self, request, *args, **kwargs):
#         # Check if the Admin entered the username while making a offline booking.
#         if request.user.groups.all()[0].name == 'Admin':
#             try:
#                 username = request.data['username']
#             except KeyError:
#                 return Response({'message': 'Enter the username of the offline booking user.'})
#
#         # Validate the serialised data, raise Exception if any
#         s = self.get_serializer(data=request.data)
#         s.is_valid(raise_exception=True)
#         s.save()
#         return Response({'message': 'Successfully created Room', 'error': 1})
#
#
# class RoomBookingRetrieveUpdateDeleteView(RetrieveUpdateDestroyAPIView):
#     serializer_class = serializers.BookedUsers
#
#     def get_object(self):
#         obj = get_object_or_404(models.BookedUsers, pk=self.kwargs['pk'])
#         if obj.user.groups.all()[0].name == 'Admin':
#             return obj
#         elif obj.user == self.request.user:
#             return obj
#         else:
#             return get_object_or_404(models.BookedUsers, pk=-1)
#
#     def update(self, request, *args, **kwargs):
#         pass
#
#     def delete(self, request, *args, **kwargs):
#         obj = self.get_object()
#         room_no = [models.Room.objects.get(i) for i in request.data['room_no']]
#         room_booking = models.Booking.objects.filter(booked_by=obj)
#         for i in room_booking:
#             # Can delete some specifc rooms in the entire room booking.
#             booked_room = i
#             if booked_room.room in room_no:
#                 booked_room['status'] = -1
#                 booked_room.save()
#
#         return Response({'message': 'Cancelled Booking', 'error': 0})
#
# # End of Room Booking views
#
#
# # Report check-in or check-out
#
# class RoomReportView(APIView):
#     http_method_names = ['post']
#
#     def post(self, request, *args, **kwargs):
#         # Frontend Changes:
#         # If 0, enter date >= today => devotee checkedIn
#         # If 1, devotee checked out
#         # If -1, no other option to be displayed.
#         # If 0, enter date <= today => devotee checkedOut already hence no change.
#         try:
#             reference = request.data['reference']
#             room = request.data['room']
#             room_status = request.data['status']
#         except KeyError:
#             return Response({'message': 'Something went wrong, Try again later', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
#
#         booking = models.Booking.objects.filter(Q(reference=reference), Q(room__room_no=room))
#
#         if request.user.groups.all()[0].name != 'Admin' and booking[0].booked_by != request.user:
#             return Response({'message': 'Permission denied', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
#         if booking.exists():
#             room_booking = booking[0]
#             room_booking.status = room_status
#             room_booking.save()
#         else:
#             return Response({'message': 'No such booking is performed!!', 'error': 1}, status=status.HTTP_400_BAD_REQUEST)
#         return Response({'message': 'Successfully done', 'error': 0})
#
# # End of Report check-in or check-out
