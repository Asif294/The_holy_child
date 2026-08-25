from django.contrib import admin

from apps.fees.models import FeeCategory, FeeStructure, Invoice, Payment


@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "frequency", "is_active")
    list_filter = ("frequency", "is_active")
    search_fields = ("name", "code")


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("session", "school_class", "category", "amount", "due_day", "is_active")
    list_filter = ("session", "school_class", "category")


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("receipt_number", "amount", "method", "paid_at", "received_by")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "student", "title", "amount", "status", "due_date")
    list_filter = ("status", "session", "category")
    search_fields = ("invoice_number", "student__full_name", "student__student_id")
    date_hierarchy = "issue_date"
    inlines = [PaymentInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "invoice", "amount", "method", "paid_at", "received_by")
    list_filter = ("method",)
    search_fields = ("receipt_number", "transaction_reference", "invoice__invoice_number")
    date_hierarchy = "paid_at"
