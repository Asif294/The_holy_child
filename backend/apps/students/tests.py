from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.constants import DEFAULT_ROLES
from apps.accounts.models import Permission, Role, User
from apps.accounts.services import sync_permissions, sync_roles
from apps.classes.models import AcademicSession, SchoolClass, Section
from apps.students.models import Student
from apps.students.services import (
    next_admission_number,
    next_enrolment_identifiers,
    next_roll_number,
    next_student_id,
)


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


class IdentifierAvailabilityTests(APITestCase):
    """The live "is this code free?" check behind the admission form."""

    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)
        cls.admin = User.objects.create_superuser(
            email="head@example.com", full_name="Head Teacher", password="StrongPass!2026"
        )
        cls.student = Student.objects.create(
            full_name="Enrolled", student_id="THC-2026-0001", admission_number="ADM-2026-0001"
        )

    def setUp(self):
        self.url = reverse("v1:student-check-identifiers")
        self.client.force_authenticate(self.admin)

    def test_a_free_code_reports_nothing(self):
        response = self.client.get(self.url, {"student_id": "THC-2026-0777"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})

    def test_a_taken_code_reports_the_clash(self):
        response = self.client.get(self.url, {"student_id": "THC-2026-0001"})

        self.assertEqual(response.data, {"student_id": "A student with this ID already exists."})

    def test_the_check_ignores_case(self):
        """`thc-2026-0001` and `THC-2026-0001` are the same code, and the save agrees."""
        response = self.client.get(self.url, {"student_id": "thc-2026-0001"})

        self.assertIn("student_id", response.data)

    def test_both_codes_can_be_checked_at_once(self):
        response = self.client.get(
            self.url, {"student_id": "THC-2026-0001", "admission_number": "ADM-2026-0001"}
        )

        self.assertEqual(set(response.data), {"student_id", "admission_number"})

    def test_only_the_clashing_code_is_reported(self):
        response = self.client.get(
            self.url, {"student_id": "THC-2026-0001", "admission_number": "ADM-2026-0999"}
        )

        self.assertEqual(set(response.data), {"student_id"})

    def test_a_students_own_code_is_not_a_clash_when_editing(self):
        response = self.client.get(
            self.url, {"student_id": "THC-2026-0001", "exclude": self.student.id}
        )

        self.assertEqual(response.data, {})

    def test_a_soft_deleted_student_still_holds_its_code(self):
        self.student.soft_delete()

        response = self.client.get(self.url, {"student_id": "THC-2026-0001"})

        self.assertIn("student_id", response.data)

    def test_an_empty_value_is_not_a_clash(self):
        """A blank field means "issue me one", not "check the empty string"."""
        response = self.client.get(self.url, {"student_id": ""})

        self.assertEqual(response.data, {})

    def test_the_message_matches_what_the_save_would_say(self):
        checked = self.client.get(self.url, {"student_id": "THC-2026-0001"}).data
        saved = self.client.post(
            reverse("v1:student-list"),
            {"full_name": "Clash", "student_id": "THC-2026-0001"},
            format="json",
        )

        self.assertEqual(checked["student_id"], saved.data["errors"]["student_id"][0])

    def test_the_check_is_closed_to_anonymous_callers(self):
        self.client.force_authenticate(None)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)


class NextRollNumberTests(APITestCase):
    """The roll the admission form fills in once a section is chosen."""

    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)
        cls.admin = User.objects.create_superuser(
            email="head@example.com", full_name="Head Teacher", password="StrongPass!2026"
        )
        school_class = SchoolClass.objects.create(name="Class 6", code="C6", order=6)
        cls.section_a = Section.objects.create(school_class=school_class, name="A")
        cls.section_b = Section.objects.create(school_class=school_class, name="B")

    def setUp(self):
        self.url = reverse("v1:student-next-roll")
        self.client.force_authenticate(self.admin)

    def enrol(self, roll, section=None, **extra):
        return Student.objects.create(
            full_name=f"Pupil {roll}",
            student_id=f"THC-2026-{roll:04d}",
            admission_number=f"ADM-2026-{roll:04d}",
            section=section or self.section_a,
            roll_number=roll,
            **extra,
        )

    def test_an_empty_section_starts_at_one(self):
        self.assertEqual(next_roll_number(self.section_a.id), 1)

    def test_the_next_roll_follows_the_highest_in_use(self):
        self.enrol(1)
        self.enrol(2)

        self.assertEqual(next_roll_number(self.section_a.id), 3)

    def test_a_gap_in_the_rolls_is_not_filled(self):
        """Following the highest keeps the number unique; filling gaps would not."""
        self.enrol(7)

        self.assertEqual(next_roll_number(self.section_a.id), 8)

    def test_rolls_are_counted_per_section_not_school_wide(self):
        self.enrol(1)
        self.enrol(2)

        self.assertEqual(next_roll_number(self.section_b.id), 1)

    def test_a_student_who_has_left_frees_their_roll(self):
        """Unlike a student ID, `(section, roll)` is unique only among live rows."""
        self.enrol(1)
        self.enrol(2).soft_delete()

        self.assertEqual(next_roll_number(self.section_a.id), 2)

    def test_a_student_without_a_roll_is_ignored(self):
        self.enrol(1)
        Student.objects.create(
            full_name="Unnumbered", student_id="THC-2026-0900", admission_number="ADM-2026-0900",
            section=self.section_a,
        )

        self.assertEqual(next_roll_number(self.section_a.id), 2)

    def test_the_endpoint_returns_the_next_roll(self):
        self.enrol(4)

        response = self.client.get(self.url, {"section": self.section_a.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"roll_number": 5})

    def test_the_endpoint_needs_a_section(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    def test_the_suggested_roll_is_actually_free(self):
        """The number handed out has to survive the save it was handed out for."""
        self.enrol(1)
        suggested = self.client.get(self.url, {"section": self.section_a.id}).data["roll_number"]

        response = self.client.post(
            reverse("v1:student-list"),
            {"full_name": "Next", "section": self.section_a.id, "roll_number": suggested},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["roll_number"], suggested)

    def test_the_endpoint_is_closed_to_anonymous_callers(self):
        self.client.force_authenticate(None)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)
