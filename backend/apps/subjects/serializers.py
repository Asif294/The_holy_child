from rest_framework import serializers

from apps.subjects.models import ClassSubject, Subject


class SubjectSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    class_count = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ("id", "name", "name_bn", "code", "category", "category_display", "full_marks",
                  "pass_marks", "description", "class_count", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "category_display", "class_count", "created_at", "updated_at")

    def get_class_count(self, obj) -> int:
        return obj.class_subjects.filter(is_deleted=False).count()

    def validate_code(self, value: str) -> str:
        value = value.strip().upper()
        queryset = Subject.objects.filter(code__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A subject with this code already exists.")
        return value

    def validate(self, attrs):
        full_marks = attrs.get("full_marks", getattr(self.instance, "full_marks", 100))
        pass_marks = attrs.get("pass_marks", getattr(self.instance, "pass_marks", 33))
        if pass_marks > full_marks:
            raise serializers.ValidationError({"pass_marks": "Pass marks cannot exceed full marks."})
        return attrs


class ClassSubjectSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    class_name = serializers.CharField(source="school_class.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True, default=None)

    class Meta:
        model = ClassSubject
        fields = ("id", "school_class", "class_name", "subject", "subject_name", "subject_code",
                  "teacher", "teacher_name", "weekly_periods", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "class_name", "subject_name", "subject_code", "teacher_name",
                            "created_at", "updated_at")

    def validate(self, attrs):
        school_class = attrs.get("school_class", getattr(self.instance, "school_class", None))
        subject = attrs.get("subject", getattr(self.instance, "subject", None))
        queryset = ClassSubject.objects.filter(school_class=school_class, subject=subject, is_deleted=False)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError({"subject": "This subject is already assigned to that class."})
        return attrs
