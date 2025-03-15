import uuid
from django.db import models
from django.core.exceptions import ValidationError
from datetime import time

RESERVATION_NUM_OF_PARTICIPANTS_LIMIT = 50000


class ReservationStatus(models.TextChoices):
    PENDING = 'PENDING', '확정 대기중'
    CONFIRMED = 'APPROVED', '확정됨'
    CANCELLED = 'REJECTED', '취소됨'


class Reservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    customer = models.ForeignKey(
        'customers.Customer', on_delete=models.CASCADE)
    num_of_participants = models.IntegerField()
    status = models.CharField(
        max_length=10,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # start_time이 end_time보다 이전이어야 한다.
            models.CheckConstraint(
                check=models.Q(start_time__lt=models.F('end_time')),
                name='start_time_before_end_time'
            ),
            # 1시간 단위로 예약할 수 있다.
            models.CheckConstraint(
                check=models.Q(start_time__minute=0, end_time__minute=0),
                name='times_on_the_hour'
            ),
        ]

    def clean(self):
        super().clean()
        if self.start_time >= self.end_time:
            raise ValidationError('Start time must be before end time.')
        if self.start_time.minute != 0 or self.end_time.minute != 0:
            raise ValidationError(
                'Start time and end time must be on the hour.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def confirmed_num_of_participants_in_time_range(date, start_time, end_time):
        return Reservation.objects.filter(
            date=date,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status=ReservationStatus.CONFIRMED
        ).aggregate(models.Sum('num_of_participants'))['num_of_participants__sum'] or 0
