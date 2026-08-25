from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.attendance.models import StudentAttendance, TeacherAttendance
from apps.attendance.serializers import (
    BulkAttendanceSerializer,
    StudentAttendanceSerializer,
    TeacherAttendanceSerializer,
)
from apps.attendance.services import attendance_summary, record_bulk_attendance
from apps.common.schema import PROTECTED_RESPONSES, WRITE_RESPONSES, crud_schema
from apps.common.viewsets import RBACModelViewSet


@crud_schema(
    tag="Attendance",
    resource="attendance record",
    plural="attendance records",
    serializer=StudentAttendanceSerializer,
    descriptions={
        "list": (
            "Attendance marks, filterable by `student`, `section`, `status` and `date`. "
            "Use `date_from` / `date_to` for a range. Requires the `attendance.view` permission."
        ),
    },
)
class StudentAttendanceViewSet(RBACModelViewSet):
    """
    Daily student attendance.

    A single mark per student per day is enforced at the database level, so a
    re-submitted register updates rather than duplicating.
    """

    permission_module = "attendance"
    permission_map = {"bulk": "attendance.create", "summary": "attendance.view", "register": "attendance.view"}
    serializer_class = StudentAttendanceSerializer
    search_fields = ["student__full_name", "student__student_id"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-date"]
    filterset_fields = ["student", "section", "status", "date", "is_active"]

    def get_queryset(self):
        queryset = (
            StudentAttendance.objects.filter(is_deleted=False)
            .select_related("student", "section__school_class", "marked_by")
        )
        params = self.request.query_params
        if params.get("date_from"):
            queryset = queryset.filter(date__gte=params["date_from"])
        if params.get("date_to"):
            queryset = queryset.filter(date__lte=params["date_to"])
        if params.get("school_class"):
            queryset = queryset.filter(student__school_class_id=params["school_class"])
        return queryset

    @extend_schema(
        tags=["Attendance"],
        summary="Submit a register in bulk",
        description=(
            "Records or corrects a whole section's attendance for one date in a single "
            "request. Existing marks for that date are updated in place, which makes the "
            "call safe to retry. Requires the `attendance.create` permission."
        ),
        request=BulkAttendanceSerializer,
        responses={
            200: OpenApiResponse(description="Summary of created and updated marks."),
            **WRITE_RESPONSES,
        },
        examples=[
            OpenApiExample(
                "Daily register",
                value={
                    "date": "2026-08-25",
                    "section": 3,
                    "entries": [
                        {"student": 11, "status": "present"},
                        {"student": 12, "status": "absent", "remarks": "Informed by guardian"},
                        {"student": 13, "status": "late", "check_in_time": "09:20:00"},
                    ],
                },
                request_only=True,
            )
        ],
    )
    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk(self, request):
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = record_bulk_attendance(
            date=serializer.validated_data["date"],
            entries=serializer.validated_data["entries"],
            section_id=serializer.validated_data.get("section"),
            marked_by=request.user,
        )
        return Response({"success": True, "message": "Attendance saved.", **result})

    @extend_schema(
        tags=["Attendance"],
        summary="Attendance summary",
        description=(
            "Present / absent / late / leave counts plus an attendance rate for the "
            "filtered set. Defaults to today when no date filter is supplied."
        ),
        parameters=[
            OpenApiParameter("date", str, description="Single date (YYYY-MM-DD)."),
            OpenApiParameter("date_from", str, description="Range start (YYYY-MM-DD)."),
            OpenApiParameter("date_to", str, description="Range end (YYYY-MM-DD)."),
            OpenApiParameter("section", int, description="Restrict to one section."),
        ],
        responses={200: OpenApiResponse(description="Attendance counts and rate."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        params = request.query_params
        queryset = self.get_queryset()
        if not any(params.get(key) for key in ("date", "date_from", "date_to")):
            queryset = queryset.filter(date=timezone.localdate())
        queryset = self.filter_queryset(queryset)
        return Response(attendance_summary(queryset))

    @extend_schema(
        tags=["Attendance"],
        summary="Register for a section on a date",
        description=(
            "Returns every active student in the section alongside their mark for the "
            "given date (`null` when not yet marked) — exactly what the register screen "
            "needs to render in one request."
        ),
        parameters=[
            OpenApiParameter("section", int, required=True, description="Section primary key."),
            OpenApiParameter("date", str, description="Defaults to today."),
        ],
        responses={200: OpenApiResponse(description="Roster with attendance marks."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="register")
    def register(self, request):
        from apps.students.models import Student

        section_id = request.query_params.get("section")
        if not section_id:
            return Response(
                {"success": False, "message": "The `section` query parameter is required.",
                 "code": "BAD_REQUEST", "errors": {"section": ["This query parameter is required."]}},
                status=400,
            )

        date = request.query_params.get("date") or timezone.localdate()
        students = Student.objects.filter(
            section_id=section_id, is_deleted=False, status=Student.Status.ACTIVE
        ).order_by("roll_number", "full_name")
        marks = {
            record.student_id: record
            for record in StudentAttendance.objects.filter(student__in=students, date=date)
        }

        return Response(
            {
                "date": str(date),
                "section": int(section_id),
                "students": [
                    {
                        "student": student.id,
                        "student_id": student.student_id,
                        "roll_number": student.roll_number,
                        "full_name": student.full_name,
                        "status": marks[student.id].status if student.id in marks else None,
                        "remarks": marks[student.id].remarks if student.id in marks else "",
                        "attendance_id": marks[student.id].id if student.id in marks else None,
                    }
                    for student in students
                ],
            }
        )


@crud_schema(
    tag="Attendance",
    resource="staff attendance record",
    plural="staff attendance records",
    serializer=TeacherAttendanceSerializer,
)
class TeacherAttendanceViewSet(RBACModelViewSet):
    """Daily staff attendance, kept separate from the student register."""

    permission_module = "attendance"
    serializer_class = TeacherAttendanceSerializer
    search_fields = ["teacher__full_name", "teacher__employee_id"]
    ordering_fields = ["date", "created_at"]
    ordering = ["-date"]
    filterset_fields = ["teacher", "status", "date", "is_active"]

    def get_queryset(self):
        return TeacherAttendance.objects.filter(is_deleted=False).select_related("teacher", "marked_by")
