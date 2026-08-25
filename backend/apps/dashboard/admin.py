from django.contrib import admin

from apps.dashboard.models import ActivityLog, SchoolEvent, SchoolProfile


@admin.register(SchoolEvent)
class SchoolEventAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "start_date", "end_date", "venue", "is_holiday", "is_active")
    list_filter = ("category", "is_holiday", "is_active")
    search_fields = ("title", "description", "venue")
    date_hierarchy = "start_date"


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "module", "description")
    list_filter = ("action", "module")
    search_fields = ("description", "actor_name")
    date_hierarchy = "created_at"
    readonly_fields = ("actor", "actor_name", "action", "module", "description", "object_id")


@admin.register(SchoolProfile)
class SchoolProfileAdmin(admin.ModelAdmin):
    """Singleton: one row, edited in place — never added to or removed."""

    list_display = ("name_en", "short_name", "phone", "email", "updated_at")

    def has_add_permission(self, request):
        return not SchoolProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
