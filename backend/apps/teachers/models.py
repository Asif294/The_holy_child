from django.db import models

from apps.common.models import BaseModel


class Department(BaseModel):
    """A teaching department, e.g. Science or Languages."""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    head = models.ForeignKey(
        "teachers.Teacher", on_delete=models.SET_NULL, related_name="heading_departments", null=True, blank=True
    )
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "departments"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Designation(BaseModel):
    """A staff job title, e.g. Assistant Teacher or Senior Teacher."""

    name = models.CharField(max_length=100, unique=True)
    rank = models.PositiveSmallIntegerField(default=0, help_text="Seniority order — lower is more senior.")
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "designations"
        ordering = ["rank", "name"]

    def __str__(self):
        return self.name


class Teacher(BaseModel):
    """
    A member of the teaching staff.

    The employment record is separate from the login account so that a teacher
    can exist in the register before (or without) being given system access.
    """

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full time"
        PART_TIME = "part_time", "Part time"
        CONTRACT = "contract", "Contract"
        GUEST = "guest", "Guest"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ON_LEAVE = "on_leave", "On leave"
        SUSPENDED = "suspended", "Suspended"
        RESIGNED = "resigned", "Resigned"
        RETIRED = "retired", "Retired"

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="teacher_profile",
        null=True,
        blank=True,
        help_text="Linked login account, if this teacher uses the system.",
    )
    employee_id = models.CharField(max_length=30, unique=True, db_index=True, help_text='e.g. "THC-T-0007"')
    full_name = models.CharField(max_length=150)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    photo = models.ImageField(upload_to="teachers/", null=True, blank=True)

    designation = models.ForeignKey(
        Designation, on_delete=models.SET_NULL, related_name="teachers", null=True, blank=True
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, related_name="teachers", null=True, blank=True
    )
    subjects = models.ManyToManyField(
        "subjects.Subject", related_name="teachers", blank=True, db_table="teacher_subjects"
    )

    employment_type = models.CharField(
        max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    joining_date = models.DateField(null=True, blank=True)
    resignation_date = models.DateField(null=True, blank=True)

    qualification = models.CharField(max_length=255, blank=True, default="", help_text='e.g. "M.Sc. in Mathematics"')
    specialization = models.CharField(max_length=150, blank=True, default="")
    experience_years = models.PositiveSmallIntegerField(default=0)

    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True, default="")
    blood_group = models.CharField(max_length=5, blank=True, default="")
    national_id = models.CharField(max_length=30, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "teachers"
        ordering = ["designation__rank", "full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.employee_id})"

    @property
    def is_class_teacher(self) -> bool:
        return self.class_teacher_of.exists()
