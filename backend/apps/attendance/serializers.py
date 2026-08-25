from django.utils import timezone
from rest_framework import serializers

from apps.attendance.models import AttendanceStatus, StudentAttendance, TeacherAttendance


class StudentAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_roll = serializers.IntegerField(source="student.roll_number", read_only=True, default=None)
    section_name = serializers.CharField(source="section.display_name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    marked_by_name = serializers.CharField(source="marked_by.full_name", read_only=True, default=None)

    class Meta:
        model = StudentAttendance
        fields = ("id", "student", "student_name", "student_roll", "section", "section_name", "date",
                  "status", "status_display", "check_in_time", "remarks", "marked_by", "marked_by_name",
                  "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "student_name", "student_roll", "section_name", "status_display",
                            "marked_by", "marked_by_name", "created_at", "updated_at")

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Attendance cannot be recorded for a future date.")
        return value

    def validate(self, attrs):
        student = attrs.get("student", getattr(self.instance, "student", None))
        date = attrs.get("date", getattr(self.instance, "date", None))
        queryset = StudentAttendance.objects.filter(student=student, date=date)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                {"date": "Attendance for this student has already been recorded on that date."}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request is not None:
            validated_data["marked_by"] = request.user
        if not validated_data.get("section") and validated_data["student"].section_id:
            validated_data["section"] = validated_data["student"].section
        return super().create(validated_data)


class AttendanceEntrySerializer(serializers.Serializer):
    """One row inside a bulk attendance submission."""

    student = serializers.IntegerField(help_text="Student primary key.")
    status = serializers.ChoiceField(choices=AttendanceStatus.choices)
    check_in_time = serializers.TimeField(required=False, allow_null=True)
    remarks = serializers.CharField(required=False, allow_blank=True, max_length=255)


class BulkAttendanceSerializer(serializers.Serializer):
    """
    Submit a whole register in one request.

    Re-submitting the same date updates the existing marks rather than failing,
    so a teacher can correct a register without deleting rows first.
    """

    date = serializers.DateField(help_text="The date the register covers.")
    section = serializers.IntegerField(required=False, allow_null=True, help_text="Section primary key.")
    entries = AttendanceEntrySerializer(many=True, allow_empty=False)

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Attendance cannot be recorded for a future date.")
        return value

    def validate_entries(self, value):
        seen = set()
        for entry in value:
            if entry["student"] in seen:
                raise serializers.ValidationError(f"Student {entry['student']} appears more than once.")
            seen.add(entry["student"])
        return value


class TeacherAttendanceSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = TeacherAttendance
        fields = ("id", "teacher", "teacher_name", "date", "status", "status_display",
                  "check_in_time", "check_out_time", "remarks", "marked_by",
                  "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "teacher_name", "status_display", "marked_by", "created_at", "updated_at")

    def create(self, validated_data):
        request = self.context.get("request")
        if request is not None:
            validated_data["marked_by"] = request.user
        return super().create(validated_data)
