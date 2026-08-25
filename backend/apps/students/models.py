from django.db import models

from apps.common.models import BaseModel


class Guardian(BaseModel):
    """A parent or guardian. Shared across siblings rather than duplicated."""

    class Relation(models.TextChoices):
        FATHER = "father", "Father"
        MOTHER = "mother", "Mother"
        BROTHER = "brother", "Brother"
        SISTER = "sister", "Sister"
        UNCLE = "uncle", "Uncle"
        AUNT = "aunt", "Aunt"
        OTHER = "other", "Other"

    user = models.OneToOneField(
        "accounts.User", on_delete=models.SET_NULL, related_name="guardian_profile", null=True, blank=True
    )
    full_name = models.CharField(max_length=150)
    relation = models.CharField(max_length=20, choices=Relation.choices, default=Relation.FATHER)
    phone = models.CharField(max_length=20, db_index=True)
    alternate_phone = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    occupation = models.CharField(max_length=100, blank=True, default="")
    national_id = models.CharField(max_length=30, blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "guardians"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.get_relation_display()})"


class Student(BaseModel):
    """
    An enrolled student.

    As with teachers, the enrolment record is independent of the login account —
    younger pupils never sign in, but they still need a record.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        GRADUATED = "graduated", "Graduated"
        TRANSFERRED = "transferred", "Transferred"
        DROPPED = "dropped", "Dropped out"
        SUSPENDED = "suspended", "Suspended"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    user = models.OneToOneField(
        "accounts.User", on_delete=models.SET_NULL, related_name="student_profile", null=True, blank=True
    )
    student_id = models.CharField(max_length=30, unique=True, db_index=True, help_text='e.g. "THC-2026-0142"')
    admission_number = models.CharField(max_length=30, unique=True, db_index=True)
    roll_number = models.PositiveIntegerField(null=True, blank=True, help_text="Roll within the section.")

    full_name = models.CharField(max_length=150, db_index=True)
    full_name_bn = models.CharField(max_length=150, blank=True, default="")
    photo = models.ImageField(upload_to="students/", null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, default="")
    blood_group = models.CharField(max_length=5, blank=True, default="")
    birth_certificate_no = models.CharField(max_length=40, blank=True, default="")
    religion = models.CharField(max_length=40, blank=True, default="")

    school_class = models.ForeignKey(
        "classes.SchoolClass", on_delete=models.PROTECT, related_name="students", null=True, blank=True
    )
    section = models.ForeignKey(
        "classes.Section", on_delete=models.SET_NULL, related_name="students", null=True, blank=True
    )
    session = models.ForeignKey(
        "classes.AcademicSession", on_delete=models.SET_NULL, related_name="students", null=True, blank=True
    )

    guardian = models.ForeignKey(
        Guardian, on_delete=models.SET_NULL, related_name="students", null=True, blank=True
    )
    father_name = models.CharField(max_length=150, blank=True, default="")
    mother_name = models.CharField(max_length=150, blank=True, default="")
    emergency_contact = models.CharField(max_length=20, blank=True, default="")

    admission_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    present_address = models.CharField(max_length=255, blank=True, default="")
    permanent_address = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "students"
        ordering = ["school_class__order", "section__name", "roll_number", "full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["section", "roll_number"],
                condition=models.Q(roll_number__isnull=False, is_deleted=False),
                name="unique_roll_per_section",
            )
        ]

    def __str__(self):
        return f"{self.full_name} ({self.student_id})"

    @property
    def class_name(self) -> str | None:
        return self.school_class.name if self.school_class_id else None
