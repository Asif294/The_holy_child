from rest_framework import serializers

from apps.teachers.models import Department, Designation, Teacher


class DesignationSerializer(serializers.ModelSerializer):
    teacher_count = serializers.SerializerMethodField()

    class Meta:
        model = Designation
        fields = ("id", "name", "rank", "description", "teacher_count", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "teacher_count", "created_at", "updated_at")

    def get_teacher_count(self, obj) -> int:
        return obj.teachers.filter(is_deleted=False).count()


class DepartmentSerializer(serializers.ModelSerializer):
    head_name = serializers.CharField(source="head.full_name", read_only=True, default=None)
    teacher_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ("id", "name", "code", "head", "head_name", "description", "teacher_count",
                  "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "head_name", "teacher_count", "created_at", "updated_at")

    def get_teacher_count(self, obj) -> int:
        return obj.teachers.filter(is_deleted=False).count()


class TeacherListSerializer(serializers.ModelSerializer):
    """Compact shape for the staff directory."""

    designation_name = serializers.CharField(source="designation.name", read_only=True, default=None)
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ("id", "employee_id", "full_name", "email", "phone", "photo_url", "designation",
                  "designation_name", "department", "department_name", "status", "status_display",
                  "employment_type", "joining_date", "is_active")
        read_only_fields = fields

    def get_photo_url(self, obj) -> str | None:
        if not obj.photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url


class TeacherSerializer(serializers.ModelSerializer):
    """Full teacher record, including the subjects they are qualified to teach."""

    designation_name = serializers.CharField(source="designation.name", read_only=True, default=None)
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    photo_url = serializers.SerializerMethodField()
    subject_names = serializers.SerializerMethodField()
    sections_led = serializers.SerializerMethodField()
    user_email = serializers.CharField(source="user.email", read_only=True, default=None)

    class Meta:
        model = Teacher
        fields = (
            "id", "user", "user_email", "employee_id", "full_name", "email", "phone", "photo", "photo_url",
            "designation", "designation_name", "department", "department_name", "subjects", "subject_names",
            "sections_led", "employment_type", "status", "status_display", "joining_date", "resignation_date",
            "qualification", "specialization", "experience_years", "date_of_birth", "gender", "blood_group",
            "national_id", "address", "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "user_email", "designation_name", "department_name", "status_display",
                            "photo_url", "subject_names", "sections_led", "created_at", "updated_at")

    def get_photo_url(self, obj) -> str | None:
        if not obj.photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url

    def get_subject_names(self, obj) -> list[str]:
        return list(obj.subjects.values_list("name", flat=True))

    def get_sections_led(self, obj) -> list[str]:
        return [str(section) for section in obj.class_teacher_of.filter(is_deleted=False)]

    def validate_employee_id(self, value: str) -> str:
        value = value.strip().upper()
        queryset = Teacher.objects.filter(employee_id__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A teacher with this employee ID already exists.")
        return value

    def validate(self, attrs):
        joining = attrs.get("joining_date", getattr(self.instance, "joining_date", None))
        resignation = attrs.get("resignation_date", getattr(self.instance, "resignation_date", None))
        if joining and resignation and resignation < joining:
            raise serializers.ValidationError(
                {"resignation_date": "The resignation date cannot fall before the joining date."}
            )
        return attrs


class TeacherPublicSerializer(serializers.ModelSerializer):
    """
    The staff directory as a visitor sees it.

    Contact details, national ID, date of birth and employment terms are all
    deliberately absent: this is a "meet our teachers" card, not a personnel
    record. Email and phone are the school's published contacts for a teacher,
    so they are included only when the school itself filled them in.
    """

    designation_name = serializers.CharField(source="designation.name", read_only=True, default=None)
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    subject_names = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = (
            "id", "full_name", "designation_name", "department_name", "subject_names",
            "qualification", "specialization", "experience_years", "photo_url",
        )
        read_only_fields = fields

    def get_subject_names(self, obj) -> list[str]:
        return list(obj.subjects.values_list("name", flat=True))

    def get_photo_url(self, obj) -> str | None:
        if not obj.photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
