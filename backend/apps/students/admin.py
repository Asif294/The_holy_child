from django.contrib import admin

from apps.students.models import Guardian, Student


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ("full_name", "relation", "phone", "occupation", "is_active")
    list_filter = ("relation", "is_active")
    search_fields = ("full_name", "phone", "email")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "school_class", "section", "roll_number", "status", "is_active")
    list_filter = ("status", "school_class", "section", "gender", "is_active")
    search_fields = ("full_name", "student_id", "admission_number", "father_name", "mother_name")
    autocomplete_fields = ("user",)
    date_hierarchy = "admission_date"
