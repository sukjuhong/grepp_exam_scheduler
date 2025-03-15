from django.urls import path

from reservations.views import ReservationAvailableSlotsView, ReservationConfirmView, ReservationView


urlpatterns = [
    path('', ReservationView.as_view(
        {'get': 'list', 'post': 'create'}), name='reservations'),
    path('<uuid:pk>/',
         ReservationView.as_view(
             {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='reservation-detail'),
    path('<uuid:pk>/confirm/',
         ReservationConfirmView.as_view(), name='reservation-confirm'),
    path('available-slots/',
         ReservationAvailableSlotsView.as_view(), name='reservation-available-slots'),
]
