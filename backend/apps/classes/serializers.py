from rest_framework import serializers

from apps.classes.models import AcademicSession, SchoolClass, Section


class AcademicSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicSession
        fields = ("id", "name", "start_date", "end_date", "is_current", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and start >= end:
            raise serializers.ValidationError({"end_date": "The session end date must fall after its start date."})
        return attrs


class SectionBriefSerializer(serializers.ModelSerializer):
    enrolled_count = serializers.IntegerField(read_only=True)
    seats_available = serializers.IntegerField(read_only=True)
    class_teacher_name = serializers.CharField(source="class_teacher.full_name", read_only=True, default=None)

    class Meta:
        model = Section
        fields = ("id", "name", "capacity", "room_number", "class_teacher", "class_teacher_name",
                  "enrolled_count", "seats_available")
        read_only_fields = ("id", "enrolled_count", "seats_available", "class_teacher_name")


class SchoolClassSerializer(serializers.ModelSerializer):
    sections = SectionBriefSerializer(many=True, read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    section_count = serializers.SerializerMethodField()

    class Meta:
        model = SchoolClass
        fields = ("id", "name", "name_bn", "code", "order", "description", "sections",
                  "section_count", "student_count", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "sections", "section_count", "student_count", "created_at", "updated_at")

    def get_section_count(self, obj) -> int:
        return obj.sections.filter(is_deleted=False).count()

    def validate_code(self, value: str) -> str:
        value = value.strip().upper()
        queryset = SchoolClass.objects.filter(code__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A class with this code already exists.")
        return value


class SectionSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source="school_class.name", read_only=True)
    class_teacher_name = serializers.CharField(source="class_teacher.full_name", read_only=True, default=None)
    enrolled_count = serializers.IntegerField(read_only=True)
    seats_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Section
        fields = ("id", "school_class", "class_name", "name", "capacity", "room_number",
                  "class_teacher", "class_teacher_name", "enrolled_count", "seats_available",
                  "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "class_name", "class_teacher_name", "enrolled_count",
                            "seats_available", "created_at", "updated_at")

    def validate(self, attrs):
        school_class = attrs.get("school_class", getattr(self.instance, "school_class", None))
        name = attrs.get("name", getattr(self.instance, "name", None))
        queryset = Section.objects.filter(school_class=school_class, name__iexact=name, is_deleted=False)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError({"name": "This class already has a section with that name."})
        return attrs
