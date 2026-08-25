"""
The security contract this project stands on:

* an unauthenticated request is rejected with **401**;
* an authenticated request without the required permission code is rejected
  with **403** — regardless of what the frontend chose to render;
* granting the code through a role immediately unlocks the endpoint.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.constants import ALL_PERMISSION_CODES, DEFAULT_ROLES
from apps.accounts.models import Permission, Role, User
from apps.accounts.services import sync_permissions, sync_roles
from apps.students.models import Student


class PermissionEnforcementTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)
        cls.teacher_role = Role.objects.get(slug="teacher")
        cls.accountant_role = Role.objects.get(slug="accountant")

        cls.teacher = User.objects.create_user(
            email="teacher@holychild.test", password="StrongPass!2026",
            full_name="Nasrin Akter", role=cls.teacher_role,
        )
        cls.accountant = User.objects.create_user(
            email="accountant@holychild.test", password="StrongPass!2026",
            full_name="Kamal Hossain", role=cls.accountant_role,
        )
        cls.student = Student.objects.create(
            student_id="THC-2026-0001", admission_number="ADM-0001", full_name="Tanvir Ahmed"
        )

    # ------------------------------------------------------------------ #
    # 401 — unauthenticated
    # ------------------------------------------------------------------ #
    def test_unauthenticated_list_returns_401(self):
        response = self.client.get(reverse("v1:student-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["code"], "AUTHENTICATION_FAILED")

    def test_unauthenticated_write_returns_401(self):
        response = self.client.post(reverse("v1:student-list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ------------------------------------------------------------------ #
    # 403 — authenticated, permission missing
    # ------------------------------------------------------------------ #
    def test_teacher_may_read_students(self):
        """The Teacher role holds student.view."""
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(reverse("v1:student-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_teacher_may_not_create_students(self):
        """The Teacher role holds student.view but not student.create."""
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(
            reverse("v1:student-list"),
            {"student_id": "THC-2026-0002", "admission_number": "ADM-0002", "full_name": "New Student"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "PERMISSION_DENIED")
        self.assertFalse(response.data["success"])

    def test_teacher_may_not_delete_students(self):
        self.client.force_authenticate(user=self.teacher)
        response = self.client.delete(reverse("v1:student-detail", args=[self.student.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_may_not_manage_roles(self):
        self.client.force_authenticate(user=self.teacher)
        self.assertEqual(self.client.get(reverse("v1:role-list")).status_code, status.HTTP_403_FORBIDDEN)

    def test_accountant_may_not_read_attendance_but_may_read_fees(self):
        self.client.force_authenticate(user=self.accountant)
        self.assertEqual(self.client.get(reverse("v1:attendance-list")).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get(reverse("v1:invoice-list")).status_code, status.HTTP_200_OK)

    # ------------------------------------------------------------------ #
    # Granting a code unlocks the endpoint
    # ------------------------------------------------------------------ #
    def test_granting_the_code_immediately_unlocks_the_endpoint(self):
        self.client.force_authenticate(user=self.teacher)
        payload = {"student_id": "THC-2026-0003", "admission_number": "ADM-0003", "full_name": "Granted Student"}
        self.assertEqual(
            self.client.post(reverse("v1:student-list"), payload, format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )

        self.teacher_role.permissions.add(Permission.objects.get(code="student.create"))

        self.assertEqual(
            self.client.post(reverse("v1:student-list"), payload, format="json").status_code,
            status.HTTP_201_CREATED,
        )

    def test_revoking_the_code_locks_the_endpoint_again(self):
        self.client.force_authenticate(user=self.teacher)
        self.assertEqual(self.client.get(reverse("v1:student-list")).status_code, status.HTTP_200_OK)

        self.teacher_role.permissions.remove(Permission.objects.get(code="student.view"))

        self.assertEqual(self.client.get(reverse("v1:student-list")).status_code, status.HTTP_403_FORBIDDEN)

    def test_a_user_without_a_role_holds_no_permissions(self):
        orphan = User.objects.create_user(
            email="orphan@holychild.test", password="StrongPass!2026", full_name="No Role"
        )
        self.assertEqual(orphan.get_permission_codes(), set())
        self.client.force_authenticate(user=orphan)
        self.assertEqual(self.client.get(reverse("v1:student-list")).status_code, status.HTTP_403_FORBIDDEN)

    def test_a_superuser_bypasses_every_check(self):
        admin = User.objects.create_superuser(
            email="admin@holychild.test", password="StrongPass!2026", full_name="Admin"
        )
        self.assertEqual(admin.get_permission_codes(), set(ALL_PERMISSION_CODES))
        self.client.force_authenticate(user=admin)
        self.assertEqual(self.client.get(reverse("v1:student-list")).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("v1:role-list")).status_code, status.HTTP_200_OK)

    def test_a_deactivated_role_strips_every_permission(self):
        self.teacher_role.is_active = False
        self.teacher_role.save(update_fields=["is_active"])
        self.assertEqual(self.teacher.get_permission_codes(), set())


class DynamicRoleTests(APITestCase):
    """The end-to-end flow an administrator follows to invent a new role."""

    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)
        cls.admin = User.objects.create_superuser(
            email="admin@holychild.test", password="StrongPass!2026", full_name="Admin"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.admin)

    def test_create_role_assign_to_user_and_watch_access_follow(self):
        # 1. An administrator invents a role with a hand-picked permission set.
        create = self.client.post(
            reverse("v1:role-list"),
            {
                "name": "Librarian",
                "description": "Runs the school library.",
                "permissions": ["student.view", "class.view", "dashboard.view"],
            },
            format="json",
        )
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create.data["slug"], "librarian")
        self.assertCountEqual(create.data["permissions"], ["student.view", "class.view", "dashboard.view"])
        role_id = create.data["id"]

        # 2. A user is created against that role.
        user_response = self.client.post(
            reverse("v1:user-list"),
            {
                "full_name": "Library Staff",
                "email": "library@holychild.test",
                "password": "StrongPass!2026",
                "role_id": role_id,
            },
            format="json",
        )
        self.assertEqual(user_response.status_code, status.HTTP_201_CREATED)
        librarian = User.objects.get(email="library@holychild.test")

        # 3. The user inherits exactly the codes the role carries.
        self.client.force_authenticate(user=librarian)
        self.assertEqual(self.client.get(reverse("v1:student-list")).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("v1:invoice-list")).status_code, status.HTTP_403_FORBIDDEN)

        # 4. Editing the role changes access without touching the user.
        self.client.force_authenticate(user=self.admin)
        self.client.post(
            reverse("v1:role-set-permissions", args=[role_id]),
            {"permissions": ["student.view", "fee.view"]},
            format="json",
        )
        self.client.force_authenticate(user=librarian)
        self.assertEqual(self.client.get(reverse("v1:invoice-list")).status_code, status.HTTP_200_OK)

    def test_system_roles_cannot_be_deleted(self):
        super_admin = Role.objects.get(slug="super-admin")
        response = self.client.delete(reverse("v1:role-detail", args=[super_admin.id]))
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_a_role_in_use_cannot_be_deleted(self):
        role = Role.objects.get(slug="teacher")
        User.objects.create_user(
            email="inuse@holychild.test", password="StrongPass!2026", full_name="In Use", role=role
        )
        response = self.client.delete(reverse("v1:role-detail", args=[role.id]))
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_duplicate_role_names_are_rejected(self):
        response = self.client.post(reverse("v1:role-list"), {"name": "Teacher"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertIn("name", response.data["errors"])

    def test_permission_catalogue_is_read_only(self):
        response = self.client.post(reverse("v1:permission-list"), {"code": "hack.all"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_grouped_permissions_are_nested_by_group_and_module(self):
        response = self.client.get(reverse("v1:permission-grouped"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        groups = {row["group"] for row in response.data}
        self.assertIn("Academics", groups)
        academics = next(row for row in response.data if row["group"] == "Academics")
        self.assertIn("student", {module["module"] for module in academics["modules"]})
