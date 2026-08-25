from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.schema import PROTECTED_RESPONSES, crud_schema
from apps.common.viewsets import RBACModelViewSet
from apps.teachers.models import Department, Designation, Teacher
from apps.teachers.serializers import (
    DepartmentSerializer,
    DesignationSerializer,
    TeacherListSerializer,
    TeacherPublicSerializer,
    TeacherSerializer,
)


@crud_schema(tag="Teachers", resource="designation", serializer=DesignationSerializer)
class DesignationViewSet(RBACModelViewSet):
    """Staff job titles, ordered by seniority."""

    permission_module = "teacher"
    serializer_class = DesignationSerializer
    queryset = Designation.objects.filter(is_deleted=False)
    search_fields = ["name"]
    ordering_fields = ["rank", "name"]
    ordering = ["rank", "name"]
    filterset_fields = ["is_active"]


@crud_schema(tag="Teachers", resource="department", serializer=DepartmentSerializer)
class DepartmentViewSet(RBACModelViewSet):
    """Teaching departments and their heads."""

    permission_module = "teacher"
    serializer_class = DepartmentSerializer
    search_fields = ["name", "code"]
    ordering_fields = ["name"]
    filterset_fields = ["is_active"]

    def get_queryset(self):
        return Department.objects.filter(is_deleted=False).select_related("head")


@crud_schema(
    tag="Teachers",
    resource="teacher",
    serializer=TeacherSerializer,
    descriptions={
        "list": (
            "Paginated staff directory. Filter by `department`, `designation`, `status` or "
            "`employment_type`, and search across name, employee ID, email and phone. "
            "Requires the `teacher.view` permission."
        ),
        "create": (
            "Adds a member of teaching staff to the register. The `user` link is optional — "
            "a teacher can be recorded before being granted system access. "
            "Requires the `teacher.create` permission."
        ),
    },
)
class TeacherViewSet(RBACModelViewSet):
    """
    The teaching staff register.

    Employment records are deliberately independent of login accounts, so the
    register can be complete before anyone is issued credentials.
    """

    permission_module = "teacher"
    permission_map = {"statistics": "teacher.view", "my_profile": "teacher.view"}
    serializer_class = TeacherSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    search_fields = ["full_name", "employee_id", "email", "phone", "specialization"]
    ordering_fields = ["full_name", "joining_date", "created_at"]
    ordering = ["full_name"]
    filterset_fields = ["department", "designation", "status", "employment_type", "gender", "is_active"]

    def get_queryset(self):
        return (
            Teacher.objects.filter(is_deleted=False)
            .select_related("designation", "department", "user")
            .prefetch_related("subjects", "class_teacher_of__school_class")
        )

    def get_serializer_class(self):
        return TeacherListSerializer if self.action == "list" else TeacherSerializer

    @extend_schema(
        tags=["Teachers"],
        summary="Teaching staff statistics",
        description="Headline counts for the staff dashboard: totals by status, department and employment type.",
        responses={
            200: OpenApiResponse(description="Aggregated staff counts."),
            **PROTECTED_RESPONSES,
        },
    )
    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        queryset = self.get_queryset()
        return Response(
            {
                "total": queryset.count(),
                "active": queryset.filter(status=Teacher.Status.ACTIVE).count(),
                "on_leave": queryset.filter(status=Teacher.Status.ON_LEAVE).count(),
                "by_department": list(
                    Department.objects.filter(is_deleted=False)
                    .annotate(total=Count("teachers", filter=Q(teachers__is_deleted=False)))
                    .values("id", "name", "total")
                ),
                "by_employment_type": list(
                    queryset.values("employment_type").annotate(total=Count("id")).order_by("-total")
                ),
            }
        )

    @extend_schema(
        tags=["Teachers"],
        summary="The signed-in teacher's own record",
        description=(
            "Returns the staff record linked to the caller's account, or `404` if the "
            "account is not linked to a teacher. Useful for a teacher's own dashboard."
        ),
        parameters=[OpenApiParameter("expand", str, description="Reserved for future expansion.")],
        responses={200: TeacherSerializer, **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="me")
    def my_profile(self, request):
        teacher = self.get_queryset().filter(user=request.user).first()
        if teacher is None:
            return Response(
                {
                    "success": False,
                    "message": "Your account is not linked to a teaching staff record.",
                    "code": "NOT_FOUND",
                    "errors": {},
                },
                status=404,
            )
        return Response(self.get_serializer(teacher).data)


@extend_schema(
    tags=["Public site"],
    summary="Public staff directory",
    description=(
        "Unauthenticated endpoint powering the *Teachers* section of the public "
        "site. Lists active teaching staff with the fields a visitor should see — "
        "photo, name, designation, department, subjects and qualification. "
        "Personal contact details are never included.\n\n"
        "Adding, editing and deleting teachers stays behind the `teacher.*` "
        "permission codes on `/api/v1/teachers/`."
    ),
    parameters=[
        OpenApiParameter("department", int, description="Filter to one department."),
        OpenApiParameter("search", str, description="Match against name, designation or specialisation."),
    ],
    responses={200: TeacherPublicSerializer(many=True)},
)
class PublicTeacherAPIView(APIView):
    """Read-only public directory of the teaching staff."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        queryset = (
            Teacher.objects.filter(is_deleted=False, is_active=True, status=Teacher.Status.ACTIVE)
            .select_related("designation", "department")
            .prefetch_related("subjects")
            .order_by("designation__rank", "full_name")
        )

        department = (request.query_params.get("department") or "").strip()
        if department.isdigit():
            queryset = queryset.filter(department_id=int(department))

        search = (request.query_params.get("search") or "").strip()
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search)
                | Q(designation__name__icontains=search)
                | Q(specialization__icontains=search)
            )

        return Response(TeacherPublicSerializer(queryset, many=True, context={"request": request}).data)
