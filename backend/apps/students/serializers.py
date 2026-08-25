from rest_framework import serializers

from apps.students.models import Guardian, Student


class GuardianSerializer(serializers.ModelSerializer):
    relation_display = serializers.CharField(source="get_relation_display", read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Guardian
        fields = ("id", "user", "full_name", "relation", "relation_display", "phone", "alternate_phone",
                  "email", "occupation", "national_id", "address", "student_count",
                  "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "relation_display", "student_count", "created_at", "updated_at")

    def get_student_count(self, obj) -> int:
        return obj.students.filter(is_deleted=False).count()


class StudentListSerializer(serializers.ModelSerializer):
    """Compact shape for the student directory table."""

    class_name = serializers.CharField(source="school_class.name", read_only=True, default=None)
    section_name = serializers.CharField(source="section.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ("id", "student_id", "admission_number", "roll_number", "full_name", "photo_url",
                  "school_class", "class_name", "section", "section_name", "gender", "status",
                  "status_display", "admission_date", "is_active")
        read_only_fields = fields

    def get_photo_url(self, obj) -> str | None:
        if not obj.photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url


class StudentSerializer(serializers.ModelSerializer):
    """Full enrolment record."""

    class_name = serializers.CharField(source="school_class.name", read_only=True, default=None)
    section_name = serializers.CharField(source="section.name", read_only=True, default=None)
    session_name = serializers.CharField(source="session.name", read_only=True, default=None)
    guardian_detail = GuardianSerializer(source="guardian", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = (
            "id", "user", "student_id", "admission_number", "roll_number", "full_name", "full_name_bn",
            "photo", "photo_url", "date_of_birth", "gender", "blood_group", "birth_certificate_no", "religion",
            "school_class", "class_name", "section", "section_name", "session", "session_name",
            "guardian", "guardian_detail", "father_name", "mother_name", "emergency_contact",
            "admission_date", "status", "status_display", "present_address", "permanent_address",
            "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "class_name", "section_name", "session_name", "guardian_detail",
                            "status_display", "photo_url", "created_at", "updated_at")

    def get_photo_url(self, obj) -> str | None:
        if not obj.photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url

    def validate_student_id(self, value: str) -> str:
        return self._validate_unique("student_id", value, "A student with this ID already exists.")

    def validate_admission_number(self, value: str) -> str:
        return self._validate_unique("admission_number", value, "This admission number is already in use.")

    def _validate_unique(self, field: str, value: str, message: str) -> str:
        value = value.strip().upper()
        queryset = Student.objects.filter(**{f"{field}__iexact": value})
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(message)
        return value

    def validate(self, attrs):
        section = attrs.get("section", getattr(self.instance, "section", None))
        school_class = attrs.get("school_class", getattr(self.instance, "school_class", None))
        roll_number = attrs.get("roll_number", getattr(self.instance, "roll_number", None))

        if section and school_class and section.school_class_id != school_class.id:
            raise serializers.ValidationError(
                {"section": "The selected section does not belong to the selected class."}
            )

        if section and roll_number:
            clash = Student.objects.filter(section=section, roll_number=roll_number, is_deleted=False)
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError(
                    {"roll_number": "Another student in this section already has that roll number."}
                )
        return attrs
