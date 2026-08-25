"""Serializer building blocks reused across the domain apps."""
from rest_framework import serializers


class TimestampedSerializer(serializers.ModelSerializer):
    """Adds the audit columns as read-only fields to any ``BaseModel`` serializer."""

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        abstract = True
        read_only_fields = ("id", "created_at", "updated_at", "created_by", "updated_by")


class ErrorResponseSerializer(serializers.Serializer):
    """Documents the project-wide error envelope in the OpenAPI schema."""

    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    code = serializers.CharField()
    errors = serializers.DictField(required=False)


class MessageResponseSerializer(serializers.Serializer):
    """Documents a simple `{success, message}` response."""

    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
