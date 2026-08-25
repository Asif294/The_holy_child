from django.contrib import admin

from apps.teachers.models import Department, Designation, Teacher


@admin.register(Designation)
class DesignationAdmin(admin.ModelAdmin):
    list_display = ("name", "rank", "is_active")
    ordering = ("rank",)
    search_fields = ("name",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "head", "is_active")
    search_fields = ("name", "code")


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "designation", "department", "status", "joining_date", "is_active")
    list_filter = ("status", "employment_type", "department", "designation", "is_active")
    search_fields = ("full_name", "employee_id", "email", "phone")
    filter_horizontal = ("subjects",)
    autocomplete_fields = ("user",)
