from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.responses import error_response
from apps.common.schema import PROTECTED_RESPONSES, crud_schema
from apps.common.viewsets import RBACModelViewSet
from apps.students.models import Guardian, Student
from apps.students.serializers import GuardianSerializer, StudentListSerializer, StudentSerializer
from apps.students.services import identifier_clashes, next_enrolment_identifiers, next_roll_number


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
    permission_map = {
        "statistics": "student.view",
        "next_identifiers": "student.create",
        "check_identifiers": "student.view",
        "next_roll": "student.view",
    }
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
        summary="Next enrolment identifiers",
        description=(
            "The student ID and admission number the next admission will be given, so the "
            "form can show them before anything is saved. Both are suggestions rather than "
            "reservations: send different values and those are stored instead, and if two "
            "clerks are handed the same number, whichever record is saved second is issued "
            "the following one. Requires the `student.create` permission."
        ),
        responses={
            200: OpenApiResponse(description="`{student_id, admission_number}`."),
            **PROTECTED_RESPONSES,
        },
    )
    @action(detail=False, methods=["get"], url_path="next-identifiers")
    def next_identifiers(self, request):
        return Response(next_enrolment_identifiers())

    @extend_schema(
        tags=["Students"],
        summary="Are these enrolment codes free?",
        description=(
            "Answers whether a student ID or admission number is already taken, so the "
            "admission form can say so while it is being typed rather than after it is "
            "submitted. Pass either or both codes; pass `exclude` with a student's id when "
            "editing, so their own code does not read as a clash.\n\n"
            "Returns only the codes that clash, as `{field: message}` — an empty object "
            "means both are free. This is a courtesy check, not a reservation: the save "
            "itself is what enforces uniqueness. Requires the `student.view` permission."
        ),
        parameters=[
            OpenApiParameter("student_id", str, description="The student ID to test."),
            OpenApiParameter("admission_number", str, description="The admission number to test."),
            OpenApiParameter("exclude", int, description="A student id to ignore — their own code."),
        ],
        responses={200: OpenApiResponse(description="`{}` when free, else `{field: message}`."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="check-identifiers")
    def check_identifiers(self, request):
        exclude = request.query_params.get("exclude")
        return Response(
            identifier_clashes(
                request.query_params,
                exclude=int(exclude) if (exclude or "").isdigit() else None,
            )
        )

    @extend_schema(
        tags=["Students"],
        summary="Next free roll number in a section",
        description=(
            "The roll after the highest one in use in a section, so the admission form can "
            "fill it in once a class and section are chosen. Rolls are unique within a "
            "section, not school-wide, so a section is required. A pupil who has left frees "
            "their roll. Requires the `student.view` permission."
        ),
        parameters=[OpenApiParameter("section", int, description="The section to number within.", required=True)],
        responses={200: OpenApiResponse(description="`{roll_number}`."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="next-roll")
    def next_roll(self, request):
        section = request.query_params.get("section") or ""
        if not section.isdigit():
            return error_response("A section is required to work out the next roll number.")
        return Response({"roll_number": next_roll_number(int(section))})

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
