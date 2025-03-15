import datetime
from typing import TypedDict
from uuid import UUID
from django.db import models

from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from reservations.models import RESERVATION_NUM_OF_PARTICIPANTS_LIMIT, Reservation, ReservationStatus
from reservations.serializers import ReservationSerializer, is_date_within_three_to_fifteen_days


class Slot(TypedDict):
    start_time: datetime.time
    end_time: datetime.time
    remaning: int


def get_available_slots() -> list[Slot]:
    available_slots = []
    for i in range(9, 18):
        available_slots.append({
            'start_time': datetime.time(i, 0),
            'end_time': datetime.time(i+1, 0),
            'remaining': RESERVATION_NUM_OF_PARTICIPANTS_LIMIT
        })
    return available_slots


def is_slot_in_reservation(slot: Slot, reservation: Reservation) -> bool:
    """슬롯이 예약에 포함되는지 확인합니다.

    Args:
        slot (Slot): 한 시간 단위 슬롯 {'start_time': '09:00', 'end_time': '10:00', 'remaining': 1000}
        reservation (Reservation): 고객의 예약

    Returns:
        bool: 슬롯이 예약에 포함되면 True, 아니면 False
    """
    return reservation.start_time <= slot['start_time'] < reservation.end_time or \
        reservation.start_time < slot['end_time'] <= reservation.end_time


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.customer == request.user or request.user.is_admin


class ReservationView(viewsets.ModelViewSet):
    queryset = Reservation.objects.all().order_by('-date', 'start_time')
    serializer_class = ReservationSerializer

    def get_queryset(self):
        """
        관리자는 모든 예약을 볼 수 있고, 고객은 자신의 예약만 볼 수 있습니다.
        """
        if self.request.user.is_admin:
            return self.queryset
        return self.queryset.filter(customer=self.request.user)

    def get_permissions(self):
        if self.action in ['confirm', 'destory']:
            return [permissions.IsAdminUser()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    def update(self, request, *args, **kwargs):
        reservation = self.get_object()
        if reservation.status == ReservationStatus.CONFIRMED and not request.user.is_admin:
            return Response(
                {'error': '어드민에 의해 확정된 예약은 수정할 수 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        reservation = self.get_object()
        if reservation.status == ReservationStatus.CONFIRMED and not request.user.is_admin:
            return Response(
                {'error': '어드민에 의해 확정된 예약은 수정할 수 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        if reservation.status == ReservationStatus.CONFIRMED and not request.user.is_admin:
            return Response(
                {'error': '어드민에 의해 확정된 예약은 취소할 수 없습니다.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.IsAdminUser]
    )
    def confirm(self, request: Request, pk: UUID) -> Response:
        reservation = self.get_object()
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save(update_fields=['status'])

        serializer = self.get_serializer(reservation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def available_slots(self, request: Request) -> Response:
        date = request.query_params.get('date')
        if not date:
            return Response({'error': '날짜를 제공해야 합니다. (예: ?date=YYYY-MM-DD)'}, status=400)

        try:
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': '날짜 형식은 YYYY-MM-DD 여야 합니다.'}, status=400)

        if not is_date_within_three_to_fifteen_days(date):
            return Response({'error': '날짜는 오늘부터 3일 후부터 15일 이내여야 합니다.'}, status=400)

        reservations = Reservation.objects \
            .filter(date=date, status=ReservationStatus.CONFIRMED) \
            .annotate(total_num_of_participants=models.Sum('num_of_participants'))

        slots = get_available_slots()

        for reservation in reservations:
            for slot in slots:
                if is_slot_in_reservation(slot, reservation):
                    slot['remaining'] -= reservation.num_of_participants
                    slot['remaining'] = max(0, slot['remaining'])

        return Response(slots, status=200)
