from django.contrib import admin

from apps.subjects.models import ClassSubject, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "category", "full_marks", "pass_marks", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "code")


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ("school_class", "subject", "teacher", "weekly_periods", "is_active")
    list_filter = ("school_class", "is_active")
    search_fields = ("subject__name", "school_class__name")
