from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import DEFAULT_PROFILE_PICS

User = get_user_model()


class UserViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = "testuser"
        self.email = "test@example.com"
        self.password = "TestPass@123"
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            profile_picture=DEFAULT_PROFILE_PICS[0],
        )

    def test_register_success(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "NewPass@123",
                "profile_picture": DEFAULT_PROFILE_PICS[0],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_existing_email(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "anotheruser",
                "email": self.email,  # Existing email
                "password": "NewPass@123",
                "profile_picture": DEFAULT_PROFILE_PICS[0],
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_register_existing_username(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": self.username,  # Existing username
                "email": "another@example.com",
                "password": "NewPass@123",
                "profile_picture": DEFAULT_PROFILE_PICS[0],
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_register_invalid_password(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "weakpass",
                "email": "weak@example.com",
                "password": "123",  # Too weak
                "profile_picture": DEFAULT_PROFILE_PICS[0],
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_login_success(self):
        response = self.client.post(
            reverse("login"),
            {"email": self.email, "password": self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("conversations"))

    def test_login_invalid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {"email": self.email, "password": "WrongPass"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))

    def test_logout(self):
        self.client.login(email=self.email, password=self.password)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("login"))

    def test_profile_access_authenticated(self):
        self.client.login(email=self.email, password=self.password)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)

    def test_profile_access_unauthenticated(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

    def test_edit_profile_success(self):
        self.client.login(email=self.email, password=self.password)
        response = self.client.post(
            reverse("edit_profile"),
            {"username": "updated_user", "profile_picture": DEFAULT_PROFILE_PICS[1]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["success"], True)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "updated_user")
        self.assertEqual(self.user.profile_picture, DEFAULT_PROFILE_PICS[1])
