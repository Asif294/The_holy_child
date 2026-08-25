from django.contrib import admin

from apps.exams.models import Exam, ExamSchedule, ExamType, Result


@admin.register(ExamType)
class ExamTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "weight", "is_active")
    search_fields = ("name", "code")


class ExamScheduleInline(admin.TabularInline):
    model = ExamSchedule
    extra = 0
    fields = ("school_class", "subject", "exam_date", "start_time", "end_time", "room", "full_marks")


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "exam_type", "session", "start_date", "end_date", "status")
    list_filter = ("status", "session", "exam_type")
    search_fields = ("name",)
    inlines = [ExamScheduleInline]


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ("exam", "school_class", "subject", "exam_date", "start_time", "end_time", "room")
    list_filter = ("exam", "school_class")


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "exam", "subject", "marks_obtained", "grade", "grade_point", "is_published")
    list_filter = ("exam", "subject", "is_published", "is_absent")
    search_fields = ("student__full_name", "student__student_id")
