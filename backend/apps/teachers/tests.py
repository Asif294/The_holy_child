from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.constants import DEFAULT_ROLES
from apps.accounts.models import Permission, Role, User
from apps.accounts.services import sync_permissions, sync_roles
from apps.teachers.models import Teacher
from apps.teachers.services import next_employee_id


class EmployeeIdentifierTests(APITestCase):
    """The employee ID the office issues when a teacher joins the register."""

    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)

        cls.admin = User.objects.create_superuser(
            email="head@example.com", full_name="Head Teacher", password="StrongPass!2026"
        )

        viewer_role = Role.objects.create(slug="teacher-viewer", name="Teacher viewer")
        viewer_role.permissions.set(Permission.objects.filter(code="teacher.view"))
        cls.viewer = User.objects.create_user(
            email="clerk@example.com", full_name="Office Clerk", password="StrongPass!2026", role=viewer_role
        )

    def setUp(self):
        self.url = reverse("v1:teacher-next-employee-id")
        self.list_url = reverse("v1:teacher-list")

    # --- generation ------------------------------------------------------

    def test_the_first_teacher_starts_the_sequence_at_one(self):
        self.assertEqual(next_employee_id(), "THC-T-0001")

    def test_each_teacher_advances_the_number_by_one(self):
        Teacher.objects.create(full_name="First", employee_id="THC-T-0001")

        self.assertEqual(next_employee_id(), "THC-T-0002")

    def test_the_sequence_follows_the_highest_number_not_the_row_count(self):
        Teacher.objects.create(full_name="Jumped", employee_id="THC-T-0042")

        self.assertEqual(next_employee_id(), "THC-T-0043")

    def test_a_resigned_teacher_keeps_their_number(self):
        teacher = Teacher.objects.create(full_name="Left", employee_id="THC-T-0001")
        teacher.soft_delete()

        self.assertEqual(next_employee_id(), "THC-T-0002")

    def test_staff_numbering_does_not_restart_each_year(self):
        """Unlike a student ID, an employee ID carries no year and never resets."""
        Teacher.objects.create(full_name="Veteran", employee_id="THC-T-0120")

        self.assertEqual(next_employee_id(), "THC-T-0121")

    def test_a_code_that_does_not_end_in_digits_is_ignored(self):
        Teacher.objects.create(full_name="Odd", employee_id="THC-T-TEMP")

        self.assertEqual(next_employee_id(), "THC-T-0001")

    # --- the endpoint ----------------------------------------------------

    def test_the_endpoint_returns_the_next_id(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"employee_id": "THC-T-0001"})

    def test_the_endpoint_needs_the_create_permission(self):
        self.client.force_authenticate(self.viewer)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_the_endpoint_is_closed_to_anonymous_callers(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    # --- creating --------------------------------------------------------

    def test_adding_a_teacher_without_an_id_generates_one(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(self.list_url, {"full_name": "Unnamed Teacher"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["employee_id"], "THC-T-0001")

    def test_a_typed_id_is_kept_as_given(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            self.list_url, {"full_name": "Transferred In", "employee_id": "legacy-77"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["employee_id"], "LEGACY-77")

    def test_a_duplicate_id_is_rejected_rather_than_silently_changed(self):
        Teacher.objects.create(full_name="Held", employee_id="THC-T-0001")
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            self.list_url, {"full_name": "Clash", "employee_id": "thc-t-0001"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("employee_id", response.data["errors"])

    def test_two_teachers_added_in_a_row_get_different_ids(self):
        self.client.force_authenticate(self.admin)

        first = self.client.post(self.list_url, {"full_name": "One"}, format="json")
        second = self.client.post(self.list_url, {"full_name": "Two"}, format="json")

        self.assertEqual(first.data["employee_id"], "THC-T-0001")
        self.assertEqual(second.data["employee_id"], "THC-T-0002")

    # --- editing ---------------------------------------------------------

    def test_blanking_the_id_on_an_edit_leaves_the_stored_one_alone(self):
        teacher = Teacher.objects.create(full_name="Before", employee_id="THC-T-0001")
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            reverse("v1:teacher-detail", args=[teacher.id]), {"employee_id": ""}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        teacher.refresh_from_db()
        self.assertEqual(teacher.employee_id, "THC-T-0001")

    def test_an_id_can_be_changed_to_a_free_one(self):
        teacher = Teacher.objects.create(full_name="Before", employee_id="THC-T-0001")
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            reverse("v1:teacher-detail", args=[teacher.id]), {"employee_id": "THC-T-0500"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["employee_id"], "THC-T-0500")


class EmployeeIdAvailabilityTests(APITestCase):
    """The live "is this ID free?" check behind the staff form."""

    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)
        cls.admin = User.objects.create_superuser(
            email="head@example.com", full_name="Head Teacher", password="StrongPass!2026"
        )
        cls.teacher = Teacher.objects.create(full_name="On staff", employee_id="THC-T-0001")

    def setUp(self):
        self.url = reverse("v1:teacher-check-employee-id")
        self.client.force_authenticate(self.admin)

    def test_a_free_id_reports_nothing(self):
        response = self.client.get(self.url, {"employee_id": "THC-T-0777"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {})

    def test_a_taken_id_reports_the_clash(self):
        response = self.client.get(self.url, {"employee_id": "THC-T-0001"})

        self.assertEqual(response.data, {"employee_id": "A teacher with this employee ID already exists."})

    def test_the_check_ignores_case(self):
        response = self.client.get(self.url, {"employee_id": "thc-t-0001"})

        self.assertIn("employee_id", response.data)

    def test_a_teachers_own_id_is_not_a_clash_when_editing(self):
        response = self.client.get(self.url, {"employee_id": "THC-T-0001", "exclude": self.teacher.id})

        self.assertEqual(response.data, {})

    def test_a_resigned_teacher_still_holds_their_id(self):
        self.teacher.soft_delete()

        response = self.client.get(self.url, {"employee_id": "THC-T-0001"})

        self.assertIn("employee_id", response.data)

    def test_an_empty_value_is_not_a_clash(self):
        response = self.client.get(self.url, {"employee_id": ""})

        self.assertEqual(response.data, {})

    def test_the_message_matches_what_the_save_would_say(self):
        """What the form says while typing must be what it says on save."""
        checked = self.client.get(self.url, {"employee_id": "thc-t-0001"}).data
        saved = self.client.post(
            reverse("v1:teacher-list"), {"full_name": "Clash", "employee_id": "thc-t-0001"}, format="json"
        )

        self.assertEqual(checked["employee_id"], saved.data["errors"]["employee_id"][0])

    def test_the_same_message_regardless_of_how_it_was_typed(self):
        """An exact match and a differently-cased one are the same rejection."""
        exact = self.client.post(
            reverse("v1:teacher-list"), {"full_name": "A", "employee_id": "THC-T-0001"}, format="json"
        )
        cased = self.client.post(
            reverse("v1:teacher-list"), {"full_name": "B", "employee_id": "thc-t-0001"}, format="json"
        )

        self.assertEqual(exact.data["errors"]["employee_id"], cased.data["errors"]["employee_id"])

    def test_the_check_is_closed_to_anonymous_callers(self):
        self.client.force_authenticate(None)

        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)


class StaffAccountTests(APITestCase):
    """The login account issued alongside a new teacher."""

    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)
        cls.admin = User.objects.create_superuser(
            email="head@example.com", full_name="Head Teacher", password="StrongPass!2026"
        )

    def setUp(self):
        self.list_url = reverse("v1:teacher-list")
        self.client.force_authenticate(self.admin)

    def payload(self, **overrides):
        return {
            "full_name": "Asif Ahmed",
            "email": "asif@holychildschool.edu.bd",
            "phone": "+8801700000000",
            "gender": "male",
            "date_of_birth": "1990-04-11",
            "address": "12 School Road, Dhaka",
            **overrides,
        }

    def test_adding_a_teacher_issues_the_account_that_goes_with_the_record(self):
        response = self.client.post(self.list_url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        teacher = Teacher.objects.get(id=response.data["id"])
        self.assertIsNotNone(teacher.user)
        self.assertEqual(teacher.user.email, "asif@holychildschool.edu.bd")
        self.assertEqual(response.data["user_email"], "asif@holychildschool.edu.bd")

    def test_the_account_carries_the_details_the_form_collected(self):
        response = self.client.post(self.list_url, self.payload(), format="json")

        user = Teacher.objects.get(id=response.data["id"]).user
        self.assertEqual(user.full_name, "Asif Ahmed")
        self.assertEqual(user.phone, "+8801700000000")
        self.assertEqual(user.gender, "male")
        self.assertEqual(str(user.date_of_birth), "1990-04-11")
        self.assertEqual(user.address, "12 School Road, Dhaka")

    def test_the_phone_number_is_the_first_password(self):
        response = self.client.post(self.list_url, self.payload(), format="json")

        user = Teacher.objects.get(id=response.data["id"]).user
        self.assertTrue(user.check_password("+8801700000000"))

    def test_the_account_signs_in_as_a_teacher(self):
        response = self.client.post(self.list_url, self.payload(), format="json")

        user = Teacher.objects.get(id=response.data["id"]).user
        self.assertEqual(user.role.slug, "teacher")
        self.assertIn("attendance.create", user.get_permission_codes())
        self.assertNotIn("teacher.create", user.get_permission_codes())

    def test_a_teacher_with_no_email_is_recorded_without_an_account(self):
        response = self.client.post(self.list_url, self.payload(email=""), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(Teacher.objects.get(id=response.data["id"]).user)

    def test_a_teacher_with_no_phone_has_no_password_to_be_given(self):
        response = self.client.post(self.list_url, self.payload(phone=""), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(Teacher.objects.get(id=response.data["id"]).user)
        self.assertFalse(User.objects.filter(email="asif@holychildschool.edu.bd").exists())

    def test_an_account_that_already_exists_is_linked_rather_than_duplicated(self):
        existing = User.objects.create_user(
            email="asif@holychildschool.edu.bd", full_name="Asif Ahmed", password="StrongPass!2026"
        )

        response = self.client.post(self.list_url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Teacher.objects.get(id=response.data["id"]).user_id, existing.id)
        self.assertEqual(User.objects.filter(email="asif@holychildschool.edu.bd").count(), 1)
        existing.refresh_from_db()
        self.assertTrue(existing.check_password("StrongPass!2026"))

    def test_an_email_that_already_signs_in_as_another_teacher_is_rejected(self):
        first = self.client.post(self.list_url, self.payload(), format="json")

        second = self.client.post(
            self.list_url, self.payload(full_name="Someone Else", phone="+8801700000001"), format="json"
        )

        self.assertEqual(second.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("email", second.data["errors"])
        self.assertIn(first.data["employee_id"], str(second.data["errors"]["email"]))

    def test_a_phone_number_already_on_another_account_is_rejected(self):
        User.objects.create_user(
            email="someone@example.com",
            full_name="Someone",
            password="StrongPass!2026",
            phone="01700000000",
        )

        response = self.client.post(self.list_url, self.payload(), format="json")

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("phone", response.data["errors"])

    def test_a_rejected_account_leaves_no_half_registered_teacher(self):
        User.objects.create_user(
            email="someone@example.com",
            full_name="Someone",
            password="StrongPass!2026",
            phone="01700000000",
        )

        self.client.post(self.list_url, self.payload(), format="json")

        self.assertFalse(Teacher.objects.exists())

    def test_a_teacher_linked_to_a_named_account_keeps_that_one(self):
        chosen = User.objects.create_user(
            email="chosen@example.com", full_name="Chosen", password="StrongPass!2026"
        )

        response = self.client.post(self.list_url, self.payload(user=chosen.id), format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Teacher.objects.get(id=response.data["id"]).user_id, chosen.id)
        self.assertFalse(User.objects.filter(email="asif@holychildschool.edu.bd").exists())

    def test_editing_a_teacher_does_not_issue_a_second_account(self):
        created = self.client.post(self.list_url, self.payload(), format="json")

        self.client.patch(
            reverse("v1:teacher-detail", args=[created.data["id"]]),
            {"email": "moved@holychildschool.edu.bd"},
            format="json",
        )

        self.assertEqual(User.objects.filter(email="moved@holychildschool.edu.bd").count(), 0)
