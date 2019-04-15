from django.conf.urls import url
from . import views

urlpatterns = [
    # Block Views
    url('^block/$', views.BlockListCreateView.as_view()),
    url('^block/(?P<pk>\d+)/', views.BlockRetrieveUpdateDesroyView.as_view()),

    # Room Views
    url('^rooms/$', views.RoomListView.as_view()),
    url('^create/$', views.RoomCreateView.as_view()),
    url('^(?P<pk>\d+)/$', views.RoomRetrieveUpdateDeleteView.as_view()),

    url('^search/', views.searchRooms),

    # Booking Views
    url('^book/$', views.RoomBookingView),

    # User Room Bookings
    url('^bookings/$', views.UserBookingsView.as_view()),

    url('^booking/delete/(?P<pk>\d+)/$', views.UserBookingDeleteView.as_view()),

    url('^delete/$', views.RoomDeleteView.as_view()),

    url('^blockroom/$', views.RoomBlockView.as_view()),

    url('^update/status/(?P<pk>\d+)/$', views.RoomStatusUpdateAPIView.as_view()),

    url('^booking/delete/(?P<pk>\d+)/$', views.RoomBookingDeleteView.as_view()),

    url('^booking/update/(?P<pk>\d+)/$', views.RoomBookingUpdateView)

]

