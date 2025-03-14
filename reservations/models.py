import uuid

from django.db import models


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
