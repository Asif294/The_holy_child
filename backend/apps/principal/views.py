from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.common.schema import DETAIL_WRITE_RESPONSES, PROTECTED_RESPONSES, crud_schema
from apps.common.viewsets import RBACModelViewSet
from apps.principal.models import ApprovalRequest, Notice, Principal
from apps.principal.serializers import (
    ApprovalDecisionSerializer,
    ApprovalRequestSerializer,
    NoticeSerializer,
    PrincipalPublicSerializer,
    PrincipalSerializer,
)


@crud_schema(
    tag="Principal",
    resource="principal",
    serializer=PrincipalSerializer,
    descriptions={
        "list": (
            "Principals of the institution, current first. Historical records are kept "
            "so past tenures remain auditable. Requires the `principal.view` permission."
        ),
        "create": (
            "Records a principal. Setting `is_current` to `true` automatically stands down "
            "the previous incumbent. Requires the `principal.update` permission."
        ),
    },
)
class PrincipalViewSet(RBACModelViewSet):
    """
    The principal's office.

    Only one principal is ``is_current`` at a time; the model enforces that when
    a new record is marked current.
    """

    permission_module = "principal"
    # The principal record has no separate create/delete codes — the office is
    # administered through `principal.update`.
    permission_map = {
        "create": "principal.update",
        "destroy": "principal.update",
        "current": "principal.view",
        "dashboard": "principal.view",
    }
    serializer_class = PrincipalSerializer
    search_fields = ["full_name", "designation", "email", "phone"]
    ordering_fields = ["tenure_start", "full_name"]
    filterset_fields = ["is_current", "is_active"]

    def get_queryset(self):
        return Principal.objects.filter(is_deleted=False).select_related("user", "teacher")

    @extend_schema(
        tags=["Principal"],
        summary="The sitting principal",
        description="Returns the record currently flagged `is_current`, or `null` if none is set.",
        responses={200: PrincipalSerializer, **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="current")
    def current(self, request):
        principal = self.get_queryset().filter(is_current=True).first()
        if principal is None:
            return Response({"success": True, "data": None, "message": "No sitting principal has been recorded."})
        return Response(self.get_serializer(principal).data)

    @extend_schema(
        tags=["Principal"],
        summary="Principal's office dashboard",
        description=(
            "A focused summary for the principal: pending approvals by category, "
            "notices awaiting publication, and the headline school counts."
        ),
        responses={200: OpenApiResponse(description="Principal office summary."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        from django.db.models import Count

        from apps.students.models import Student
        from apps.teachers.models import Teacher

        pending = ApprovalRequest.objects.filter(is_deleted=False, status=ApprovalRequest.Status.PENDING)
        return Response(
            {
                "principal": PrincipalSerializer(
                    self.get_queryset().filter(is_current=True).first(), context=self.get_serializer_context()
                ).data
                if self.get_queryset().filter(is_current=True).exists()
                else None,
                "pending_approvals": pending.count(),
                "pending_by_category": list(
                    pending.values("category").annotate(total=Count("id")).order_by("-total")
                ),
                "unpublished_notices": Notice.objects.filter(is_deleted=False, is_published=False).count(),
                "total_students": Student.objects.filter(is_deleted=False, status=Student.Status.ACTIVE).count(),
                "total_teachers": Teacher.objects.filter(is_deleted=False, status=Teacher.Status.ACTIVE).count(),
                "recent_approvals": ApprovalRequestSerializer(
                    ApprovalRequest.objects.filter(is_deleted=False).select_related("requested_by", "decided_by")[:5],
                    many=True,
                    context=self.get_serializer_context(),
                ).data,
            }
        )


@extend_schema(
    tags=["Principal"],
    summary="Public principal profile",
    description=(
        "Unauthenticated endpoint powering the *Message from the Principal* section "
        "of the public site. Exposes only the name, designation, qualification and "
        "message — never contact details or internal fields."
    ),
    responses={
        200: OpenApiResponse(response=PrincipalPublicSerializer, description="The sitting principal, or null."),
    },
    examples=[
        OpenApiExample(
            "Public profile",
            value={
                "full_name": "Md. Abdul Karim",
                "designation": "Principal",
                "qualification": "M.A., B.Ed.",
                "experience_years": 22,
                "message": "Welcome to The Holy Child Pre-Cadet & High School…",
                "photo_url": None,
            },
            response_only=True,
        )
    ],
)
class PublicPrincipalViewSet(ReadOnlyModelViewSet):
    """Read-only public view of the sitting principal."""

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = PrincipalPublicSerializer
    pagination_class = None

    def get_queryset(self):
        return Principal.objects.filter(is_deleted=False, is_active=True, is_current=True)

    def list(self, request, *args, **kwargs):
        principal = self.get_queryset().first()
        if principal is None:
            return Response({"success": True, "data": None})
        return Response({"success": True, "data": self.get_serializer(principal).data})


@crud_schema(
    tag="Principal",
    resource="notice",
    serializer=NoticeSerializer,
    descriptions={
        "list": (
            "Notices issued by the principal's office. Filter by `audience`, `priority` "
            "or `is_published`. Requires the `notice.view` permission."
        ),
    },
)
class NoticeViewSet(RBACModelViewSet):
    """Notices issued by the principal's office."""

    permission_module = "notice"
    permission_map = {"publish": "notice.update"}
    serializer_class = NoticeSerializer
    search_fields = ["title", "body"]
    ordering_fields = ["published_at", "created_at", "priority"]
    ordering = ["-published_at", "-created_at"]
    filterset_fields = ["audience", "priority", "is_published", "is_active"]

    def get_queryset(self):
        return Notice.objects.filter(is_deleted=False).select_related("issued_by")

    @extend_schema(
        tags=["Principal"],
        summary="Publish a notice",
        description="Marks the notice published and stamps `published_at` if it is not already set.",
        request=None,
        responses={200: NoticeSerializer, **DETAIL_WRITE_RESPONSES},
    )
    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        notice = self.get_object()
        notice.is_published = True
        notice.published_at = notice.published_at or timezone.now()
        notice.save(update_fields=["is_published", "published_at", "updated_at"])
        return Response(self.get_serializer(notice).data)


@crud_schema(
    tag="Principal",
    resource="approval request",
    plural="approval requests",
    serializer=ApprovalRequestSerializer,
    descriptions={
        "create": (
            "Raises a request for the principal's decision. The requester is taken from "
            "the authenticated user, never from the request body."
        ),
    },
)
class ApprovalRequestViewSet(RBACModelViewSet):
    """
    Requests routed to the principal for a decision.

    Anyone authenticated may raise a request; only a holder of `principal.approve`
    can decide one.
    """

    permission_module = "principal"
    permission_map = {
        "list": "principal.view",
        "retrieve": "principal.view",
        # Raising a request is not a privileged act — the decision is.
        "create": None,
        "update": "principal.update",
        "partial_update": "principal.update",
        "destroy": "principal.update",
        "decide": "principal.approve",
        "mine": None,
    }
    serializer_class = ApprovalRequestSerializer
    search_fields = ["title", "details"]
    ordering_fields = ["created_at", "decided_at"]
    filterset_fields = ["status", "category", "requested_by", "is_active"]

    def get_queryset(self):
        return ApprovalRequest.objects.filter(is_deleted=False).select_related("requested_by", "decided_by")

    @extend_schema(
        tags=["Principal"],
        summary="Approve or reject a request",
        description=(
            "Records the principal's decision. A request can only be decided once — "
            "re-deciding a settled request is rejected. Requires the `principal.approve` permission."
        ),
        request=ApprovalDecisionSerializer,
        responses={200: ApprovalRequestSerializer, **DETAIL_WRITE_RESPONSES},
        examples=[
            OpenApiExample(
                "Approve",
                value={"decision": "approved", "note": "Approved for three days."},
                request_only=True,
            )
        ],
    )
    @action(detail=True, methods=["post"], url_path="decide")
    def decide(self, request, pk=None):
        approval = self.get_object()
        if approval.status != ApprovalRequest.Status.PENDING:
            raise ValidationError(
                {"detail": f"This request has already been {approval.get_status_display().lower()}."}
            )

        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        approval.status = serializer.validated_data["decision"]
        approval.decision_note = serializer.validated_data.get("note", "")
        approval.decided_by = request.user
        approval.decided_at = timezone.now()
        approval.save(update_fields=["status", "decision_note", "decided_by", "decided_at", "updated_at"])
        return Response(self.get_serializer(approval).data)

    @extend_schema(
        tags=["Principal"],
        summary="My approval requests",
        description="The requests raised by the signed-in user, whatever their role.",
        responses={200: ApprovalRequestSerializer(many=True), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        queryset = self.filter_queryset(self.get_queryset().filter(requested_by=request.user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(queryset, many=True).data)
