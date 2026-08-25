from django.contrib import admin

from apps.attendance.models import StudentAttendance, TeacherAttendance


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "status", "section", "marked_by")
    list_filter = ("status", "date", "section")
    search_fields = ("student__full_name", "student__student_id")
    date_hierarchy = "date"


@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ("teacher", "date", "status", "check_in_time", "check_out_time")
    list_filter = ("status", "date")
    search_fields = ("teacher__full_name", "teacher__employee_id")
    date_hierarchy = "date"
