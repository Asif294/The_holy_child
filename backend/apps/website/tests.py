"""
The public site is the one part of the API an anonymous visitor reaches, so the
line between "anyone may read this" and "only a permission code may change it"
is worth testing explicitly rather than trusting to the viewset base class.
"""
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.constants import DEFAULT_ROLES, ROLE_SCHOOL_ADMIN, ROLE_STUDENT
from apps.accounts.models import Role, User
from apps.accounts.services import sync_permissions, sync_roles
from apps.principal.models import Principal
from apps.teachers.models import Designation, Teacher
from apps.website.models import AboutSection, Achievement, SuccessfulStudent


class PublicSiteTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        sync_permissions()
        sync_roles(DEFAULT_ROLES)

        AboutSection.objects.create(
            pk=1, headline="A school with a story", mission="Educate every child.", vision="A literate Sribordi."
        )
        Achievement.objects.create(title="100% pass rate", year="2025", metric="100%")

        SuccessfulStudent.objects.create(academic_year="2025", full_name="Ayesha Siddika", result="GPA 5.00")
        SuccessfulStudent.objects.create(academic_year="2024", full_name="Tanvir Hasan", result="GPA 4.89")

        designation = Designation.objects.create(name="Senior Teacher", rank=1)
        Teacher.objects.create(employee_id="THC-T-0001", full_name="Nasrin Akter", designation=designation)
        Teacher.objects.create(
            employee_id="THC-T-0002", full_name="Retired Teacher", status=Teacher.Status.RESIGNED
        )

        Principal.objects.create(full_name="Md. Abdul Karim", office=Principal.Office.PRINCIPAL)
        Principal.objects.create(full_name="Salma Begum", office=Principal.Office.VICE_PRINCIPAL)

    # -- read: open to everyone ------------------------------------------ #
    def test_about_is_readable_without_signing_in(self):
        response = self.client.get(reverse("v1:public-about"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["headline"], "A school with a story")
        self.assertEqual(len(response.data["achievements"]), 1)

    def test_hero_slides_are_readable_without_signing_in(self):
        response = self.client.get(reverse("v1:public-hero-slides"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_the_teacher_directory_lists_only_active_staff(self):
        response = self.client.get(reverse("v1:public-teachers"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [row["full_name"] for row in response.data]
        self.assertEqual(names, ["Nasrin Akter"])

    def test_the_teacher_directory_withholds_contact_details(self):
        response = self.client.get(reverse("v1:public-teachers"))
        self.assertNotIn("email", response.data[0])
        self.assertNotIn("phone", response.data[0])
        self.assertNotIn("national_id", response.data[0])

    def test_administration_returns_both_seats(self):
        response = self.client.get(reverse("v1:public-administration"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["principal"]["full_name"], "Md. Abdul Karim")
        self.assertEqual(response.data["vice_principal"]["full_name"], "Salma Begum")

    def test_successful_students_can_be_filtered_by_year(self):
        response = self.client.get(reverse("v1:public-successful-students"), {"year": "2025"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([row["full_name"] for row in response.data], ["Ayesha Siddika"])

    def test_successful_students_defaults_to_every_year(self):
        response = self.client.get(reverse("v1:public-successful-students"))
        self.assertEqual(len(response.data), 2)

    def test_the_year_filter_options_come_back_newest_first(self):
        response = self.client.get(reverse("v1:public-achievement-years"))
        self.assertEqual(response.data, ["2025", "2024"])

    # -- write: permission codes only ------------------------------------ #
    def test_an_anonymous_visitor_cannot_add_a_hero_slide(self):
        response = self.client.post(reverse("v1:hero-slide-list"), {"title": "Sports day"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_a_signed_in_user_without_the_code_cannot_add_a_successful_student(self):
        student = User.objects.create_user(
            email="pupil@example.com",
            password="StrongPass!2026",
            full_name="A Pupil",
            role=Role.objects.get(slug=ROLE_STUDENT),
        )
        self.client.force_authenticate(student)
        response = self.client.post(
            reverse("v1:successful-student-list"),
            {"academic_year": "2025", "full_name": "Nobody"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_a_school_admin_can_add_a_successful_student(self):
        admin = User.objects.create_user(
            email="admin@example.com",
            password="StrongPass!2026",
            full_name="School Admin",
            role=Role.objects.get(slug=ROLE_SCHOOL_ADMIN),
        )
        self.client.force_authenticate(admin)
        response = self.client.post(
            reverse("v1:successful-student-list"),
            {"academic_year": "2026", "full_name": "Fahim Rahman", "result": "GPA 5.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SuccessfulStudent.objects.filter(full_name="Fahim Rahman").exists())

    def test_the_academic_year_must_look_like_a_year(self):
        admin = User.objects.create_user(
            email="admin2@example.com",
            password="StrongPass!2026",
            full_name="School Admin",
            role=Role.objects.get(slug=ROLE_SCHOOL_ADMIN),
        )
        self.client.force_authenticate(admin)
        response = self.client.post(
            reverse("v1:successful-student-list"),
            {"academic_year": "last year", "full_name": "Fahim Rahman"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)


class AdministrationOfficeTests(APITestCase):
    """Two seats, two independent tenures."""

    def test_recording_a_vice_principal_does_not_stand_down_the_principal(self):
        principal = Principal.objects.create(full_name="Md. Abdul Karim", office=Principal.Office.PRINCIPAL)
        Principal.objects.create(full_name="Salma Begum", office=Principal.Office.VICE_PRINCIPAL)

        principal.refresh_from_db()
        self.assertTrue(principal.is_current)

    def test_a_new_principal_stands_down_the_previous_one(self):
        outgoing = Principal.objects.create(full_name="Outgoing Head", office=Principal.Office.PRINCIPAL)
        Principal.objects.create(full_name="Incoming Head", office=Principal.Office.PRINCIPAL)

        outgoing.refresh_from_db()
        self.assertFalse(outgoing.is_current)

    def test_current_resolves_per_office(self):
        Principal.objects.create(full_name="Md. Abdul Karim", office=Principal.Office.PRINCIPAL)
        Principal.objects.create(full_name="Salma Begum", office=Principal.Office.VICE_PRINCIPAL)

        self.assertEqual(Principal.current().full_name, "Md. Abdul Karim")
        self.assertEqual(
            Principal.current(Principal.Office.VICE_PRINCIPAL).full_name, "Salma Begum"
        )
