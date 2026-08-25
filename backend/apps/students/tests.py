from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.constants import DEFAULT_ROLES
from apps.accounts.models import Permission, Role, User
from apps.accounts.services import sync_permissions, sync_roles
from apps.classes.models import AcademicSession
from apps.students.models import Student
from apps.students.services import next_admission_number, next_enrolment_identifiers, next_student_id


class EnrolmentIdentifierTests(APITestCase):
    """The student ID and admission number the office issues on admission."""

    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)

        cls.admin = User.objects.create_superuser(
            email="head@example.com", full_name="Head Teacher", password="StrongPass!2026"
        )

        viewer_role = Role.objects.create(slug="student-viewer", name="Student viewer")
        viewer_role.permissions.set(Permission.objects.filter(code="student.view"))
        cls.viewer = User.objects.create_user(
            email="clerk@example.com", full_name="Office Clerk", password="StrongPass!2026", role=viewer_role
        )

        AcademicSession.objects.create(
            name="2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31), is_current=True
        )

    def setUp(self):
        self.url = reverse("v1:student-next-identifiers")
        self.list_url = reverse("v1:student-list")

    # --- generation ------------------------------------------------------

    def test_the_first_admission_starts_the_sequence_at_one(self):
        self.assertEqual(next_student_id(), "THC-2026-0001")
        self.assertEqual(next_admission_number(), "ADM-2026-0001")

    def test_each_admission_advances_the_number_by_one(self):
        Student.objects.create(full_name="First", student_id="THC-2026-0001", admission_number="ADM-2026-0001")

        self.assertEqual(next_enrolment_identifiers(), {
            "student_id": "THC-2026-0002",
            "admission_number": "ADM-2026-0002",
        })

    def test_the_sequence_follows_the_highest_number_not_the_row_count(self):
        """A gap left by a hand-typed ID must not hand the same number out twice."""
        Student.objects.create(full_name="Jumped", student_id="THC-2026-0042", admission_number="ADM-2026-0042")

        self.assertEqual(next_student_id(), "THC-2026-0043")

    def test_a_soft_deleted_student_keeps_its_number(self):
        student = Student.objects.create(
            full_name="Left", student_id="THC-2026-0001", admission_number="ADM-2026-0001"
        )
        student.soft_delete()

        # Reissuing 0001 would collide with the row that still holds it.
        self.assertEqual(next_student_id(), "THC-2026-0002")

    def test_a_code_that_does_not_end_in_digits_is_ignored(self):
        Student.objects.create(full_name="Odd", student_id="THC-2026-TEMP", admission_number="ADM-2026-TEMP")

        self.assertEqual(next_student_id(), "THC-2026-0001")

    def test_the_year_comes_from_the_current_session_not_the_calendar(self):
        AcademicSession.objects.update(is_current=False)
        AcademicSession.objects.create(
            name="2031", start_date=date(2031, 1, 1), end_date=date(2031, 12, 31), is_current=True
        )

        self.assertEqual(next_student_id(), "THC-2031-0001")

    # --- the endpoint ----------------------------------------------------

    def test_the_endpoint_returns_both_codes(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"student_id": "THC-2026-0001", "admission_number": "ADM-2026-0001"})

    def test_the_endpoint_needs_the_create_permission(self):
        """Being able to read the register is not the same as issuing a number."""
        self.client.force_authenticate(self.viewer)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_the_endpoint_is_closed_to_anonymous_callers(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    # --- creating --------------------------------------------------------

    def test_admitting_without_codes_generates_them(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(self.list_url, {"full_name": "Unnamed Pupil"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["student_id"], "THC-2026-0001")
        self.assertEqual(response.data["admission_number"], "ADM-2026-0001")

    def test_a_typed_code_is_kept_as_given(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            self.list_url,
            {"full_name": "Transferred In", "student_id": "old-4477", "admission_number": "old-adm-4477"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["student_id"], "OLD-4477")
        self.assertEqual(response.data["admission_number"], "OLD-ADM-4477")

    def test_a_duplicate_code_is_rejected_rather_than_silently_changed(self):
        Student.objects.create(full_name="Held", student_id="THC-2026-0001", admission_number="ADM-2026-0001")
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            self.list_url,
            {"full_name": "Clash", "student_id": "thc-2026-0001", "admission_number": "ADM-2026-0009"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("student_id", response.data["errors"])

    def test_two_admissions_in_a_row_get_different_codes(self):
        self.client.force_authenticate(self.admin)

        first = self.client.post(self.list_url, {"full_name": "One"}, format="json")
        second = self.client.post(self.list_url, {"full_name": "Two"}, format="json")

        self.assertEqual(first.data["student_id"], "THC-2026-0001")
        self.assertEqual(second.data["student_id"], "THC-2026-0002")

    # --- editing ---------------------------------------------------------

    def test_editing_without_touching_the_id_keeps_it(self):
        student = Student.objects.create(
            full_name="Before", student_id="THC-2026-0001", admission_number="ADM-2026-0001"
        )
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            reverse("v1:student-detail", args=[student.id]), {"full_name": "After"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["student_id"], "THC-2026-0001")

    def test_blanking_the_id_on_an_edit_leaves_the_stored_one_alone(self):
        """An empty field on an edit means "untouched", never "wipe the code"."""
        student = Student.objects.create(
            full_name="Before", student_id="THC-2026-0001", admission_number="ADM-2026-0001"
        )
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            reverse("v1:student-detail", args=[student.id]), {"student_id": ""}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        student.refresh_from_db()
        self.assertEqual(student.student_id, "THC-2026-0001")

    def test_an_id_can_be_changed_to_a_free_one(self):
        student = Student.objects.create(
            full_name="Before", student_id="THC-2026-0001", admission_number="ADM-2026-0001"
        )
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            reverse("v1:student-detail", args=[student.id]), {"student_id": "THC-2026-0500"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["student_id"], "THC-2026-0500")
