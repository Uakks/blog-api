"""Tests for email login and custom user creation."""

from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()


class UserManagerTests(APITestCase):
    def test_create_user_normalizes_email_and_hashes_password(self) -> None:
        user = User.objects.create_user(
            email=" TeST@EXAMPLE.COM ",
            first_name="Jane",
            last_name="Doe",
            password="ExamplePass1234!",
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("ExamplePass1234!"))
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

    def test_create_superuser_sets_staff_and_superuser(self) -> None:
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="ExamplePass1234!",
            first_name="Blog",
            last_name="Admin",
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_user_requires_first_and_last_name(self) -> None:
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="user@example.com", password="Secret123456"
            )


class AuthenticationTests(APITestCase):
    def setUp(self) -> None:
        self.password = "ExamplePass1234!"
        self.user = User.objects.create_user(
            email="jane@example.com",
            password=self.password,
            first_name="Jane",
            last_name="Doe",
        )

    def test_register_user(self) -> None:
        response = self.client.post(
            reverse("register"),
            {
                "email": "NEW@example.com",
                "first_name": "New",
                "last_name": "User",
                "password": "ExamplePass1234!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(email="new@example.com").count(), 1)
        self.assertNotIn("password", response.data)

    def test_register_duplicate_email_case_insensitive(self) -> None:
        response = self.client.post(
            reverse("register"),
            {
                "email": "JANE@EXAMPLE.COM",
                "first_name": "Jane",
                "last_name": "Doe",
                "password": self.password,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_jwt_with_email(self) -> None:
        response = self.client.post(
            reverse("token_obtain_pair"),
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
