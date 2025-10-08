from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from user.api.v1.serializers import UserMeSerializer, UserRegisterSerializer

User = get_user_model()

REGISTER_URL = reverse("user_api_v1:user_register")
ME_URL = reverse("user_api_v1:user_me")


def create_user(**kwargs) -> User:
    defaults = {
        "email": "user@example.com",
        "password": "StrongPass#12345",
        "first_name": "John",
        "last_name": "Doe",
    }
    defaults.update(kwargs)
    password = defaults.pop("password")
    return User.objects.create_user(password=password, **defaults)


class UserSerializerTests(TestCase):
    def test_user_me_serializer_hides_sensitive_fields_on_get(self):
        user = create_user()
        ser = UserMeSerializer(instance=user)
        self.assertNotIn("password", ser.data)
        self.assertNotIn("current_password", ser.data)
        self.assertIn("email", ser.data)
        self.assertIn("first_name", ser.data)
        self.assertIn("last_name", ser.data)

    def test_user_register_serializer_success(self):
        payload = {
            "email": "new@example.com",
            "password": "NewStrong#12345",
            "password2": "NewStrong#12345",
            "first_name": "Neo",
            "last_name": "Anderson",
        }
        ser = UserRegisterSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)
        user = ser.save()
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.check_password("NewStrong#12345"))

    def test_user_register_serializer_password_mismatch(self):
        payload = {
            "email": "new2@example.com",
            "password": "NewStrong#12345",
            "password2": "Mismatch#12345",
            "first_name": "A",
            "last_name": "B",
        }
        ser = UserRegisterSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("password2", ser.errors)

    def test_user_register_serializer_email_unique(self):
        create_user(email="dup@example.com")
        payload = {
            "email": "dup@example.com",
            "password": "NewStrong#12345",
            "password2": "NewStrong#12345",
            "first_name": "A",
            "last_name": "B",
        }
        ser = UserRegisterSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("email", ser.errors)


class AccountsApiAnonTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_create_user(self):
        payload = {
            "email": "api_new@example.com",
            "password": "NewStrong#12345",
            "password2": "NewStrong#12345",
            "first_name": "Api",
            "last_name": "User",
        }
        res = self.client.post(REGISTER_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["email"], payload["email"])
        self.assertNotIn("password", res.data)
        self.assertNotIn("password2", res.data)
        user = User.objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))

    def test_me_requires_auth(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AccountsApiAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_password = "StrongPass#12345"
        self.user = create_user(
            email="me@example.com",
            password=self.user_password,
            first_name="Old",
            last_name="Name",
        )
        self.client.force_authenticate(self.user)

    def test_me_get_profile(self):
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], "me@example.com")
        self.assertNotIn("password", res.data)
        self.assertNotIn("current_password", res.data)

    def test_me_patch_names_only(self):
        payload = {"first_name": "New", "last_name": "Name"}
        res = self.client.patch(ME_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "New")
        self.assertEqual(self.user.last_name, "Name")

    def test_me_change_email_requires_current_password(self):
        res = self.client.patch(ME_URL, {"email": "new@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "me@example.com")

    def test_me_change_email_wrong_current_password(self):
        res = self.client.patch(
            ME_URL,
            {"email": "new@example.com", "current_password": "Wrong#123"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_change_email_ok(self):
        res = self.client.patch(
            ME_URL,
            {"email": "new@example.com", "current_password": self.user_password},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")

    def test_me_change_password_requires_current_password(self):
        res = self.client.patch(
            ME_URL, {"password": "AnotherStrong#12345"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(self.user.check_password(self.user_password))

    def test_me_change_password_ok(self):
        new_pwd = "AnotherStrong#12345"
        res = self.client.patch(
            ME_URL,
            {"password": new_pwd, "current_password": self.user_password},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_pwd))

    def test_me_change_email_unique(self):
        create_user(email="taken@example.com")
        res = self.client.patch(
            ME_URL,
            {"email": "taken@example.com", "current_password": self.user_password},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", res.data)
