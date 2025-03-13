from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from customers.models import Customer


class CustomerAPITestCase(APITestCase):
    def setUp(self):
        self.admin_customer = Customer.objects.create_superuser(
            company_name="grepp",
            password="grepp1234"
        )
        self.normal_customer = Customer.objects.create(
            company_name="programmers",
            password="progremmers123"
        )

    def test_create_account(self):
        """
        회원가입을 성공적으로 진행하는 경우
        """
        url = reverse('customer-list')
        data = {
            "company_name": "sktelecom",
            "password": "sktelecom123",
            "is_active": True,
            "is_admin": False,
        }

        self.client.force_login(self.admin_customer)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['company_name'], 'sktelecom')

    def test_failed_create_account_with_existed_company_name(self):
        """
        이미 존재하는 회사명으로 회원가입을 시도하는 경우
        """
        url = reverse('customer-list')
        data = {
            "company_name": "programmers",
            "password": "",
            "is_active": True,
            "is_admin": False,
        }

        self.client.force_login(self.admin_customer)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_failed_create_account_with_no_credentials(self):
        """
        어드민이 아닌 사용자가 고객 등록을 시도하는 경우
        """
        url = reverse('customer-list')
        data = {
            "company_name": "naver",
            "password": "",
            "is_active": True,
            "is_admin": False,
        }

        self.client.force_login(self.normal_customer)
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_customer_list(self):
        """
        고객 리스트를 조회하는 경우
        """
        url = reverse('customer-list')

        self.client.force_login(self.admin_customer)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["count"], 2)
        self.assertEqual(response.json()["next"], None)

    def test_patch_customer(self):
        """
        고객 정보를 수정하는 경우
        """
        url = reverse('customer-detail', args=[self.normal_customer.id])
        data = {
            "company_name": "programmers_recruit",
        }

        self.client.force_login(self.admin_customer)
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()['company_name'], 'programmers_recruit')

    def test_delete_customer(self):
        """
        고객 정보를 삭제하는 경우
        """
        url = reverse('customer-detail', args=[self.normal_customer.id])

        self.client.force_login(self.admin_customer)
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Customer.objects.count(), 1)
