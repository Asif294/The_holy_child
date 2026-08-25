"""Cross-module aggregation for the dashboard. Read-only by design."""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.attendance.models import AttendanceStatus, StudentAttendance
from apps.classes.models import SchoolClass
from apps.exams.models import Exam
from apps.fees.models import Invoice, Payment
from apps.principal.models import ApprovalRequest
from apps.students.models import Student
from apps.subjects.models import Subject
from apps.teachers.models import Teacher


def _attendance_rate(queryset) -> float:
    counted = queryset.exclude(status=AttendanceStatus.HOLIDAY).count()
    if not counted:
        return 0.0
    attending = queryset.filter(status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE]).count()
    return round((attending / counted) * 100, 2)


def dashboard_summary() -> dict:
    """The headline numbers rendered as cards at the top of the dashboard."""
    today = timezone.localdate()
    todays_attendance = StudentAttendance.objects.filter(is_deleted=False, date=today)

    invoices = Invoice.objects.filter(is_deleted=False).exclude(
        status__in=[Invoice.Status.CANCELLED, Invoice.Status.WAIVED]
    )
    billed = invoices.aggregate(amount=Sum("amount"), discount=Sum("discount"), fine=Sum("fine"))
    total_billed = (
        (billed["amount"] or Decimal("0")) - (billed["discount"] or Decimal("0")) + (billed["fine"] or Decimal("0"))
    )
    collected = Payment.objects.filter(is_deleted=False).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    return {
        "total_students": Student.objects.filter(is_deleted=False, status=Student.Status.ACTIVE).count(),
        "total_teachers": Teacher.objects.filter(is_deleted=False, status=Teacher.Status.ACTIVE).count(),
        "total_classes": SchoolClass.objects.filter(is_deleted=False, is_active=True).count(),
        "total_subjects": Subject.objects.filter(is_deleted=False, is_active=True).count(),
        "todays_attendance_rate": _attendance_rate(todays_attendance),
        "todays_present": todays_attendance.filter(
            status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE]
        ).count(),
        "todays_absent": todays_attendance.filter(status=AttendanceStatus.ABSENT).count(),
        "pending_fees": max(total_billed - collected, Decimal("0.00")),
        "collected_fees": collected,
        "upcoming_exams": Exam.objects.filter(
            is_deleted=False,
            start_date__gte=today,
            status__in=[Exam.Status.PLANNED, Exam.Status.ONGOING],
        ).count(),
        "pending_approvals": ApprovalRequest.objects.filter(
            is_deleted=False, status=ApprovalRequest.Status.PENDING
        ).count(),
    }


def attendance_trend(days: int = 7) -> list[dict]:
    """Daily attendance rate for the last ``days`` days, oldest first."""
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    records = StudentAttendance.objects.filter(is_deleted=False, date__gte=start, date__lte=today)

    by_date = {
        row["date"]: row
        for row in records.values("date").annotate(
            total=Count("id"),
            present=Count("id", filter=Q(status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE])),
            absent=Count("id", filter=Q(status=AttendanceStatus.ABSENT)),
        )
    }

    trend = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = by_date.get(day, {"total": 0, "present": 0, "absent": 0})
        trend.append(
            {
                "date": day.isoformat(),
                "label": day.strftime("%a"),
                "present": row["present"],
                "absent": row["absent"],
                "rate": round((row["present"] / row["total"]) * 100, 2) if row["total"] else 0.0,
            }
        )
    return trend


def enrollment_by_class() -> list[dict]:
    """Student headcount per class, in curriculum order."""
    return [
        {
            "class_id": row["id"],
            "class_name": row["name"],
            "students": row["total"],
        }
        for row in SchoolClass.objects.filter(is_deleted=False, is_active=True)
        .annotate(total=Count("students", filter=Q(students__is_deleted=False, students__status=Student.Status.ACTIVE)))
        .order_by("order")
        .values("id", "name", "total")
    ]


def fee_collection_trend(months: int = 6) -> list[dict]:
    """Collected amount per month for the last ``months`` months, oldest first."""
    today = timezone.localdate()
    trend = []
    for offset in range(months - 1, -1, -1):
        month = (today.replace(day=1) - timedelta(days=offset * 30)).replace(day=1)
        collected = Payment.objects.filter(
            is_deleted=False, paid_at__year=month.year, paid_at__month=month.month
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")
        trend.append({"month": month.strftime("%b %Y"), "label": month.strftime("%b"), "collected": collected})
    return trend


def public_school_stats() -> dict:
    """The counts shown on the public landing page — no personal data."""
    return {
        "students": Student.objects.filter(is_deleted=False, status=Student.Status.ACTIVE).count(),
        "teachers": Teacher.objects.filter(is_deleted=False, status=Teacher.Status.ACTIVE).count(),
        "classes": SchoolClass.objects.filter(is_deleted=False, is_active=True).count(),
        "subjects": Subject.objects.filter(is_deleted=False, is_active=True).count(),
    }
