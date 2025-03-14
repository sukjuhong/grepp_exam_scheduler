from django.db import models
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from reservations.models import Reservation
from reservations.serializers import ReservationSerializer


class ReservationView(viewsets.ReadOnlyModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[permissions.IsAuthenticated],
    )
    def available_slots(self, request: Request) -> Response:
        date = request.query_params.get('date')
        if not date:
            return Response({'error': 'date query parameter is required'}, status=400)

        reservations = Reservation.objects \
            .filter(date=date) \
            .values('start_time', 'end_time') \
            .annotate(total_num_of_participants=models.Sum('num_of_participants'))
        available_slots = [
            {'start_time': '09:00', 'end_time': '10:00', 'remain': 50000},
            {'start_time': '10:00', 'end_time': '11:00', 'remain': 50000},
            {'start_time': '11:00', 'end_time': '12:00', 'remain': 50000},
            {'start_time': '13:00', 'end_time': '14:00', 'remain': 50000},
            {'start_time': '14:00', 'end_time': '15:00', 'remain': 50000},
            {'start_time': '15:00', 'end_time': '16:00', 'remain': 50000},
            {'start_time': '16:00', 'end_time': '17:00', 'remain': 50000},
            {'start_time': '17:00', 'end_time': '18:00', 'remain': 50000},
        ]

        def is_reservation_in_slot(slot, reservation):
            return (
                slot['start_time'] <= reservation['start_time'] and
                slot['end_time'] >= reservation['end_time']
            )

        for reservation in reservations:
            for slot in available_slots:
                if is_reservation_in_slot(slot, reservation):
                    slot['remain'] -= reservation['total_num_of_participants']

        for reservation in reservations:
            available_slots = [
                slot for slot in available_slots if slot['remain'] >= 0]

        return Response(available_slots)
