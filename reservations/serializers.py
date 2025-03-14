from rest_framework import serializers

from reservations.models import Reservation


class ReservationSerializer(serializers.ModelSerializer):
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
        ]
        read_only_fields = ['id', 'created_at', 'status']
