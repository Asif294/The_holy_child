from decimal import Decimal

from django.db import models
from django.db.models import Sum

from apps.common.models import BaseModel


class FeeCategory(BaseModel):
    """A billable head — tuition, admission, exam, transport, and so on."""

    class Frequency(models.TextChoices):
        ONE_TIME = "one_time", "One time"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        YEARLY = "yearly", "Yearly"

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.MONTHLY)
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "fee_categories"
        ordering = ["name"]
        verbose_name_plural = "Fee categories"

    def __str__(self):
        return self.name


class FeeStructure(BaseModel):
    """How much a given class pays under a given fee head for a given session."""

    session = models.ForeignKey(
        "classes.AcademicSession", on_delete=models.CASCADE, related_name="fee_structures"
    )
    school_class = models.ForeignKey("classes.SchoolClass", on_delete=models.CASCADE, related_name="fee_structures")
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name="structures")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_day = models.PositiveSmallIntegerField(default=10, help_text="Day of month the instalment falls due.")

    class Meta:
        db_table = "fee_structures"
        ordering = ["school_class__order", "category__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "school_class", "category"], name="unique_fee_structure"
            )
        ]

    def __str__(self):
        return f"{self.school_class.name} · {self.category.name} · {self.amount}"


class Invoice(BaseModel):
    """A bill raised against a student, settled by one or more payments."""

    class Status(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PARTIAL = "partial", "Partially paid"
        PAID = "paid", "Paid"
        WAIVED = "waived", "Waived"
        CANCELLED = "cancelled", "Cancelled"

    invoice_number = models.CharField(max_length=30, unique=True, db_index=True)
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="invoices")
    session = models.ForeignKey(
        "classes.AcademicSession", on_delete=models.SET_NULL, related_name="invoices", null=True, blank=True
    )
    category = models.ForeignKey(
        FeeCategory, on_delete=models.SET_NULL, related_name="invoices", null=True, blank=True
    )
    title = models.CharField(max_length=150, help_text='e.g. "Tuition — March 2026"')
    period_month = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1–12 for monthly fees.")
    period_year = models.PositiveSmallIntegerField(null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    issue_date = models.DateField()
    due_date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID, db_index=True)
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "invoices"
        ordering = ["-issue_date", "-created_at"]
        indexes = [models.Index(fields=["status", "due_date"])]

    def __str__(self):
        return f"{self.invoice_number} · {self.student.full_name}"

    @property
    def payable(self) -> Decimal:
        return (self.amount or Decimal("0")) - (self.discount or Decimal("0")) + (self.fine or Decimal("0"))

    @property
    def paid_amount(self) -> Decimal:
        return self.payments.filter(is_deleted=False).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

    @property
    def due_amount(self) -> Decimal:
        return max(self.payable - self.paid_amount, Decimal("0.00"))

    def refresh_status(self, commit: bool = True) -> str:
        """Recompute ``status`` from the payments recorded against this invoice."""
        if self.status in {self.Status.WAIVED, self.Status.CANCELLED}:
            return self.status
        paid = self.paid_amount
        if paid <= 0:
            self.status = self.Status.UNPAID
        elif paid < self.payable:
            self.status = self.Status.PARTIAL
        else:
            self.status = self.Status.PAID
        if commit:
            self.save(update_fields=["status", "updated_at"])
        return self.status


class Payment(BaseModel):
    """Money actually received against an invoice."""

    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        BKASH = "bkash", "bKash"
        NAGAD = "nagad", "Nagad"
        ROCKET = "rocket", "Rocket"
        BANK = "bank", "Bank transfer"
        CHEQUE = "cheque", "Cheque"
        CARD = "card", "Card"

    receipt_number = models.CharField(max_length=30, unique=True, db_index=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices, default=Method.CASH)
    transaction_reference = models.CharField(max_length=100, blank=True, default="")
    paid_at = models.DateTimeField(db_index=True)
    received_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, related_name="received_payments", null=True, blank=True
    )
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "payments"
        ordering = ["-paid_at"]

    def __str__(self):
        return f"{self.receipt_number} · {self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.refresh_status()
