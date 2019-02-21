from django.conf.urls import url
from . import views

urlpatterns = [
    # Block Views
    url('^block/', views.BlockListCreateView.as_view()),
    url('^block/(?P<pk>\d+)/', views.BlockListCreateView.as_view()),

]

