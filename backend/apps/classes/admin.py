from django.contrib import admin

from apps.classes.models import AcademicSession, SchoolClass, Section


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_current", "is_active")
    list_filter = ("is_current", "is_active")
    search_fields = ("name",)


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0
    fields = ("name", "capacity", "room_number", "class_teacher", "is_active")


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "order", "is_active")
    list_editable = ("order",)
    search_fields = ("name", "code")
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "capacity", "room_number", "class_teacher", "is_active")
    list_filter = ("school_class", "is_active")
    search_fields = ("name", "school_class__name")
