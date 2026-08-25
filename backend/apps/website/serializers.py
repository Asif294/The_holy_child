from rest_framework import serializers

from apps.common.serializers import MultipartModelSerializer
from apps.website.models import AboutSection, Achievement, HeroSlide, SuccessfulStudent


def absolute(serializer, image) -> str | None:
    """Build an absolute media URL when a request is in context, else a relative one."""
    if not image:
        return None
    request = serializer.context.get("request")
    return request.build_absolute_uri(image.url) if request else image.url


class HeroSlideSerializer(MultipartModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = HeroSlide
        fields = (
            "id", "title", "subtitle", "caption", "image", "image_url", "alt_text",
            "link_url", "link_label", "order", "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "image_url", "created_at", "updated_at")
        extra_kwargs = {"image": {"write_only": True}}

    def get_image_url(self, obj) -> str | None:
        return absolute(self, obj.image)


class HeroSlidePublicSerializer(serializers.ModelSerializer):
    """What an anonymous visitor sees — no internal flags or timestamps."""

    image_url = serializers.SerializerMethodField()

    class Meta:
        model = HeroSlide
        fields = ("id", "title", "subtitle", "caption", "image_url", "alt_text", "link_url", "link_label", "order")
        read_only_fields = fields

    def get_image_url(self, obj) -> str | None:
        return absolute(self, obj.image)


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ("id", "title", "description", "year", "metric", "order", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class AchievementPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ("id", "title", "description", "year", "metric")
        read_only_fields = fields


class AboutSectionSerializer(MultipartModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = AboutSection
        fields = (
            "id", "headline", "summary", "history", "mission", "vision", "motto",
            "image", "image_url", "updated_at",
        )
        read_only_fields = ("id", "image_url", "updated_at")
        extra_kwargs = {"image": {"write_only": True, "required": False, "allow_null": True}}

    def get_image_url(self, obj) -> str | None:
        return absolute(self, obj.image)


class AboutPublicSerializer(serializers.ModelSerializer):
    """The about copy plus the achievements that belong beside it."""

    image_url = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()

    class Meta:
        model = AboutSection
        fields = ("headline", "summary", "history", "mission", "vision", "motto", "image_url", "achievements")
        read_only_fields = fields

    def get_image_url(self, obj) -> str | None:
        return absolute(self, obj.image)

    def get_achievements(self, obj) -> list:
        queryset = Achievement.objects.filter(is_deleted=False, is_active=True)
        return AchievementPublicSerializer(queryset, many=True, context=self.context).data


class SuccessfulStudentSerializer(MultipartModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = SuccessfulStudent
        fields = (
            "id", "academic_year", "full_name", "student", "student_class", "section", "roll_number",
            "exam_name", "result", "gpa", "achievement", "photo", "photo_url", "remarks",
            "is_featured", "order", "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "photo_url", "created_at", "updated_at")
        extra_kwargs = {"photo": {"write_only": True, "required": False, "allow_null": True}}

    def get_photo_url(self, obj) -> str | None:
        return absolute(self, obj.photo)

    def validate_academic_year(self, value: str) -> str:
        value = value.strip()
        if not value.isdigit() or not (1900 <= int(value) <= 2200):
            raise serializers.ValidationError("Enter the academic year as a four-digit year, e.g. 2025.")
        return value


class SuccessfulStudentPublicSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = SuccessfulStudent
        fields = (
            "id", "academic_year", "full_name", "student_class", "section", "roll_number",
            "exam_name", "result", "gpa", "achievement", "photo_url", "remarks", "is_featured",
        )
        read_only_fields = fields

    def get_photo_url(self, obj) -> str | None:
        return absolute(self, obj.photo)
