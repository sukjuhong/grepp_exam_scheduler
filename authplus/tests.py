from django.urls import reverse
from rest_framework.test import APITestCase
from customers.models import Customer


class AuthAPITestCase(APITestCase):
    def setUp(self):
        self.test_password = 'testpassword'
        self.customer = Customer.objects.create_user(
            company_name="testcompany",
            password=self.test_password,
        )

    def test_login(self):
        """
        올바른 회사명과 비밀번호으로 로그인이 가능한지 확인
        """
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'company_name': self.customer.company_name,
            'password': self.test_password,
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('refresh_token', response.data)
        self.assertIn('access_token', response.data)
        self.assertIn('customer', response.data)

    def test_login_invalid_password(self):
        """
        잘못된 비밀번호로 로그인 시도 시 실패하는지 확인
        """
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'company_name': self.customer.company_name,
            'password': 'invalidpassword',
        })

        self.assertEqual(response.status_code, 401)

    def test_refresh_token(self):
        """
        리프레쉬 토큰을 사용하여 엑세스 토큰을 갱신할 수 있는지 확인
        """
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'company_name': self.customer.company_name,
            'password': self.test_password,
        })

        refresh_url = reverse('token_refresh')
        response = self.client.post(refresh_url, {
            'refresh_token': response.data['refresh_token'],
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('access_token', response.data)
