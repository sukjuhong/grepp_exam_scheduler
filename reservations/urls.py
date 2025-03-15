from django.urls import path

from reservations.views import ReservationView


urlpatterns = [
    path('', ReservationView.as_view(
        {'get': 'list', 'post': 'create'}), name='reservations'),
    path('<uuid:pk>/',
         ReservationView.as_view(
             {'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='reservation-detail'),
    path('<uuid:pk>/confirm/',
         ReservationView.as_view({'post': 'confirm'}), name='reservation-confirm'),
    path('available-slots/',
         ReservationView.as_view({'get': 'available_slots'}), name='reservation-available-slots'),
]
