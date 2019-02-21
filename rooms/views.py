from rest_framework import status
from rest_framework.response import Response

from . import serializers, models
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView


class RoomBookingListCreateView(ListCreateAPIView):
    serializers = serializers.BookingSerializer

    def get_queryset(self):
        if self.request.user.groups.all()[0].name == 'Admin':
            return models.BookedUsers.objects.order_by('booked_date')
        else:
            return models.BookedUsers.objects.filter(Q(user=self.request.user)).order_by('booked_date')

    def post(self, request, *args, **kwargs):
        s = self.get_serializer(data=request.data)
        if request.user.groups.all()[0].name == 'Admin' and s.validated_data['usernmae'] != '':
            return Response({'message': 'Error in'})


# class RoomBookingView(RetrieveUpdateDestroyAPIView):
#     serializers = serializers.BookingSerializer
#
#     def get_queryset(self):

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

# End of Block Views.
