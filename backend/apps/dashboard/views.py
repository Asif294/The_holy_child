from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from apps.common.permissions import HasActionPermission
from apps.common.schema import PROTECTED_RESPONSES, crud_schema
from apps.common.viewsets import RBACModelViewSet
from apps.dashboard.models import ActivityLog, SchoolEvent, SchoolProfile
from apps.dashboard.serializers import (
    ActivityLogSerializer,
    DashboardSummarySerializer,
    SchoolEventSerializer,
    SchoolInfoSerializer,
    SchoolProfileSerializer,
)
from apps.dashboard.services import (
    attendance_trend,
    dashboard_summary,
    enrollment_by_class,
    fee_collection_trend,
    public_school_stats,
)
from apps.exams.models import Exam
from apps.exams.serializers import ExamSerializer
from apps.fees.models import Payment
from apps.fees.serializers import PaymentSerializer
from apps.principal.models import Notice
from apps.principal.serializers import NoticeSerializer


class DashboardViewSet(ViewSet):
    """
    Aggregated, read-only views over every module.

    Everything here is gated behind `dashboard.view`; the individual figures
    themselves are counts, never personal records, so one permission is enough.
    """

    permission_classes = [IsAuthenticated, HasActionPermission]
    permission_module = "dashboard"

    @extend_schema(
        tags=["Dashboard"],
        summary="Dashboard summary cards",
        description=(
            "The headline numbers for the dashboard: student, teacher, class and subject "
            "totals, today's attendance, fee collection and outstanding balance, upcoming "
            "exams and pending approvals. Requires the `dashboard.view` permission."
        ),
        responses={200: DashboardSummarySerializer, **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        return Response(dashboard_summary())

    @extend_schema(
        tags=["Dashboard"],
        summary="Attendance trend",
        description="Daily attendance rate for the last N days, oldest first — feeds the attendance chart.",
        parameters=[OpenApiParameter("days", int, description="Window size (default 7, max 90).")],
        responses={200: OpenApiResponse(description="One entry per day."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="attendance-trend")
    def attendance_trend(self, request):
        days = min(max(int(request.query_params.get("days", 7)), 1), 90)
        return Response(attendance_trend(days))

    @extend_schema(
        tags=["Dashboard"],
        summary="Enrolment by class",
        description="Student headcount per class in curriculum order — feeds the enrolment bar chart.",
        responses={200: OpenApiResponse(description="One entry per class."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="enrollment")
    def enrollment(self, request):
        return Response(enrollment_by_class())

    @extend_schema(
        tags=["Dashboard"],
        summary="Fee collection trend",
        description="Amount collected per month for the last N months, oldest first.",
        parameters=[OpenApiParameter("months", int, description="Window size (default 6, max 24).")],
        responses={200: OpenApiResponse(description="One entry per month."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="fee-trend")
    def fee_trend(self, request):
        months = min(max(int(request.query_params.get("months", 6)), 1), 24)
        return Response(fee_collection_trend(months))

    @extend_schema(
        tags=["Dashboard"],
        summary="Recent activity",
        description="The most recent audited actions across the platform.",
        parameters=[OpenApiParameter("limit", int, description="How many to return (default 10, max 50).")],
        responses={200: ActivityLogSerializer(many=True), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="activities")
    def activities(self, request):
        limit = min(int(request.query_params.get("limit", 10)), 50)
        queryset = ActivityLog.objects.filter(is_deleted=False).select_related("actor")[:limit]
        return Response(ActivityLogSerializer(queryset, many=True).data)

    @extend_schema(
        tags=["Dashboard"],
        summary="Everything the dashboard screen needs",
        description=(
            "One call that returns the summary cards, attendance trend, enrolment "
            "breakdown, upcoming events and exams, recent payments, notices and activity. "
            "Saves the dashboard eight round trips on load."
        ),
        responses={200: OpenApiResponse(description="Composite dashboard payload."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="overview")
    def overview(self, request):
        today = timezone.localdate()
        context = {"request": request}
        return Response(
            {
                "summary": dashboard_summary(),
                "attendance_trend": attendance_trend(7),
                "enrollment_by_class": enrollment_by_class(),
                "fee_trend": fee_collection_trend(6),
                "upcoming_events": SchoolEventSerializer(
                    SchoolEvent.objects.filter(is_deleted=False, start_date__gte=today).order_by("start_date")[:5],
                    many=True,
                ).data,
                "upcoming_exams": ExamSerializer(
                    Exam.objects.filter(
                        is_deleted=False,
                        start_date__gte=today,
                        status__in=[Exam.Status.PLANNED, Exam.Status.ONGOING],
                    ).order_by("start_date")[:5],
                    many=True,
                ).data,
                "recent_payments": PaymentSerializer(
                    Payment.objects.filter(is_deleted=False).select_related("invoice__student")[:5],
                    many=True,
                    context=context,
                ).data,
                "recent_notices": NoticeSerializer(
                    Notice.objects.filter(is_deleted=False, is_published=True)[:5], many=True, context=context
                ).data,
                "recent_activities": ActivityLogSerializer(
                    ActivityLog.objects.filter(is_deleted=False).select_related("actor")[:8], many=True
                ).data,
            }
        )


@crud_schema(tag="Dashboard", resource="event", serializer=SchoolEventSerializer)
class SchoolEventViewSet(RBACModelViewSet):
    """The school calendar — exams, holidays, sports days and meetings."""

    permission_module = "notice"
    permission_map = {"upcoming": "notice.view"}
    serializer_class = SchoolEventSerializer
    queryset = SchoolEvent.objects.filter(is_deleted=False)
    search_fields = ["title", "description", "venue"]
    ordering_fields = ["start_date", "title"]
    ordering = ["start_date"]
    filterset_fields = ["category", "is_holiday", "is_active"]

    @extend_schema(
        tags=["Dashboard"],
        summary="Upcoming events",
        description="Calendar entries starting today or later.",
        responses={200: SchoolEventSerializer(many=True), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="upcoming")
    def upcoming(self, request):
        queryset = self.get_queryset().filter(start_date__gte=timezone.localdate()).order_by("start_date")[:10]
        return Response(self.get_serializer(queryset, many=True).data)


@extend_schema(
    tags=["Dashboard"],
    summary="Public school profile",
    description=(
        "Unauthenticated endpoint that supplies the landing page with the school's "
        "identity and headline counts. Contains no personal data."
    ),
    responses={200: SchoolInfoSerializer},
)
class SchoolInfoAPIView(APIView):
    """Public identity and statistics for The Holy Child Pre-Cadet & High School."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        school = SchoolProfile.load()
        logo = school.logo.url if school.logo else None
        return Response(
            {
                "name_en": school.name_en,
                "name_bn": school.name_bn,
                "short_name": school.short_name,
                "brand_name": school.brand_name,
                "address": school.address,
                "village": school.village,
                "upazila": school.upazila,
                "district": school.district,
                "country": school.country,
                "established": school.established,
                "grade_range": school.grade_range,
                "grade_range_bn": school.grade_range_bn,
                "email": school.email,
                "phone": school.phone,
                "website": school.website,
                "logo_url": request.build_absolute_uri(logo) if logo else None,
                "stats": public_school_stats(),
            }
        )


@extend_schema(tags=["Settings"])
class SchoolProfileAPIView(RetrieveUpdateAPIView):
    """
    The editable school identity behind the Settings screen.

    ``setting.view`` to read, ``setting.update`` to change — resolved from the
    request method by :class:`HasActionPermission`. Accepts multipart so the
    crest can be uploaded in the same request as the text fields.
    """

    serializer_class = SchoolProfileSerializer
    permission_classes = [IsAuthenticated, HasActionPermission]
    permission_module = "setting"
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_object(self):
        return SchoolProfile.load()

    @extend_schema(
        summary="Read the school profile",
        responses={200: SchoolProfileSerializer, **PROTECTED_RESPONSES},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update the school profile",
        description="Requires `setting.update`. Send multipart to replace the logo.",
        responses={200: SchoolProfileSerializer, **PROTECTED_RESPONSES},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update the school profile",
        responses={200: SchoolProfileSerializer, **PROTECTED_RESPONSES},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def perform_update(self, serializer):
        profile = serializer.save()
        ActivityLog.record(
            self.request.user, ActivityLog.Action.UPDATED, "setting", "School profile updated."
        )
        return profile
