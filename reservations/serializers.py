import datetime
from rest_framework import serializers

from reservations.models import RESERVATION_NUM_OF_PARTICIPANTS_LIMIT, Reservation


def is_date_within_three_to_fifteen_days_from_today(date: datetime.time) -> bool:
    return (
        date >= (datetime.datetime.now() + datetime.timedelta(days=3)).date() and
        date <= (datetime.datetime.now() + datetime.timedelta(days=15)).date()
    )


class ReservationSerializer(serializers.ModelSerializer):
    customer = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display', read_only=True)

    class Meta:
        model = Reservation
        fields = [
            'id',
            'title',
            'date',
            'start_time',
            'end_time',
            'num_of_participants',
            'status',
            'status_display',
            'created_at',
            'customer',
        ]
        read_only_fields = ['id', 'created_at', 'status']

    def validate(self, attrs):
        if is_date_within_three_to_fifteen_days_from_today(attrs['date']) is False:
            raise serializers.ValidationError(
                '예약은 오늘을 기준으로 3일 후부터 15일 후까지 가능합니다.')

        if (
            attrs['start_time'] >= attrs['end_time'] or
            attrs['start_time'].hour < 9 or
            attrs['end_time'].hour > 18
        ):
            raise serializers.ValidationError('올바른 시간을 입력해주세요.')

        if (
            Reservation.confirmed_num_of_participants_in_time_range(
                attrs['date'], attrs['start_time'], attrs['end_time'], exclude_reservation=self.instance) +
            attrs['num_of_participants'] > RESERVATION_NUM_OF_PARTICIPANTS_LIMIT
        ):
            raise serializers.ValidationError('예약 가능한 인원 수를 초과했습니다.')
        return attrs


class ReservationSlotSerializer(serializers.Serializer):
    """
    슬롯 정보를 직렬화하는 Serializer
    """
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    remaining = serializers.IntegerField()
