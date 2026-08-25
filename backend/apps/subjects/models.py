from django.db import models

from apps.common.models import BaseModel


class Subject(BaseModel):
    """A subject in the school's catalogue."""

    class Category(models.TextChoices):
        COMPULSORY = "compulsory", "Compulsory"
        OPTIONAL = "optional", "Optional"
        EXTRA = "extra", "Extra-curricular"

    name = models.CharField(max_length=100)
    name_bn = models.CharField(max_length=100, blank=True, default="")
    code = models.CharField(max_length=20, unique=True, help_text='e.g. "MATH-101"')
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.COMPULSORY)
    full_marks = models.PositiveSmallIntegerField(default=100)
    pass_marks = models.PositiveSmallIntegerField(default=33)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "subjects"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class ClassSubject(BaseModel):
    """
    Assigns a subject to a class and (optionally) names the teacher who takes it.

    Keeping this as its own table means the same subject can be taught in several
    classes by different teachers without duplicating the subject record.
    """

    school_class = models.ForeignKey("classes.SchoolClass", on_delete=models.CASCADE, related_name="class_subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="class_subjects")
    teacher = models.ForeignKey(
        "teachers.Teacher", on_delete=models.SET_NULL, related_name="teaching_subjects", null=True, blank=True
    )
    weekly_periods = models.PositiveSmallIntegerField(default=5)

    class Meta:
        db_table = "class_subjects"
        ordering = ["school_class__order", "subject__name"]
        constraints = [
            models.UniqueConstraint(fields=["school_class", "subject"], name="unique_subject_per_class")
        ]

    def __str__(self):
        return f"{self.school_class.name} · {self.subject.name}"
