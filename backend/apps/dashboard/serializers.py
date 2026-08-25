from rest_framework import serializers

from apps.dashboard.models import ActivityLog, SchoolEvent, SchoolProfile


class SchoolEventSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = SchoolEvent
        fields = ("id", "title", "description", "category", "category_display", "start_date",
                  "end_date", "start_time", "venue", "is_holiday", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "category_display", "created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "An event cannot end before it starts."})
        return attrs


class ActivityLogSerializer(serializers.ModelSerializer):
    actor_display = serializers.SerializerMethodField()
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = ActivityLog
        fields = ("id", "actor", "actor_display", "action", "action_display", "module",
                  "description", "object_id", "created_at")
        read_only_fields = fields

    def get_actor_display(self, obj) -> str:
        if obj.actor_id and obj.actor:
            return obj.actor.full_name
        return obj.actor_name or "System"


class StatCardSerializer(serializers.Serializer):
    """One headline number on the dashboard."""

    key = serializers.CharField()
    label = serializers.CharField()
    value = serializers.CharField()
    change = serializers.FloatField(required=False, allow_null=True)


class DashboardSummarySerializer(serializers.Serializer):
    """Documents the payload of ``GET /api/v1/dashboard/summary/``."""

    total_students = serializers.IntegerField()
    total_teachers = serializers.IntegerField()
    total_classes = serializers.IntegerField()
    total_subjects = serializers.IntegerField()
    todays_attendance_rate = serializers.FloatField()
    todays_present = serializers.IntegerField()
    todays_absent = serializers.IntegerField()
    pending_fees = serializers.DecimalField(max_digits=12, decimal_places=2)
    collected_fees = serializers.DecimalField(max_digits=12, decimal_places=2)
    upcoming_exams = serializers.IntegerField()
    pending_approvals = serializers.IntegerField()


class SchoolInfoSerializer(serializers.Serializer):
    """Documents the public ``GET /api/v1/school/info/`` payload."""

    name_en = serializers.CharField()
    name_bn = serializers.CharField()
    short_name = serializers.CharField()
    address = serializers.CharField()
    village = serializers.CharField()
    upazila = serializers.CharField()
    district = serializers.CharField()
    country = serializers.CharField()
    established = serializers.CharField()
    grade_range = serializers.CharField()
    grade_range_bn = serializers.CharField()
    brand_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    website = serializers.CharField(allow_blank=True)
    logo_url = serializers.CharField(allow_null=True)
    stats = serializers.DictField()


class SchoolProfileSerializer(serializers.ModelSerializer):
    """
    Read/write view of the singleton profile, used by the Settings screen.

    ``address`` is derived from the four location parts rather than stored, so
    it is exposed read-only — editing it would have nowhere to go.
    """

    address = serializers.CharField(read_only=True)
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = SchoolProfile
        fields = (
            "id", "name_en", "name_bn", "short_name", "brand_name",
            "village", "upazila", "district", "country", "address",
            "established", "grade_range", "grade_range_bn",
            "email", "phone", "website",
            "logo", "logo_url", "updated_at",
        )
        read_only_fields = ("id", "address", "logo_url", "updated_at")
        extra_kwargs = {"logo": {"write_only": True, "required": False, "allow_null": True}}

    def get_logo_url(self, obj) -> str | None:
        if not obj.logo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url

    def validate_name_en(self, value):
        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError("The school needs a name.")
        return value
