from django.urls import include, path

from reservations.views import ReservationView


urlpatterns = [
    path('', ReservationView.as_view({'get': 'list'})),
    path('<int:pk>/',
         ReservationView.as_view({'get': 'retrieve'})),
    path('available-slots/',
         ReservationView.as_view({'get': 'available_slots'})),
]
