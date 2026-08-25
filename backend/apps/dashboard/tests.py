import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.constants import DEFAULT_ROLES
from apps.accounts.models import Permission, Role, User
from apps.accounts.services import sync_permissions, sync_roles
from apps.dashboard.models import SchoolProfile


def png_upload(name="crest.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), (10, 65, 137)).save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


class SchoolProfileTests(APITestCase):
    """The editable school identity behind the Settings screen."""

    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)

        cls.admin = User.objects.create_superuser(
            email="head@example.com", full_name="Head Teacher", password="StrongPass!2026"
        )

        viewer_role = Role.objects.create(slug="settings-viewer", name="Settings viewer")
        viewer_role.permissions.set(Permission.objects.filter(code="setting.view"))
        cls.viewer = User.objects.create_user(
            email="clerk@example.com", full_name="Office Clerk", password="StrongPass!2026", role=viewer_role
        )

    def setUp(self):
        self.url = reverse("v1:school-profile")

    def test_profile_seeds_itself_from_the_environment_defaults(self):
        """A fresh database has no row; the first read creates it."""
        self.assertFalse(SchoolProfile.objects.exists())

        profile = SchoolProfile.load()

        self.assertTrue(profile.name_en)
        self.assertEqual(SchoolProfile.objects.count(), 1)

    def test_load_never_creates_a_second_row(self):
        first, second = SchoolProfile.load(), SchoolProfile.load()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(SchoolProfile.objects.count(), 1)

    def test_address_is_composed_from_the_parts_that_are_set(self):
        profile = SchoolProfile.load()
        profile.village, profile.upazila = "Longorpara", "Sribordi"
        profile.district, profile.country = "", "Bangladesh"
        self.assertEqual(profile.address, "Longorpara, Sribordi, Bangladesh")

    def test_reading_the_profile_requires_authentication(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_updating_requires_the_update_permission(self):
        """`setting.view` alone reads but must not write."""
        self.client.force_authenticate(self.viewer)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)

        response = self.client.patch(self.url, {"phone": "+880 1999-999999"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(SchoolProfile.load().phone, "+880 1999-999999")

    def test_an_administrator_can_change_the_identity(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            self.url,
            {"name_en": "Holy Child High School", "phone": "+880 1712-345678", "village": "Longorpara"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        profile = SchoolProfile.load()
        self.assertEqual(profile.name_en, "Holy Child High School")
        self.assertEqual(profile.phone, "+880 1712-345678")

    def test_the_public_endpoint_serves_the_saved_values(self):
        """What an administrator saves is what the landing page shows."""
        self.client.force_authenticate(self.admin)
        self.client.patch(self.url, {"phone": "+880 1712-345678"}, format="json")
        self.client.force_authenticate(None)

        response = self.client.get(reverse("v1:school-info"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["phone"], "+880 1712-345678")

    def test_the_name_cannot_be_blanked(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.url, {"name_en": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertTrue(SchoolProfile.load().name_en)

    def test_a_logo_can_be_uploaded_and_is_served_publicly(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(self.url, {"logo": png_upload()}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["logo_url"])

        self.client.force_authenticate(None)
        public = self.client.get(reverse("v1:school-info"))
        self.assertIsNotNone(public.data["logo_url"])

        SchoolProfile.load().logo.delete(save=True)

    def test_a_non_image_upload_is_rejected(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            self.url,
            {"logo": SimpleUploadedFile("notes.txt", b"not an image", content_type="text/plain")},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertFalse(SchoolProfile.load().logo)

    def test_the_profile_cannot_be_deleted(self):
        with self.assertRaises(NotImplementedError):
            SchoolProfile.load().delete()
