import datetime
import re
from typing import cast
from unittest.mock import patch
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import time, timedelta

from customers.models import Customer
from reservations.utils import Slot, is_slot_in_reservation
from .models import RESERVATION_NUM_OF_PARTICIPANTS_LIMIT, Reservation, ReservationStatus


class ReservationAPITestCase(APITestCase):
    def setUp(self):
        self.admin_customer = Customer.objects.create_superuser(
            company_name="grepp",
            password="grepp1234"
        )
        self.normal_customer = Customer.objects.create(
            company_name="programmers",
            password="progremmers123"
        )
        self.normal_customer2 = Customer.objects.create(
            company_name="kakao",
            password="kakao1234"
        )

    def authenticate(self, customer: Customer):
        self.client.force_authenticate(customer)

    def create_reservation(self, customer: Customer, num_of_participants=None):
        if num_of_participants is None:
            num_of_participants = RESERVATION_NUM_OF_PARTICIPANTS_LIMIT // 2

        return Reservation.objects.create(
            title="테스트 시험",
            customer=customer,
            date=now().date() + timedelta(days=5),
            start_time=time(hour=9, minute=0, second=0).strftime('%H:%M:%S'),
            end_time=time(hour=12, minute=0, second=0).strftime('%H:%M:%S'),
            num_of_participants=num_of_participants
        )

    # --- 예약 생성 ---

    def test_create_reservation(self):
        """
        고객이 새로운 시험 예약을 생성할 수 있는지 확인
        """
        self.authenticate(self.normal_customer)

        url = reverse('reservations')
        data = {
            "title": "테스트 시험",
            "date": (now() + timedelta(days=5)).date().isoformat(),
            "start_time": time(hour=9, minute=0, second=0).strftime('%H:%M:%S'),
            "end_time": time(hour=10, minute=0, second=0).strftime('%H:%M:%S'),
            "num_of_participants": RESERVATION_NUM_OF_PARTICIPANTS_LIMIT // 2
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_reservation = Reservation.objects.get(id=response.data["id"])
        self.assertEqual(created_reservation.title, data["title"])
        self.assertEqual(created_reservation.date.isoformat(), data["date"])
        self.assertEqual(created_reservation.start_time.strftime(
            '%H:%M:%S'), data["start_time"])
        self.assertEqual(created_reservation.end_time.strftime(
            '%H:%M:%S'), data["end_time"])
        self.assertEqual(created_reservation.num_of_participants,
                         data["num_of_participants"])

    def test_failed_create_reservation_with_invalid_date(self):
        """
        유효하지 않은 날짜로 예약을 생성하면 실패하는지 확인
        """
        self.authenticate(self.normal_customer)

        url = reverse('reservations')
        data = {
            "title": "테스트 시험",
            "date": (now() + timedelta(days=1)).date().isoformat(),
            "start_time": time(hour=9, minute=0, second=0).strftime('%H:%M:%S'),
            "end_time": time(hour=10, minute=0, second=0).strftime('%H:%M:%S'),
            "num_of_participants": RESERVATION_NUM_OF_PARTICIPANTS_LIMIT // 2
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {
            "title": "테스트 시험",
            "date": (now() + timedelta(days=16)).date().isoformat(),
            "start_time": time(hour=9, minute=0, second=0).strftime('%H:%M:%S'),
            "end_time": time(hour=10, minute=0, second=0).strftime('%H:%M:%S'),
            "num_of_participants": RESERVATION_NUM_OF_PARTICIPANTS_LIMIT // 2
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_failed_create_reservation_with_invalid_time(self):
        """
        유효하지 않은 시간대로 예약을 생성하면 실패하는지 확인
        """
        self.authenticate(self.normal_customer)

        url = reverse('reservations')
        data = {
            "start_time": time(hour=9, minute=0, second=0).strftime('%H:%M:%S'),
            "end_time": time(hour=20, minute=0, second=0).strftime('%H:%M:%S'),
            "num_of_participants": RESERVATION_NUM_OF_PARTICIPANTS_LIMIT // 2
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_failed_create_reservation_with_invalid_num_of_participants(self):
        """
        유효하지 않은 인원으로 예약을 생성하면 실패하는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer)

        url = reverse('reservations')
        data = {
            "date": (now() + timedelta(days=5)).date().isoformat(),
            "start_time": time(hour=9, minute=0, second=0).strftime('%H:%M:%S'),
            "end_time": time(hour=10, minute=0, second=0).strftime('%H:%M:%S'),
            "num_of_participants": RESERVATION_NUM_OF_PARTICIPANTS_LIMIT - reservation.num_of_participants + 1
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- 예약 수정 ---
    def test_update_reservation(self):
        """
        예약을 수정할 수 있는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer)

        url = reverse('reservation-detail', args=[reservation.id])
        data = {
            "title": "변경된 테스트 시험",
            "date": (now() + timedelta(days=8)).date().isoformat(),
            "start_time": time(hour=10, minute=0, second=0).strftime('%H:%M:%S'),
            "end_time": time(hour=12, minute=0, second=0).strftime('%H:%M:%S'),
            "num_of_participants": RESERVATION_NUM_OF_PARTICIPANTS_LIMIT // 2
        }

        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        reservation.refresh_from_db()
        updated_reservation = Reservation.objects.get(id=reservation.id)
        self.assertEqual(updated_reservation.title, data["title"])
        self.assertEqual(updated_reservation.date.isoformat(), data["date"])
        self.assertEqual(updated_reservation.start_time.strftime(
            '%H:%M:%S'), data["start_time"])
        self.assertEqual(updated_reservation.end_time.strftime(
            '%H:%M:%S'), data["end_time"])
        self.assertEqual(updated_reservation.num_of_participants,
                         data["num_of_participants"])

    def test_admin_can_update_any_reservation(self):
        """
        어드민이 모든 예약을 수정할 수 있는지 확인
        """
        self.authenticate(self.admin_customer)
        reservation = self.create_reservation(self.normal_customer)

        url = reverse('reservation-detail', args=[reservation.id])
        data = {
            "title": "변경된 테스트 시험",
            "date": (now() + timedelta(days=8)).date().isoformat(),
            "start_time": time(hour=10, minute=0, second=0).strftime('%H:%M:%S'),
            "end_time": time(hour=12, minute=0, second=0).strftime('%H:%M:%S'),
            "num_of_participants": RESERVATION_NUM_OF_PARTICIPANTS_LIMIT // 2
        }

        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_do_updating_confirmed_reservation_delete_cache(self):
        """
        어드민이 확정 된 예약 수정 시 캐시를 삭제하는지 확인
        """
        self.authenticate(self.admin_customer)
        reservation = self.create_reservation(self.normal_customer)
        old_reservation_date = reservation.date
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save()
        reservation.refresh_from_db()

        with patch('django.core.cache.cache.delete') as mock_delete:
            url = reverse('reservation-detail', args=[reservation.id])
            data = {
                "title": "변경된 테스트 시험",
                "date": (now() + timedelta(days=8)).date().isoformat(),
                "start_time": time(hour=10, minute=0, second=0).strftime('%H:%M:%S'),
                "end_time": time(hour=12, minute=0, second=0).strftime('%H:%M:%S'),
                "num_of_participants": RESERVATION_NUM_OF_PARTICIPANTS_LIMIT // 2
            }

            response = self.client.put(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(mock_delete.call_count, 2)
            mock_delete.assert_any_call(
                f'available_slots:{old_reservation_date.isoformat()}')
            mock_delete.assert_any_call(
                f'available_slots:{reservation.date.isoformat()}')

    def test_user_cannot_update_other_customer_reservation(self):
        """
        다른 고객의 예약을 수정할 수 없는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer2)

        url = reverse('reservation-detail', args=[reservation.id])
        data = {
            "title": "변경된 테스트 시험",
            "date": (now() + timedelta(days=8)).date().isoformat(),
            "start_time": time(hour=10, minute=0, second=0).strftime('%H:%M:%S'),
            "end_time": time(hour=12, minute=0, second=0).strftime('%H:%M:%S'),
            "num_of_participants": RESERVATION_NUM_OF_PARTICIPANTS_LIMIT // 2
        }

        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_confirmed_reservation(self):
        """
        고객이 확정된 예약을 수정할 수 없는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer)
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save()

        url = reverse('reservation-detail', args=[reservation.id])
        data = {
            "title": "변경된 테스트 시험",
            "date": (now() + timedelta(days=8)).date().isoformat(),
            "start_time": time(hour=10, minute=0, second=0).strftime('%H:%M:%S'),
            "end_time": time(hour=12, minute=0, second=0).strftime('%H:%M:%S'),
            "num_of_participants": RESERVATION_NUM_OF_PARTICIPANTS_LIMIT // 2
        }

        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- 예약 확정 ---

    def test_admin_can_confirm_reservation(self):
        """
        어드민이 예약을 확정할 수 있는지 확인
        """
        self.authenticate(self.admin_customer)
        reservation = self.create_reservation(self.normal_customer)

        url = reverse('reservation-confirm', args=[reservation.id])
        response = self.client.post(url)
        reservation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)

    def test_do_cofirming_reservation_delete_cache(self):
        """
        예약 확정 시 캐시를 삭제하는지 확인
        """
        self.authenticate(self.admin_customer)
        reservation = self.create_reservation(self.normal_customer)

        with patch('django.core.cache.cache.delete') as mock_delete:
            url = reverse('reservation-confirm', args=[reservation.id])
            response = self.client.post(url)
            reservation.refresh_from_db()

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)
            mock_delete.assert_any_call(
                f'available_slots:{reservation.date.isoformat()}')

    def test_user_cannot_confirm_reservation(self):
        """
        고객이 예약을 확정할 수 없는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer)

        url = reverse('reservation-confirm', args=[reservation.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- 예약 삭제 ---

    def test_admin_can_delete_any_reservation(self):
        """
        어드민이 모든 예약을 삭제할 수 있는지 확인
        """
        self.authenticate(self.admin_customer)
        reservation = self.create_reservation(self.normal_customer)

        url = reverse('reservation-detail', args=[reservation.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_do_deleting_confirmed_reservation_delete_cache(self):
        """
        어드민이 확정된 예약 삭제 시 캐시를 삭제하는지 확인
        """
        self.authenticate(self.admin_customer)
        reservation = self.create_reservation(self.normal_customer)
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save()
        reservation.refresh_from_db()

        with patch('django.core.cache.cache.delete') as mock_delete:
            url = reverse('reservation-detail', args=[reservation.id])
            response = self.client.delete(url)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
            mock_delete.assert_called_once_with(
                f'available_slots:{reservation.date.isoformat()}')

    def test_user_can_delete_pending_reservation(self):
        """
        고객이 확정 대기중인 예약을 삭제할 수 있는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer)

        url = reverse('reservation-detail', args=[reservation.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_cannot_delete_other_customer_reservation(self):
        """
        다른 고객의 예약을 삭제할 수 없는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer2)

        url = reverse('reservation-detail', args=[reservation.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_delete_confirmed_reservation(self):
        """
        고객이 확정된 예약을 삭제할 수 없는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer)
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save()

        url = reverse('reservation-detail', args=[reservation.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- 예약 조회 ---

    def test_list_reservations(self):
        """
        고객이 자신의 예약 목록을 조회할 수 있는지 확인
        추가로 다른 사람의 예약은 조회할 수 없는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer)
        reservation2 = self.create_reservation(self.normal_customer2)

        url = reverse('reservations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["next"], None)
        self.assertIn(str(reservation.id), [item["id"]
                                            for item in response.data["results"]])
        self.assertNotIn(str(reservation2.id), [item["id"]
                                                for item in response.data["results"]])

    def test_admin_can_list_all_reservations(self):
        """
        어드민이 모든 예약 목록을 조회할 수 있는지 확인
        """
        self.authenticate(self.admin_customer)
        reservation = self.create_reservation(self.normal_customer)
        reservation2 = self.create_reservation(self.normal_customer2)

        url = reverse('reservations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["next"], None)
        self.assertIn(str(reservation.id), [item["id"]
                                            for item in response.data["results"]])
        self.assertIn(str(reservation2.id), [item["id"]
                                             for item in response.data["results"]])

    def test_retrieve_reservation(self):
        """
        고객이 자신의 예약을 조회할 수 있는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer)

        url = reverse('reservation-detail', args=[reservation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(reservation.id))

    def test_cant_retrieve_other_customer_reservation(self):
        """
        다른 고객의 예약을 조회할 수 없는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer2)

        url = reverse('reservation-detail', args=[reservation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_retrieve_any_reservation(self):
        """
        어드민이 모든 예약을 조회할 수 있는지 확인
        """
        self.authenticate(self.admin_customer)
        reservation = self.create_reservation(self.normal_customer)

        url = reverse('reservation-detail', args=[reservation.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(reservation.id))

    # --- 신청 가능한 시간과 인원 조회 ---

    def test_available_slots(self):
        """
        예약 가능한 시간대 목록을 조회할 수 있는지 확인
        추가로, 확정된 예약이 있는 시간대가 남은 인원을 제대로 표시하는지 확인
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer)
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save()

        url = reverse('reservation-available-slots')
        response = self.client.get(
            url + f'?date={reservation.date.isoformat()}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.data, list))
        self.assertIn('start_time', response.data[0])
        self.assertIn('end_time', response.data[0])
        self.assertIn('remaining', response.data[0])

        for slot in response.data:
            slot = Slot(
                start_time=datetime.datetime.strptime(
                    slot['start_time'], '%H:%M:%S').time(),
                end_time=datetime.datetime.strptime(
                    slot['end_time'], '%H:%M:%S').time(),
                remaining=cast(int, slot['remaining'])
            )
            if is_slot_in_reservation(slot, reservation):
                self.assertEqual(
                    slot['remaining'], RESERVATION_NUM_OF_PARTICIPANTS_LIMIT - reservation.num_of_participants)

    def test_caching_available_slots(self):
        """
        예약 가능한 시간대 목록을 캐싱하여 빠르게 조회할 수 있는지 확인
        첫 조회 시 캐싱되고, (mock_get.call_count == 1, mock_set.call_count == 1)
        두 번째 조회 시 캐싱된 데이터를 사용하는지 확인 (mock_get.call_count == 2, mock_set.call_count == 1)
        """
        self.authenticate(self.normal_customer)
        reservation = self.create_reservation(self.normal_customer)
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save()

        with patch('django.core.cache.cache.get') as mock_get, patch('django.core.cache.cache.set') as mock_set:
            mock_get.return_value = None
            url = reverse('reservation-available-slots')
            response = self.client.get(
                url + f'?date={reservation.date.isoformat()}', format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_get.assert_called_once_with(
                f'available_slots:{reservation.date.isoformat()}')
            mock_set.assert_called_once()

            mock_get.return_value = response.data
            response = self.client.get(
                url + f'?date={reservation.date.isoformat()}', format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(mock_get.call_count, 2)
            self.assertEqual(mock_set.call_count, 1)

    def test_failed_available_slots_with_invalid_date(self):
        """
        유효하지 않은 날짜 형식으로 조회하면 실패하는지 확인
        """

        self.authenticate(self.normal_customer)

        url = reverse('reservation-available-slots')
        response = self.client.get(url + '?date=20250430')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_failed_available_slots_with_not_three_days_later(self):
        """
        3일 이후 15일 이내가 아닌 날짜로 조회하면 실패하는지 확인
        """
        self.authenticate(self.normal_customer)

        url = reverse('reservation-available-slots')
        response = self.client.get(
            url + f'?date={(now() + timedelta(days=2)).date().isoformat()}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.get(
            url + f'?date={(now() + timedelta(days=16)).date().isoformat()}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
