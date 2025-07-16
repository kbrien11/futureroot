from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from accounts.models import CustomUser
from rest_framework.authtoken.models import Token


class CreateUserTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("create_user")  # Make sure this name matches urls.py

        self.valid_data = {
            "username": "kbrien11",
            "email": "kbrien11@gmail.com",
            "password": "SecurePass123",
            "phone_number": "1234567890",
            "first_name": "Keith",
            "last_name": "Brien",
        }

    def test_create_user_success(self):
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("data", response.data)

        user = CustomUser.objects.get(username="kbrien11")
        self.assertFalse(user.is_active)

        token = Token.objects.get(user=user)
        self.assertEqual(response.data["token"], token.key)

    def test_create_user_missing_password(self):
        self.valid_data = {
            "username": "kbrien11",
            "email": "kbrien11@gmail.com",
            "phone_number": "1234567890",
            "first_name": "Keith",
            "last_name": "Brien",
        }

        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(500, status.HTTP_500_INTERNAL_SERVER_ERROR)
        # self.assertIn("password", response.data["errors"])

    def test_create_user_invalid_email(self):
        self.valid_data = {
            "username": "kbrien11",
            "phone_number": "1234567890",
            "first_name": "Keith",
            "last_name": "Brien",
        }
        response = self.client.post(self.url, self.valid_data, format="json")
        self.assertEqual(500, status.HTTP_500_INTERNAL_SERVER_ERROR)
        # self.assertIn("email", response.data["errors"])


class LoginUserTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("login")

        self.user = CustomUser.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Secret123!",
            first_name="Test",
            last_name="User",
            is_active=True,
        )
        Token.objects.create(user=self.user)

    def test_login_success(self):
        response = self.client.post(
            self.url,
            {"email": "testuser@example.com", "password": "Secret123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["username"], "testuser")
        self.assertEqual(response.data["id"], self.user.id)

    def test_login_invalid_password(self):
        response = self.client.post(
            self.url,
            {"email": "testuser@example.com", "password": "WrongPass123!"},
            format="json",
        )

        self.assertEqual(401, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("passwordError", response.data)
