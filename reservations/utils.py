
import datetime
from typing import TypedDict

from reservations.models import RESERVATION_NUM_OF_PARTICIPANTS_LIMIT, Reservation


class Slot(TypedDict):
    """
    슬롯 정보를 담는 타입입니다.
    """
    start_time: datetime.time
    end_time: datetime.time
    remaning: int


def get_available_slots() -> list[Slot]:
    """9시부터 18시까지 초기 슬롯을 반환합니다.

    Returns:
        list[Slot]: 초기 슬롯 리스트
    """
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
