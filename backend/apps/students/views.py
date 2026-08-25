from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.schema import PROTECTED_RESPONSES, crud_schema
from apps.common.viewsets import RBACModelViewSet
from apps.students.models import Guardian, Student
from apps.students.serializers import GuardianSerializer, StudentListSerializer, StudentSerializer


@crud_schema(tag="Students", resource="guardian", serializer=GuardianSerializer)
class GuardianViewSet(RBACModelViewSet):
    """Parents and guardians, shared across siblings rather than duplicated."""

    permission_module = "student"
    serializer_class = GuardianSerializer
    queryset = Guardian.objects.filter(is_deleted=False)
    search_fields = ["full_name", "phone", "email", "national_id"]
    ordering_fields = ["full_name", "created_at"]
    filterset_fields = ["relation", "is_active"]


@crud_schema(
    tag="Students",
    resource="student",
    serializer=StudentSerializer,
    descriptions={
        "list": (
            "Paginated student directory. Filter by `school_class`, `section`, `session`, "
            "`status` or `gender`, and search by name, student ID or admission number. "
            "Requires the `student.view` permission."
        ),
        "destroy": (
            "Soft-deletes the enrolment so attendance, results and fee history stay intact. "
            "Requires the `student.delete` permission."
        ),
    },
)
class StudentViewSet(RBACModelViewSet):
    """The student register."""

    permission_module = "student"
    permission_map = {"statistics": "student.view"}
    serializer_class = StudentSerializer
    search_fields = ["full_name", "student_id", "admission_number", "father_name", "mother_name"]
    ordering_fields = ["full_name", "roll_number", "admission_date", "created_at"]
    filterset_fields = ["school_class", "section", "session", "status", "gender", "guardian", "is_active"]

    def get_queryset(self):
        return (
            Student.objects.filter(is_deleted=False)
            .select_related("school_class", "section", "session", "guardian", "user")
        )

    def get_serializer_class(self):
        return StudentListSerializer if self.action == "list" else StudentSerializer

    @extend_schema(
        tags=["Students"],
        summary="Student statistics",
        description="Totals by status, gender and class — the numbers behind the dashboard cards.",
        parameters=[OpenApiParameter("session", int, description="Restrict the counts to one academic session.")],
        responses={200: OpenApiResponse(description="Aggregated student counts."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        queryset = self.get_queryset()
        session = request.query_params.get("session")
        if session:
            queryset = queryset.filter(session_id=session)

        return Response(
            {
                "total": queryset.count(),
                "active": queryset.filter(status=Student.Status.ACTIVE).count(),
                "by_gender": list(queryset.values("gender").annotate(total=Count("id")).order_by("-total")),
                "by_status": list(queryset.values("status").annotate(total=Count("id")).order_by("-total")),
                "by_class": list(
                    queryset.filter(school_class__isnull=False)
                    .values("school_class__id", "school_class__name", "school_class__order")
                    .annotate(total=Count("id"))
                    .order_by("school_class__order")
                ),
                "male": queryset.filter(gender=Student.Gender.MALE).count(),
                "female": queryset.filter(gender=Student.Gender.FEMALE).count(),
                "new_this_session": queryset.filter(
                    Q(admission_date__isnull=False) & Q(session__is_current=True)
                ).count(),
            }
        )
