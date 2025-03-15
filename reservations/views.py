import datetime
import logging
from uuid import UUID

from django.core.cache import cache

from rest_framework import generics, permissions, viewsets, status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from customers.models import Customer
from customers.permissions import IsOwnerOrAdmin
from reservations.models import RESERVATION_NUM_OF_PARTICIPANTS_LIMIT, Reservation, ReservationStatus
from reservations.serializers import ReservationSerializer, ReservationSlotSerializer, is_date_within_three_to_fifteen_days_from_today
from reservations.utils import get_available_slots, is_slot_in_reservation

logger = logging.getLogger(__name__)


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
    """
    예약 CRUD view
    """
    queryset = Reservation.objects.all().order_by('-date', 'start_time')
    serializer_class = ReservationSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        if self.request.user.is_admin:
            return self.queryset
        return self.queryset.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    @staticmethod
    def validate_modification(reservation: Reservation, customer: Customer):
        """
        예약 수정/삭제 유효성 검사
        """
        if reservation.status == ReservationStatus.CONFIRMED and not customer.is_admin:
            raise ValidationError('확정된 예약은 수정/삭제할 수 없습니다.')

    def update(self, request, *args, **kwargs):
        reservation = self.get_object()
        try:
            self.validate_modification(
                reservation=reservation, customer=request.user
            )
        except ValidationError as err:
            return Response({'error': err.get_full_details()}, status=403)

        if reservation.status == ReservationStatus.CONFIRMED:
            logger.debug(
                f"clearing cache for date {reservation.date}, {request.data.get('date')}")
            cache.delete(f"available_slots:{reservation.date}")
            cache.delete(f"available_slots:{request.data.get('date')}")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        reservation = self.get_object()
        try:
            self.validate_modification(
                reservation=reservation, customer=request.user
            )
        except ValidationError as err:
            return Response({'error': err.get_full_details()}, status=403)

        if reservation.status == ReservationStatus.CONFIRMED:
            logger.debug(
                f"clearing cache for date {reservation.date}, {request.data.get('date')}")
            cache.delete(f"available_slots:{reservation.date}")
            cache.delete(f"available_slots:{request.data.get('date')}")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        try:
            self.validate_modification(
                reservation=reservation, customer=request.user
            )
        except ValidationError as err:
            return Response({'error': err.get_full_details()}, status=403)

        if reservation.status == ReservationStatus.CONFIRMED:
            logger.debug(f"clearing cache for date {reservation.date}")
            cache.delete(f"available_slots:{reservation.date}")
        return super().destroy(request, *args, **kwargs)


@extend_schema_view(
    post=extend_schema(
        summary="예약 확정",
        description="예약을 확정합니다. 어드민만 사용할 수 있습니다.",
        responses={200: ReservationSerializer})
)
class ReservationConfirmView(generics.GenericAPIView):
    """
    예약 확정 view
    """
    queryset = Reservation.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = ReservationSerializer

    def post(self, request: Request, pk: UUID) -> Response:
        reservation = self.get_object()
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save(update_fields=['status'])

        logger.debug(f"clearing cache for date {reservation.date}")
        cache.delete(f"available_slots:{reservation.date}")
        return Response(self.get_serializer(reservation).data, status=status.HTTP_200_OK)


@extend_schema_view(
    get=extend_schema(
        summary="예약 가능 시간 조회",
        description="특정 날짜의 예약 가능한 시간 및 인원을 조회합니다. </br> \
            날짜는 오늘을 기준으로 3일 후부터 15일 후까지 가능합니다.",
        parameters=[
            OpenApiParameter(name='date', type=str, location=OpenApiParameter.QUERY,
                             description='날짜 (예: ?date=YYYY-MM-DD)')
        ],
        responses={200: ReservationSlotSerializer(many=True)}
    )
)
class ReservationAvailableSlotsView(generics.GenericAPIView):
    """
    예약 가능 시간 조회 view
    """
    queryset = Reservation.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    @staticmethod
    def validate_date_param(date_str: str) -> datetime.date:
        """
        날짜 유효성 검사
        """
        if not date_str:
            raise ValidationError('날짜를 제공해야 합니다. (예: ?date=YYYY-MM-DD)')

        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError('날짜 형식은 YYYY-MM-DD 여야 합니다.')

        if not is_date_within_three_to_fifteen_days_from_today(date):
            raise ValidationError('날짜는 오늘부터 3일 후부터 15일 이내여야 합니다.')

        return date

    def get(self, request: Request) -> Response:
        """예약 가능 시간 조회

        캐시된 예약 가능 시간을 반환하거나, 새로 계산하여 반환합니다.
        캐시는 확정된 예약이 생성/수정/삭제될 때마다 갱신됩니다.

        See Also:
            - reservations.utils.get_available_slots
            - reservations.utils.is_slot_in_reservation
            - reservations.models.Reservation.clear_reservation_cache_on_save
        """
        try:
            date = self.validate_date_param(request.query_params.get('date'))
        except ValidationError as err:
            return Response({'error': err.get_full_details()}, status=400)

        cache_key = f"available_slots:{date}"
        cached_slots = cache.get(cache_key)

        if cached_slots:
            logger.debug(f"retuning cached slots for date {date}")
            return Response(cached_slots, status=200)

        slots = get_available_slots()
        reservations = Reservation.objects.filter(
            date=date, status=ReservationStatus.CONFIRMED)

        for reservation in reservations:
            for slot in slots:
                if is_slot_in_reservation(slot, reservation):
                    slot['remaining'] = max(
                        0, slot['remaining'] - reservation.num_of_participants)

        cache.set(cache_key, ReservationSlotSerializer(
            slots, many=True).data, timeout=60*60)

        return Response(ReservationSlotSerializer(slots, many=True).data, status=200)
