from decimal import Decimal

from rest_framework import serializers

from apps.fees.models import FeeCategory, FeeStructure, Invoice, Payment


class FeeCategorySerializer(serializers.ModelSerializer):
    frequency_display = serializers.CharField(source="get_frequency_display", read_only=True)

    class Meta:
        model = FeeCategory
        fields = ("id", "name", "code", "frequency", "frequency_display", "description",
                  "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "frequency_display", "created_at", "updated_at")


class FeeStructureSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="school_class.name", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    session_name = serializers.CharField(source="session.name", read_only=True)

    class Meta:
        model = FeeStructure
        fields = ("id", "session", "session_name", "school_class", "class_name", "category",
                  "category_name", "amount", "due_day", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "session_name", "class_name", "category_name", "created_at", "updated_at")

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError("The amount cannot be negative.")
        return value

    def validate_due_day(self, value):
        if not 1 <= value <= 31:
            raise serializers.ValidationError("The due day must fall between 1 and 31.")
        return value


class PaymentSerializer(serializers.ModelSerializer):
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    student_name = serializers.CharField(source="invoice.student.full_name", read_only=True)
    invoice_number = serializers.CharField(source="invoice.invoice_number", read_only=True)
    received_by_name = serializers.CharField(source="received_by.full_name", read_only=True, default=None)

    class Meta:
        model = Payment
        fields = ("id", "receipt_number", "invoice", "invoice_number", "student_name", "amount",
                  "method", "method_display", "transaction_reference", "paid_at", "received_by",
                  "received_by_name", "note", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "invoice_number", "student_name", "method_display", "received_by",
                            "received_by_name", "created_at", "updated_at")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("A payment must be greater than zero.")
        return value

    def validate(self, attrs):
        invoice = attrs.get("invoice", getattr(self.instance, "invoice", None))
        amount = attrs.get("amount", getattr(self.instance, "amount", Decimal("0")))
        if invoice is not None:
            already_paid = invoice.paid_amount
            if self.instance:
                already_paid -= self.instance.amount
            if already_paid + amount > invoice.payable:
                raise serializers.ValidationError(
                    {"amount": f"This payment would exceed the outstanding balance of {invoice.payable - already_paid}."}
                )
            if invoice.status in {Invoice.Status.CANCELLED, Invoice.Status.WAIVED}:
                raise serializers.ValidationError(
                    {"invoice": f"This invoice is {invoice.get_status_display().lower()} and cannot take payments."}
                )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request is not None:
            validated_data["received_by"] = request.user
        return super().create(validated_data)


class InvoiceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_code = serializers.CharField(source="student.student_id", read_only=True)
    class_name = serializers.CharField(source="student.school_class.name", read_only=True, default=None)
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payable = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    paid_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    due_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id", "invoice_number", "student", "student_name", "student_code", "class_name",
            "session", "category", "category_name", "title", "period_month", "period_year",
            "amount", "discount", "fine", "payable", "paid_amount", "due_amount",
            "issue_date", "due_date", "status", "status_display", "note", "payments",
            "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "student_name", "student_code", "class_name", "category_name",
                            "status_display", "payable", "paid_amount", "due_amount", "payments",
                            "created_at", "updated_at")

    def validate_invoice_number(self, value: str) -> str:
        value = value.strip().upper()
        queryset = Invoice.objects.filter(invoice_number__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("An invoice with this number already exists.")
        return value

    def validate(self, attrs):
        issue_date = attrs.get("issue_date", getattr(self.instance, "issue_date", None))
        due_date = attrs.get("due_date", getattr(self.instance, "due_date", None))
        if issue_date and due_date and due_date < issue_date:
            raise serializers.ValidationError({"due_date": "The due date cannot fall before the issue date."})

        amount = attrs.get("amount", getattr(self.instance, "amount", Decimal("0")))
        discount = attrs.get("discount", getattr(self.instance, "discount", Decimal("0")))
        if discount > amount:
            raise serializers.ValidationError({"discount": "The discount cannot exceed the invoice amount."})

        month = attrs.get("period_month", getattr(self.instance, "period_month", None))
        if month is not None and not 1 <= month <= 12:
            raise serializers.ValidationError({"period_month": "The month must fall between 1 and 12."})
        return attrs
