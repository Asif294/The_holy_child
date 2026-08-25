from django.contrib import admin

from apps.principal.models import ApprovalRequest, Notice, Principal


@admin.register(Principal)
class PrincipalAdmin(admin.ModelAdmin):
    list_display = ("full_name", "designation", "tenure_start", "tenure_end", "is_current", "is_active")
    list_filter = ("is_current", "is_active")
    search_fields = ("full_name", "email", "phone")
    autocomplete_fields = ("user",)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "audience", "priority", "is_published", "published_at", "issued_by")
    list_filter = ("audience", "priority", "is_published")
    search_fields = ("title", "body")
    date_hierarchy = "created_at"


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "status", "requested_by", "decided_by", "decided_at")
    list_filter = ("status", "category")
    search_fields = ("title", "details")
    date_hierarchy = "created_at"
