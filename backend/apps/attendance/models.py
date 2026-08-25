from django.db import models

from apps.common.models import BaseModel


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Present"
    ABSENT = "absent", "Absent"
    LATE = "late", "Late"
    LEAVE = "leave", "On leave"
    HOLIDAY = "holiday", "Holiday"


class StudentAttendance(BaseModel):
    """
    One attendance mark for one student on one date.

    The unique constraint on ``(student, date)`` is what makes a re-submitted
    register idempotent instead of double-counting.
    """

    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="attendance_records")
    section = models.ForeignKey(
        "classes.Section", on_delete=models.SET_NULL, related_name="attendance_records", null=True, blank=True
    )
    date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT, db_index=True
    )
    check_in_time = models.TimeField(null=True, blank=True)
    remarks = models.CharField(max_length=255, blank=True, default="")
    marked_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, related_name="marked_attendance", null=True, blank=True
    )

    class Meta:
        db_table = "student_attendance"
        ordering = ["-date", "student__roll_number"]
        constraints = [
            models.UniqueConstraint(fields=["student", "date"], name="unique_attendance_per_student_per_day")
        ]
        indexes = [models.Index(fields=["date", "status"])]

    def __str__(self):
        return f"{self.student.full_name} · {self.date} · {self.get_status_display()}"

    @property
    def is_present(self) -> bool:
        return self.status in {AttendanceStatus.PRESENT, AttendanceStatus.LATE}


class TeacherAttendance(BaseModel):
    """Daily staff attendance, kept separate so student reports stay clean."""

    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField(db_index=True)
    status = models.CharField(
        max_length=20, choices=AttendanceStatus.choices, default=AttendanceStatus.PRESENT, db_index=True
    )
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    remarks = models.CharField(max_length=255, blank=True, default="")
    marked_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, related_name="marked_teacher_attendance", null=True, blank=True
    )

    class Meta:
        db_table = "teacher_attendance"
        ordering = ["-date", "teacher__full_name"]
        constraints = [
            models.UniqueConstraint(fields=["teacher", "date"], name="unique_attendance_per_teacher_per_day")
        ]

    def __str__(self):
        return f"{self.teacher.full_name} · {self.date} · {self.get_status_display()}"
