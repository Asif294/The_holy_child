from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.schema import PROTECTED_RESPONSES, crud_schema
from apps.common.viewsets import RBACModelViewSet
from apps.fees.models import FeeCategory, FeeStructure, Invoice, Payment
from apps.fees.serializers import (
    FeeCategorySerializer,
    FeeStructureSerializer,
    InvoiceSerializer,
    PaymentSerializer,
)


@crud_schema(tag="Fees", resource="fee category", plural="fee categories", serializer=FeeCategorySerializer)
class FeeCategoryViewSet(RBACModelViewSet):
    """Billable heads — tuition, admission, exam, transport, and so on."""

    permission_module = "fee"
    serializer_class = FeeCategorySerializer
    queryset = FeeCategory.objects.filter(is_deleted=False)
    search_fields = ["name", "code"]
    ordering_fields = ["name"]
    filterset_fields = ["frequency", "is_active"]


@crud_schema(tag="Fees", resource="fee structure", plural="fee structures", serializer=FeeStructureSerializer)
class FeeStructureViewSet(RBACModelViewSet):
    """How much each class pays under each fee head, per session."""

    permission_module = "fee"
    serializer_class = FeeStructureSerializer
    search_fields = ["school_class__name", "category__name"]
    ordering_fields = ["amount", "created_at"]
    filterset_fields = ["session", "school_class", "category", "is_active"]

    def get_queryset(self):
        return FeeStructure.objects.filter(is_deleted=False).select_related("session", "school_class", "category")


@crud_schema(
    tag="Fees",
    resource="invoice",
    serializer=InvoiceSerializer,
    descriptions={
        "list": (
            "Invoices with their computed `payable`, `paid_amount` and `due_amount`. "
            "Filter by `student`, `status`, `session` or `category`. "
            "Requires the `fee.view` permission."
        ),
    },
)
class InvoiceViewSet(RBACModelViewSet):
    """Bills raised against students."""

    permission_module = "fee"
    permission_map = {"statistics": "fee.view", "outstanding": "fee.view"}
    serializer_class = InvoiceSerializer
    search_fields = ["invoice_number", "student__full_name", "student__student_id", "title"]
    ordering_fields = ["issue_date", "due_date", "amount", "created_at"]
    ordering = ["-issue_date"]
    filterset_fields = ["student", "status", "session", "category", "period_month", "period_year", "is_active"]

    def get_queryset(self):
        return (
            Invoice.objects.filter(is_deleted=False)
            .select_related("student__school_class", "session", "category")
            .prefetch_related("payments")
        )

    @extend_schema(
        tags=["Fees"],
        summary="Fee collection statistics",
        description="Billed, collected and outstanding totals plus a breakdown by invoice status.",
        parameters=[OpenApiParameter("session", int, description="Restrict to one academic session.")],
        responses={200: OpenApiResponse(description="Fee totals."), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="statistics")
    def statistics(self, request):
        queryset = self.get_queryset()
        session = request.query_params.get("session")
        if session:
            queryset = queryset.filter(session_id=session)

        billed = queryset.aggregate(
            amount=Sum("amount"), discount=Sum("discount"), fine=Sum("fine")
        )
        total_billed = (
            (billed["amount"] or Decimal("0")) - (billed["discount"] or Decimal("0")) + (billed["fine"] or Decimal("0"))
        )
        collected = Payment.objects.filter(is_deleted=False, invoice__in=queryset).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")

        return Response(
            {
                "total_billed": total_billed,
                "total_collected": collected,
                "total_outstanding": max(total_billed - collected, Decimal("0")),
                "collection_rate": round(float(collected / total_billed * 100), 2) if total_billed else 0.0,
                "invoice_count": queryset.count(),
                "by_status": list(queryset.values("status").annotate(total=Count("id")).order_by("-total")),
                "overdue_count": queryset.filter(
                    due_date__lt=timezone.localdate(),
                    status__in=[Invoice.Status.UNPAID, Invoice.Status.PARTIAL],
                ).count(),
            }
        )

    @extend_schema(
        tags=["Fees"],
        summary="Outstanding invoices",
        description="Unpaid and partially paid invoices, oldest due date first — the collections worklist.",
        responses={200: InvoiceSerializer(many=True), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="outstanding")
    def outstanding(self, request):
        queryset = self.filter_queryset(
            self.get_queryset()
            .filter(status__in=[Invoice.Status.UNPAID, Invoice.Status.PARTIAL])
            .order_by("due_date")
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return Response(self.get_serializer(queryset, many=True).data)


@crud_schema(
    tag="Fees",
    resource="payment",
    serializer=PaymentSerializer,
    descriptions={
        "create": (
            "Records money received against an invoice and re-derives the invoice status "
            "(unpaid → partial → paid). Overpayment is rejected. "
            "Requires the `payment.create` permission."
        ),
    },
)
class PaymentViewSet(RBACModelViewSet):
    """Money received against invoices."""

    permission_module = "payment"
    permission_map = {"recent": "payment.view"}
    serializer_class = PaymentSerializer
    search_fields = ["receipt_number", "transaction_reference", "invoice__invoice_number",
                     "invoice__student__full_name"]
    ordering_fields = ["paid_at", "amount", "created_at"]
    ordering = ["-paid_at"]
    filterset_fields = ["invoice", "method", "received_by", "is_active"]

    def get_queryset(self):
        return (
            Payment.objects.filter(is_deleted=False)
            .select_related("invoice__student", "received_by")
        )

    @extend_schema(
        tags=["Fees"],
        summary="Recent payments",
        description="The most recent payments — powers the dashboard's *Recent payments* panel.",
        parameters=[OpenApiParameter("limit", int, description="How many to return (default 10, max 50).")],
        responses={200: PaymentSerializer(many=True), **PROTECTED_RESPONSES},
    )
    @action(detail=False, methods=["get"], url_path="recent")
    def recent(self, request):
        limit = min(int(request.query_params.get("limit", 10)), 50)
        queryset = self.get_queryset()[:limit]
        return Response(self.get_serializer(queryset, many=True).data)
