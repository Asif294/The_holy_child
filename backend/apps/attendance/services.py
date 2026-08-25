"""Attendance operations that are worth keeping out of the view layer."""
from datetime import date as date_type

from django.db import transaction
from django.db.models import Count, Q

from apps.attendance.models import AttendanceStatus, StudentAttendance
from apps.students.models import Student


@transaction.atomic
def record_bulk_attendance(*, date: date_type, entries: list[dict], section_id=None, marked_by=None) -> dict:
    """
    Upsert a day's register in one pass.

    Returns a summary of what changed so the client can confirm the save without
    re-fetching the whole register.
    """
    student_ids = [entry["student"] for entry in entries]
    students = {
        student.id: student
        for student in Student.objects.filter(id__in=student_ids, is_deleted=False).select_related("section")
    }

    missing = sorted(set(student_ids) - set(students))
    existing = {
        record.student_id: record
        for record in StudentAttendance.objects.filter(student_id__in=students, date=date)
    }

    created = updated = 0
    for entry in entries:
        student = students.get(entry["student"])
        if student is None:
            continue

        values = {
            "status": entry["status"],
            "check_in_time": entry.get("check_in_time"),
            "remarks": entry.get("remarks", ""),
            "section_id": section_id or student.section_id,
            "marked_by": marked_by,
        }

        record = existing.get(student.id)
        if record is None:
            StudentAttendance.objects.create(student=student, date=date, **values)
            created += 1
        else:
            for field, value in values.items():
                setattr(record, field, value)
            record.save()
            updated += 1

    return {"created": created, "updated": updated, "skipped_student_ids": missing}


def attendance_summary(queryset) -> dict:
    """Counts and an attendance rate for any ``StudentAttendance`` queryset."""
    aggregate = queryset.aggregate(
        total=Count("id"),
        present=Count("id", filter=Q(status=AttendanceStatus.PRESENT)),
        absent=Count("id", filter=Q(status=AttendanceStatus.ABSENT)),
        late=Count("id", filter=Q(status=AttendanceStatus.LATE)),
        leave=Count("id", filter=Q(status=AttendanceStatus.LEAVE)),
    )
    counted = aggregate["total"] - queryset.filter(status=AttendanceStatus.HOLIDAY).count()
    attending = aggregate["present"] + aggregate["late"]
    aggregate["attendance_rate"] = round((attending / counted) * 100, 2) if counted else 0.0
    return aggregate
