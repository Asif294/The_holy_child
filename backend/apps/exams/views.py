from django.db.models import Avg, Count
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.schema import DETAIL_WRITE_RESPONSES, PROTECTED_RESPONSES, crud_schema
from apps.common.viewsets import RBACModelViewSet
from apps.exams.models import Exam, ExamSchedule, ExamType, Result
from apps.exams.serializers import (
    ExamScheduleSerializer,
    ExamSerializer,
    ExamTypeSerializer,
    ResultSerializer,
)


@crud_schema(tag="Exams", resource="exam type", plural="exam types", serializer=ExamTypeSerializer)
class ExamTypeViewSet(RBACModelViewSet):
    """Recurring assessment types — First Terminal, Half Yearly, Annual."""

    permission_module = "exam"
    serializer_class = ExamTypeSerializer
    queryset = ExamType.objects.filter(is_deleted=False)
    search_fields = ["name", "code"]
    ordering_fields = ["name"]
    filterset_fields = ["is_active"]


@crud_schema(tag="Exams", resource="exam", serializer=ExamSerializer)
class ExamViewSet(RBACModelViewSet):
    """Scheduled examinations for a session."""

    permission_module = "exam"
    permission_map = {"upcoming": "exam.view"}
    serializer_class = ExamSerializer
    search_fields = ["name", "instructions"]
    ordering_fields = ["start_date", "name", "created_at"]
    ordering = ["-start_date"]
    filterset_fields = ["session", "exam_type", "status", "is_active"]

    def get_queryset(self):
        return Exam.objects.filter(is_deleted=False).select_related("exam_type", "session")

    @extend_schema(
        tags=["Exams"],
        summary="Upcoming exams",
        description="Exams starting today or later that are still planned or ongoing.",
        parameters=[OpenApiParameter("limit", int, description="How many to return (default 5, max 20).")],
        responses={200: ExamSerializer(many=True), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="upcoming")
    def upcoming(self, request):
        limit = min(int(request.query_params.get("limit", 5)), 20)
        queryset = self.get_queryset().filter(
            start_date__gte=timezone.localdate(),
            status__in=[Exam.Status.PLANNED, Exam.Status.ONGOING],
        ).order_by("start_date")[:limit]
        return Response(self.get_serializer(queryset, many=True).data)


@crud_schema(tag="Exams", resource="exam schedule", plural="exam schedules", serializer=ExamScheduleSerializer)
class ExamScheduleViewSet(RBACModelViewSet):
    """Individual papers: a class sitting a subject at a specific time."""

    permission_module = "exam"
    serializer_class = ExamScheduleSerializer
    search_fields = ["exam__name", "subject__name", "school_class__name", "room"]
    ordering_fields = ["exam_date", "start_time"]
    ordering = ["exam_date", "start_time"]
    filterset_fields = ["exam", "school_class", "subject", "exam_date", "is_active"]

    def get_queryset(self):
        return ExamSchedule.objects.filter(is_deleted=False).select_related("exam", "school_class", "subject")


@crud_schema(
    tag="Exams",
    resource="result",
    serializer=ResultSerializer,
    descriptions={
        "create": (
            "Records a student's marks for one paper. The grade and grade point are "
            "derived from the marks using the national grading scale — they are never "
            "accepted from the client. Requires the `result.create` permission."
        ),
    },
)
class ResultViewSet(RBACModelViewSet):
    """Marks recorded against exam papers."""

    permission_module = "result"
    permission_map = {"publish": "result.publish", "student_summary": "result.view"}
    serializer_class = ResultSerializer
    search_fields = ["student__full_name", "student__student_id", "subject__name", "exam__name"]
    ordering_fields = ["marks_obtained", "created_at"]
    filterset_fields = ["exam", "student", "subject", "is_published", "is_absent", "is_active"]

    def get_queryset(self):
        return Result.objects.filter(is_deleted=False).select_related("exam", "student", "subject")

    @extend_schema(
        tags=["Exams"],
        summary="Publish an exam's results",
        description=(
            "Marks every result for the given exam as published and moves the exam to "
            "`published`. Requires the `result.publish` permission, which is deliberately "
            "separate from `result.update` so teachers can enter marks without releasing them."
        ),
        request={"application/json": {"type": "object", "properties": {"exam": {"type": "integer"}},
                                      "required": ["exam"]}},
        responses={200: OpenApiResponse(description="Number of results published."), **DETAIL_WRITE_RESPONSES},
    )
    @action(detail=False, methods=["post"], url_path="publish")
    def publish(self, request):
        exam_id = request.data.get("exam")
        if not exam_id:
            return Response(
                {"success": False, "message": "The `exam` field is required.", "code": "BAD_REQUEST",
                 "errors": {"exam": ["This field is required."]}},
                status=400,
            )
        published = self.get_queryset().filter(exam_id=exam_id).update(is_published=True)
        Exam.objects.filter(pk=exam_id).update(status=Exam.Status.PUBLISHED)
        return Response({"success": True, "message": f"{published} result(s) published.", "published": published})

    @extend_schema(
        tags=["Exams"],
        summary="A student's result summary for an exam",
        description="Per-subject marks plus the aggregate GPA for one student in one exam.",
        parameters=[
            OpenApiParameter("student", int, required=True, description="Student primary key."),
            OpenApiParameter("exam", int, required=True, description="Exam primary key."),
        ],
        responses={200: OpenApiResponse(description="Marks and GPA."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="student-summary")
    def student_summary(self, request):
        student_id = request.query_params.get("student")
        exam_id = request.query_params.get("exam")
        if not student_id or not exam_id:
            return Response(
                {"success": False, "message": "Both `student` and `exam` query parameters are required.",
                 "code": "BAD_REQUEST", "errors": {}},
                status=400,
            )

        queryset = self.get_queryset().filter(student_id=student_id, exam_id=exam_id)
        aggregate = queryset.aggregate(gpa=Avg("grade_point"), subjects=Count("id"))
        failed = queryset.filter(grade="F").count()
        return Response(
            {
                "student": int(student_id),
                "exam": int(exam_id),
                "subjects": aggregate["subjects"],
                "gpa": round(float(aggregate["gpa"] or 0), 2) if not failed else 0.0,
                "failed_subjects": failed,
                "passed": failed == 0 and aggregate["subjects"] > 0,
                "results": self.get_serializer(queryset, many=True).data,
            }
        )
