from django.conf.urls import url
from . import views

urlpatterns = [
    # Block Views
    url('^block/$', views.BlockListCreateView.as_view()),
    url('^block/(?P<pk>\d+)/', views.BlockListCreateView.as_view()),

    # Room Views
    url('^rooms/$', views.RoomListView.as_view()),
    url('^create/$', views.RoomCreateView.as_view()),
    url('^(?P<pk>\d+)/$', views.RoomRetrieveUpdateDeleteView.as_view()),

    # Booking Views
    url('^book/$', views.RoomBookingListCreateView.as_view()),

    # Room Status Update Views
    url('^update/booking/$', views.RoomReportView.as_view())

]

