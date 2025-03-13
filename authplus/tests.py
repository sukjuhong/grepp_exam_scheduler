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
        올바른 회사명과 비밀번호으로 로그인이 가능한지 테스트합니다.
        """
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'company_name': self.customer.company_name,
            'password': self.test_password,
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('refreshToken', response.data)
        self.assertIn('accessToken', response.data)
        self.assertIn('customer', response.data)

    def test_refresh_token(self):
        """
        리프레쉬 토큰을 사용하여 엑세스 토큰을 갱신할 수 있는지 테스트합니다.
        """
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'company_name': self.customer.company_name,
            'password': self.test_password,
        })

        refresh_url = reverse('token_refresh')
        response = self.client.post(refresh_url, {
            'refreshToken': response.data['refreshToken'],
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('accessToken', response.data)
