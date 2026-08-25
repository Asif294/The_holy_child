from decimal import Decimal

from django.db import models

from apps.common.models import BaseModel


class ExamType(BaseModel):
    """A recurring assessment type — First Terminal, Half Yearly, Annual, …"""

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    weight = models.PositiveSmallIntegerField(
        default=100, help_text="Contribution to the final grade, as a percentage."
    )
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "exam_types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Exam(BaseModel):
    """A scheduled examination for a session."""

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        ONGOING = "ongoing", "Ongoing"
        COMPLETED = "completed", "Completed"
        PUBLISHED = "published", "Results published"
        CANCELLED = "cancelled", "Cancelled"

    name = models.CharField(max_length=150)
    exam_type = models.ForeignKey(ExamType, on_delete=models.SET_NULL, related_name="exams", null=True, blank=True)
    session = models.ForeignKey(
        "classes.AcademicSession", on_delete=models.CASCADE, related_name="exams"
    )
    start_date = models.DateField(db_index=True)
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED, db_index=True)
    instructions = models.TextField(blank=True, default="")

    class Meta:
        db_table = "exams"
        ordering = ["-start_date"]

    def __str__(self):
        return self.name

    @property
    def is_upcoming(self) -> bool:
        from django.utils import timezone

        return self.start_date >= timezone.localdate() and self.status in {
            self.Status.PLANNED,
            self.Status.ONGOING,
        }


class ExamSchedule(BaseModel):
    """One paper: a class sitting a subject at a specific time."""

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="schedules")
    school_class = models.ForeignKey("classes.SchoolClass", on_delete=models.CASCADE, related_name="exam_schedules")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="exam_schedules")
    exam_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=30, blank=True, default="")
    full_marks = models.PositiveSmallIntegerField(default=100)
    pass_marks = models.PositiveSmallIntegerField(default=33)

    class Meta:
        db_table = "exam_schedules"
        ordering = ["exam_date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["exam", "school_class", "subject"], name="unique_paper_per_exam_class_subject"
            )
        ]

    def __str__(self):
        return f"{self.exam.name} · {self.school_class.name} · {self.subject.name}"


class Result(BaseModel):
    """A student's marks for one paper."""

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="results")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="results")
    subject = models.ForeignKey("subjects.Subject", on_delete=models.CASCADE, related_name="results")
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    full_marks = models.PositiveSmallIntegerField(default=100)
    grade = models.CharField(max_length=5, blank=True, default="")
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("0.00"))
    is_absent = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False, db_index=True)
    remarks = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "results"
        ordering = ["-exam__start_date", "student__roll_number"]
        constraints = [
            models.UniqueConstraint(fields=["exam", "student", "subject"], name="unique_result_per_paper")
        ]

    def __str__(self):
        return f"{self.student.full_name} · {self.subject.name} · {self.marks_obtained}"

    # Bangladesh national grading scale.
    GRADE_SCALE = (
        (80, "A+", Decimal("5.00")),
        (70, "A", Decimal("4.00")),
        (60, "A-", Decimal("3.50")),
        (50, "B", Decimal("3.00")),
        (40, "C", Decimal("2.00")),
        (33, "D", Decimal("1.00")),
        (0, "F", Decimal("0.00")),
    )

    @property
    def percentage(self) -> Decimal:
        if not self.full_marks:
            return Decimal("0.00")
        return round((self.marks_obtained / self.full_marks) * 100, 2)

    def compute_grade(self) -> tuple[str, Decimal]:
        if self.is_absent:
            return "F", Decimal("0.00")
        percentage = self.percentage
        for threshold, grade, point in self.GRADE_SCALE:
            if percentage >= threshold:
                return grade, point
        return "F", Decimal("0.00")

    def save(self, *args, **kwargs):
        self.grade, self.grade_point = self.compute_grade()
        super().save(*args, **kwargs)
