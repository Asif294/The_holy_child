from django.utils import timezone
from rest_framework import serializers

from apps.principal.models import ApprovalRequest, Notice, Principal


class PrincipalSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()
    signature_url = serializers.SerializerMethodField()
    user_email = serializers.CharField(source="user.email", read_only=True, default=None)
    teacher_employee_id = serializers.CharField(source="teacher.employee_id", read_only=True, default=None)

    class Meta:
        model = Principal
        fields = (
            "id", "user", "user_email", "teacher", "teacher_employee_id", "full_name", "designation",
            "email", "phone", "photo", "photo_url", "signature", "signature_url", "qualification",
            "experience_years", "message", "biography", "tenure_start", "tenure_end", "is_current",
            "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "user_email", "teacher_employee_id", "photo_url", "signature_url",
                            "created_at", "updated_at")

    def _absolute(self, field) -> str | None:
        if not field:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(field.url) if request else field.url

    def get_photo_url(self, obj) -> str | None:
        return self._absolute(obj.photo)

    def get_signature_url(self, obj) -> str | None:
        return self._absolute(obj.signature)

    def validate(self, attrs):
        start = attrs.get("tenure_start", getattr(self.instance, "tenure_start", None))
        end = attrs.get("tenure_end", getattr(self.instance, "tenure_end", None))
        if start and end and end < start:
            raise serializers.ValidationError({"tenure_end": "Tenure end cannot fall before tenure start."})
        return attrs


class PrincipalPublicSerializer(serializers.ModelSerializer):
    """The subset of the principal's record that is safe to show publicly."""

    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Principal
        fields = ("full_name", "designation", "qualification", "experience_years", "message", "photo_url")
        read_only_fields = fields

    def get_photo_url(self, obj) -> str | None:
        if not obj.photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url


class NoticeSerializer(serializers.ModelSerializer):
    issued_by_name = serializers.CharField(source="issued_by.full_name", read_only=True, default=None)
    audience_display = serializers.CharField(source="get_audience_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = (
            "id", "title", "body", "audience", "audience_display", "priority", "priority_display",
            "attachment", "attachment_url", "published_at", "expires_at", "is_published",
            "issued_by", "issued_by_name", "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "issued_by", "issued_by_name", "audience_display", "priority_display",
                            "attachment_url", "created_at", "updated_at")

    def get_attachment_url(self, obj) -> str | None:
        if not obj.attachment:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.attachment.url) if request else obj.attachment.url

    def validate(self, attrs):
        published_at = attrs.get("published_at", getattr(self.instance, "published_at", None))
        expires_at = attrs.get("expires_at", getattr(self.instance, "expires_at", None))
        if published_at and expires_at and expires_at <= published_at:
            raise serializers.ValidationError({"expires_at": "A notice must expire after it is published."})
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        if request is not None:
            validated_data["issued_by"] = request.user
        if validated_data.get("is_published") and not validated_data.get("published_at"):
            validated_data["published_at"] = timezone.now()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("is_published") and not (instance.published_at or validated_data.get("published_at")):
            validated_data["published_at"] = timezone.now()
        return super().update(instance, validated_data)


class ApprovalRequestSerializer(serializers.ModelSerializer):
    requested_by_name = serializers.CharField(source="requested_by.full_name", read_only=True, default=None)
    decided_by_name = serializers.CharField(source="decided_by.full_name", read_only=True, default=None)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = (
            "id", "title", "category", "category_display", "details", "attachment",
            "requested_by", "requested_by_name", "status", "status_display",
            "decided_by", "decided_by_name", "decided_at", "decision_note",
            "is_active", "created_at", "updated_at",
        )
        read_only_fields = ("id", "requested_by", "requested_by_name", "status", "status_display",
                            "decided_by", "decided_by_name", "decided_at", "decision_note",
                            "category_display", "created_at", "updated_at")

    def create(self, validated_data):
        request = self.context.get("request")
        if request is not None:
            validated_data["requested_by"] = request.user
        return super().create(validated_data)


class ApprovalDecisionSerializer(serializers.Serializer):
    """Body for approving or rejecting a request."""

    decision = serializers.ChoiceField(
        choices=[ApprovalRequest.Status.APPROVED, ApprovalRequest.Status.REJECTED],
        help_text="`approved` or `rejected`.",
    )
    note = serializers.CharField(required=False, allow_blank=True, max_length=1000)
