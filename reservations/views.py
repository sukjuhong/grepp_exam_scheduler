import datetime
from typing import List, TypedDict
from uuid import UUID
from django.db import models

from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from reservations.models import RESERVATION_NUM_OF_PARTICIPANTS_LIMIT, Reservation, ReservationStatus
from reservations.serializers import ReservationSerializer, is_date_within_three_to_fifteen_days_from_today


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


@extend_schema_view(
    list=extend_schema(
        summary="예약 목록 조회",
        description="페이지네이션 처리된 예약 목록을 조회합니다. </br> \
            어드민은 모든 예약을 볼 수 있고, 고객은 자신의 예약만 볼 수 있습니다."),
    retrieve=extend_schema(
        summary="단일 예약 조회",
        description="예약 ID로 예약 정보를 조회합니다. </br> \
            어드민은 모든 예약을 볼 수 있고, 고객은 자신의 예약만 볼 수 있습니다."),
    create=extend_schema(
        summary="예약 생성",
        description=f"새로운 예약을 생성합니다. </br> \
            예약은 오늘을 기준으로 3일 후부터 15일 후까지 가능합니다. </br> \
            예약은 1시간 단위이며, 그렙의 대응 가능 시간인 9시부터 18시까지 예약이 가능합니다. </br> \
            동 시간에 {RESERVATION_NUM_OF_PARTICIPANTS_LIMIT}명이 수용 가능하므로, \
                예약 가능한 인원 수를 초과하면 예약할 수 없습니다."),
    update=extend_schema(
        summary="예약 수정",
        description="예약 정보를 수정합니다. </br> \
            어드민은 모든 예약을 수정할 수 있고, 고객은 자신의 예약만 수정할 수 있습니다. </br> \
            고객은 확정된 예약을 수정할 수 없습니다."),
    partial_update=extend_schema(
        summary="예약 일부 수정",
        description="예약 정보를 일부 수정합니다. </br> \
            어드민은 모든 예약을 수정할 수 있고, 고객은 자신의 예약만 수정할 수 있습니다. </br> \
            고객은 확정된 예약을 수정할 수 없습니다."),
    destroy=extend_schema(
        summary="예약 삭제",
        description="예약 정보를 삭제합니다. </br> \
            어드민은 모든 예약을 삭제할 수 있고, 고객은 자신의 예약만 삭제할 수 있습니다. </br> \
            고객은 확정된 예약을 삭제할 수 없습니다."),
)
class ReservationView(viewsets.ModelViewSet):
    queryset = Reservation.objects.all().order_by('-date', 'start_time')
    serializer_class = ReservationSerializer

    def get_queryset(self):
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

    @extend_schema(
        summary="예약 확정",
        description="예약을 확정합니다. 어드민만 사용할 수 있습니다.",
        responses={200: ReservationSerializer}
    )
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

    @extend_schema(
        summary="예약 가능 시간 조회",
        description="특정 날짜의 예약 가능한 시간 및 인원을 조회합니다. </br> \
            날짜는 오늘을 기준으로 3일 후부터 15일 후까지 가능합니다.",
        parameters=[
            OpenApiParameter(
                name='date',
                type=str,
                description='날짜 (형식: 2025-03-15)',
                required=True)],
        responses={200: List[Slot]}
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def available_slots(self, request: Request) -> Response:
        date = request.query_params.get('date')
        if not date:
            return Response({'error': '날짜를 제공해야 합니다. (예: ?date=YYYY-MM-DD)'}, status=400)

        try:
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': '날짜 형식은 YYYY-MM-DD 여야 합니다.'}, status=400)

        if not is_date_within_three_to_fifteen_days_from_today(date):
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
