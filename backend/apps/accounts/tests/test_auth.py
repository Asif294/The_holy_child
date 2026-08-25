from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.constants import DEFAULT_ROLES, DEFAULT_SELF_REGISTRATION_ROLE, ROLE_SUPER_ADMIN
from apps.accounts.models import Role, User
from apps.accounts.services import sync_permissions, sync_roles


class AuthenticationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)

    def test_registration_creates_user_with_the_default_role(self):
        response = self.client.post(
            reverse("v1:auth-register"),
            {
                "full_name": "Rahim Uddin",
                "email": "Rahim@Example.com",
                "password": "StrongPass!2026",
                "password_confirmation": "StrongPass!2026",
                "phone": "+8801700000000",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data["data"])

        user = User.objects.get(email="rahim@example.com")
        self.assertEqual(user.role.slug, DEFAULT_SELF_REGISTRATION_ROLE)

    def test_registration_ignores_a_self_assigned_privileged_role(self):
        """A registrant must not be able to promote themselves."""
        super_admin = Role.objects.get(slug=ROLE_SUPER_ADMIN)
        response = self.client.post(
            reverse("v1:auth-register"),
            {
                "full_name": "Sneaky User",
                "email": "sneaky@example.com",
                "password": "StrongPass!2026",
                "password_confirmation": "StrongPass!2026",
                "phone": "01700000001",
                "role": super_admin.id,
                "role_id": super_admin.id,
                "is_superuser": True,
                "is_staff": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email="sneaky@example.com")
        self.assertEqual(user.role.slug, DEFAULT_SELF_REGISTRATION_ROLE)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_registration_rejects_mismatched_password_confirmation(self):
        response = self.client.post(
            reverse("v1:auth-register"),
            {
                "full_name": "Mismatch User",
                "email": "mismatch@example.com",
                "password": "StrongPass!2026",
                "password_confirmation": "DifferentPass!2026",
                "phone": "01700000002",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["code"], "VALIDATION_ERROR")
        self.assertIn("password_confirmation", response.data["errors"])

    def test_registration_rejects_a_duplicate_email(self):
        User.objects.create_user(email="taken@example.com", password="StrongPass!2026", full_name="Taken")
        response = self.client.post(
            reverse("v1:auth-register"),
            {
                "full_name": "Second User",
                "email": "taken@example.com",
                "password": "StrongPass!2026",
                "password_confirmation": "StrongPass!2026",
                "phone": "01700000003",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("email", response.data["errors"])

    def test_registration_rejects_a_weak_password(self):
        response = self.client.post(
            reverse("v1:auth-register"),
            {
                "full_name": "Weak User",
                "email": "weak@example.com",
                "password": "12345678",
                "password_confirmation": "12345678",
                "phone": "01700000004",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("password", response.data["errors"])

    def test_login_returns_tokens_and_the_permission_list(self):
        teacher_role = Role.objects.get(slug="teacher")
        User.objects.create_user(
            email="teacher@holychild.test", password="StrongPass!2026", full_name="Nasrin Akter", role=teacher_role
        )

        response = self.client.post(
            reverse("v1:auth-login"),
            {"email": "teacher@holychild.test", "password": "StrongPass!2026"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], "Teacher")
        self.assertIn("attendance.create", response.data["user"]["permissions"])
        self.assertNotIn("student.delete", response.data["user"]["permissions"])

    def test_login_with_bad_credentials_returns_401(self):
        User.objects.create_user(email="real@holychild.test", password="StrongPass!2026", full_name="Real User")
        response = self.client.post(
            reverse("v1:auth-login"),
            {"email": "real@holychild.test", "password": "WrongPassword!1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])

    def test_me_requires_authentication(self):
        response = self.client.get(reverse("v1:auth-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["code"], "AUTHENTICATION_FAILED")

    def test_me_returns_the_caller_with_resolved_permissions(self):
        user = User.objects.create_user(
            email="me@holychild.test",
            password="StrongPass!2026",
            full_name="Me User",
            role=Role.objects.get(slug="accountant"),
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(reverse("v1:auth-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "me@holychild.test")
        self.assertIn("fee.create", response.data["permissions"])

    def test_logout_blacklists_the_refresh_token(self):
        user = User.objects.create_user(
            email="logout@holychild.test", password="StrongPass!2026", full_name="Logout User"
        )
        login = self.client.post(
            reverse("v1:auth-login"),
            {"email": "logout@holychild.test", "password": "StrongPass!2026"},
            format="json",
        )
        refresh = login.data["refresh"]

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse("v1:auth-logout"), {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=None)
        retry = self.client.post(reverse("v1:auth-token-refresh"), {"refresh": refresh}, format="json")
        self.assertEqual(retry.status_code, status.HTTP_401_UNAUTHORIZED)


class LoginIdentifierTests(APITestCase):
    """The login form takes one box; it must accept everything that names an account."""

    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)
        cls.password = "StrongPass!2026"
        cls.user = User.objects.create_user(
            email="nasrin@holychildschool.edu.bd",
            password=cls.password,
            full_name="Nasrin Akter",
            phone="+880 1700-111222",
            username="nasrin",
        )

    def login(self, payload):
        return self.client.post(reverse("v1:auth-login"), payload, format="json")

    def test_phone_is_stored_without_spaces_or_dashes(self):
        self.assertEqual(self.user.phone, "+8801700111222")

    def test_login_with_the_email_address(self):
        response = self.login({"identifier": self.user.email, "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_with_the_phone_number(self):
        response = self.login({"identifier": "+8801700111222", "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], self.user.email)

    def test_login_with_a_differently_formatted_phone_number(self):
        """Digits are what matter — punctuation is not a credential."""
        response = self.login({"identifier": "+880 1700 111 222", "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_with_the_username(self):
        response = self.login({"identifier": "nasrin", "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_the_email_key_still_works_as_an_alias(self):
        response = self.login({"email": self.user.email, "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_an_unknown_identifier_is_rejected(self):
        response = self.login({"identifier": "01999999999", "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_missing_identifier_is_a_validation_error(self):
        response = self.login({"password": self.password})
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_a_second_account_cannot_claim_the_same_phone_number(self):
        response = self.client.post(
            reverse("v1:auth-register"),
            {
                "full_name": "Copycat User",
                "email": "copycat@example.com",
                "password": "StrongPass!2026",
                "password_confirmation": "StrongPass!2026",
                "phone": "+880 1700-111222",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("phone", response.data["errors"])

    def test_a_deactivated_account_cannot_sign_in(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.login({"identifier": self.user.email, "password": self.password})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])
