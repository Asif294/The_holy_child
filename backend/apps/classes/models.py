from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import BaseModel


class AcademicSession(BaseModel):
    """A school year, e.g. "2026". Exactly one session is marked current."""

    name = models.CharField(max_length=30, unique=True, help_text='e.g. "2026"')
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "academic_sessions"
        ordering = ["-start_date"]
        verbose_name = "Academic session"

    def __str__(self):
        return self.name

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({"end_date": "The session end date must fall after its start date."})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            AcademicSession.objects.exclude(pk=self.pk).filter(is_current=True).update(is_current=False)

    @classmethod
    def current(cls):
        return cls.active_objects.filter(is_current=True).first()


class SchoolClass(BaseModel):
    """
    A grade level offered by the school — Play Group through Class 10.

    ``order`` drives sorting so "Class 10" never lands between "Class 1" and
    "Class 2" the way alphabetic sorting would.
    """

    name = models.CharField(max_length=50, unique=True, help_text='e.g. "Class 6" or "Play Group"')
    name_bn = models.CharField(max_length=50, blank=True, default="", help_text="Bangla label, e.g. ৬ষ্ঠ শ্রেণি")
    code = models.CharField(max_length=20, unique=True, help_text='Short code, e.g. "C6" or "PG"')
    order = models.PositiveSmallIntegerField(default=0, db_index=True, help_text="Sort position, lowest first.")
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "school_classes"
        ordering = ["order", "name"]
        verbose_name = "Class"
        verbose_name_plural = "Classes"

    def __str__(self):
        return self.name

    @property
    def student_count(self) -> int:
        return self.students.filter(is_deleted=False, is_active=True).count()


class Section(BaseModel):
    """A branch of a class, e.g. Class 6 — Section A."""

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=20, help_text='e.g. "A"')
    capacity = models.PositiveSmallIntegerField(default=40)
    room_number = models.CharField(max_length=20, blank=True, default="")
    class_teacher = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        related_name="class_teacher_of",
        null=True,
        blank=True,
        help_text="The teacher responsible for this section.",
    )

    class Meta:
        db_table = "sections"
        ordering = ["school_class__order", "name"]
        constraints = [
            models.UniqueConstraint(fields=["school_class", "name"], name="unique_section_per_class")
        ]

    def __str__(self):
        return f"{self.school_class.name} — {self.name}"

    @property
    def display_name(self) -> str:
        return f"{self.school_class.name} ({self.name})"

    @property
    def enrolled_count(self) -> int:
        return self.students.filter(is_deleted=False, is_active=True).count()

    @property
    def seats_available(self) -> int:
        return max(self.capacity - self.enrolled_count, 0)
