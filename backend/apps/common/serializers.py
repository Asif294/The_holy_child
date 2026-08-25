"""Serializer building blocks reused across the domain apps."""
from django.db import models
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.utils import html


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


class FormSafeBooleanField(serializers.BooleanField):
    """
    A boolean that treats "not sent" as "not sent", even in a multipart body.

    DRF's :class:`~rest_framework.fields.BooleanField` reads an absent key in
    an HTML form as ``False``, because an unticked checkbox sends nothing. That
    is right for a browser form and wrong for an API: a ``POST`` of
    ``multipart/form-data`` — the only way to upload a file — would set every
    boolean it did not mention to ``False``, so creating a record with a
    photograph attached would file it away deactivated.

    DRF already exempts partial updates from that rule, so only creates are
    affected. Here, absent means absent in both cases, and the model default
    applies. Everything else — parsing ``"true"``, blank handling, null
    handling — is left to the base class.
    """

    def get_value(self, dictionary):
        if html.is_html_input(dictionary) and self.field_name not in dictionary:
            return empty
        return super().get_value(dictionary)


class MultipartModelSerializer(serializers.ModelSerializer):
    """
    Base for any serializer behind an endpoint that accepts ``multipart/form-data``.

    Identical to :class:`~rest_framework.serializers.ModelSerializer` except
    that model booleans become :class:`FormSafeBooleanField`. Anything with a
    file field on it wants this base — see the docstring above for why.
    """

    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.BooleanField: FormSafeBooleanField,
    }
