from rest_framework import serializers

from apps.exams.models import Exam, ExamSchedule, ExamType, Result


class ExamTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamType
        fields = ("id", "name", "code", "weight", "description", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_weight(self, value):
        if not 0 < value <= 100:
            raise serializers.ValidationError("The weight must fall between 1 and 100 percent.")
        return value


class ExamScheduleSerializer(serializers.ModelSerializer):
    exam_name = serializers.CharField(source="exam.name", read_only=True)
    class_name = serializers.CharField(source="school_class.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)

    class Meta:
        model = ExamSchedule
        fields = ("id", "exam", "exam_name", "school_class", "class_name", "subject", "subject_name",
                  "exam_date", "start_time", "end_time", "room", "full_marks", "pass_marks",
                  "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "exam_name", "class_name", "subject_name", "created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and end <= start:
            raise serializers.ValidationError({"end_time": "A paper must end after it starts."})

        full_marks = attrs.get("full_marks", getattr(self.instance, "full_marks", 100))
        pass_marks = attrs.get("pass_marks", getattr(self.instance, "pass_marks", 33))
        if pass_marks > full_marks:
            raise serializers.ValidationError({"pass_marks": "Pass marks cannot exceed full marks."})

        exam = attrs.get("exam", getattr(self.instance, "exam", None))
        exam_date = attrs.get("exam_date", getattr(self.instance, "exam_date", None))
        if exam and exam_date and not (exam.start_date <= exam_date <= exam.end_date):
            raise serializers.ValidationError(
                {"exam_date": f"The paper must sit between {exam.start_date} and {exam.end_date}."}
            )
        return attrs


class ExamSerializer(serializers.ModelSerializer):
    exam_type_name = serializers.CharField(source="exam_type.name", read_only=True, default=None)
    session_name = serializers.CharField(source="session.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    schedule_count = serializers.SerializerMethodField()
    is_upcoming = serializers.BooleanField(read_only=True)

    class Meta:
        model = Exam
        fields = ("id", "name", "exam_type", "exam_type_name", "session", "session_name",
                  "start_date", "end_date", "status", "status_display", "instructions",
                  "schedule_count", "is_upcoming", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "exam_type_name", "session_name", "status_display",
                            "schedule_count", "is_upcoming", "created_at", "updated_at")

    def get_schedule_count(self, obj) -> int:
        return obj.schedules.filter(is_deleted=False).count()

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "An exam cannot end before it starts."})
        return attrs


class ResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_roll = serializers.IntegerField(source="student.roll_number", read_only=True, default=None)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    exam_name = serializers.CharField(source="exam.name", read_only=True)
    percentage = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)

    class Meta:
        model = Result
        fields = ("id", "exam", "exam_name", "student", "student_name", "student_roll", "subject",
                  "subject_name", "marks_obtained", "full_marks", "percentage", "grade", "grade_point",
                  "is_absent", "is_published", "remarks", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "exam_name", "student_name", "student_roll", "subject_name",
                            "percentage", "grade", "grade_point", "created_at", "updated_at")

    def validate(self, attrs):
        marks = attrs.get("marks_obtained", getattr(self.instance, "marks_obtained", 0))
        full_marks = attrs.get("full_marks", getattr(self.instance, "full_marks", 100))
        if marks < 0:
            raise serializers.ValidationError({"marks_obtained": "Marks cannot be negative."})
        if marks > full_marks:
            raise serializers.ValidationError({"marks_obtained": "Marks obtained cannot exceed the full marks."})

        exam = attrs.get("exam", getattr(self.instance, "exam", None))
        student = attrs.get("student", getattr(self.instance, "student", None))
        subject = attrs.get("subject", getattr(self.instance, "subject", None))
        queryset = Result.objects.filter(exam=exam, student=student, subject=subject)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                {"subject": "A result for this student and subject already exists in this exam."}
            )
        return attrs
