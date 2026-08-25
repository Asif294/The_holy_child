"""Small helpers shared between the user model, its serializers and the auth backend."""
import re


def normalise_phone(value: str) -> str:
    """Digits only, so ``+880 1700-000000`` and ``01700000000`` compare equal."""
    return re.sub(r"\D", "", value or "")


def clean_phone(value: str) -> str:
    """
    The form a phone number is stored in: no spaces, dashes or brackets, with a
    leading ``+`` kept when the caller supplied one.

    Storing a single canonical form is what lets the number be unique, and lets
    "the number I gave the office" match whatever the office typed in.
    """
    value = (value or "").strip()
    if not value:
        return ""
    digits = normalise_phone(value)
    return f"+{digits}" if value.startswith("+") else digits


def validate_phone_value(value: str, *, instance=None, required: bool = False) -> str:
    """
    Shared phone validation: shape, then uniqueness.

    Raises ``rest_framework.serializers.ValidationError`` so every serializer
    reports the same message for the same mistake, and so a duplicate number
    surfaces as a field error rather than a database ``IntegrityError``.
    """
    from rest_framework import serializers

    from apps.accounts.models import User

    value = clean_phone(value)
    if not value:
        if required:
            raise serializers.ValidationError("A phone number is required.")
        return ""

    digits = normalise_phone(value)
    if not (6 <= len(digits) <= 15):
        raise serializers.ValidationError("Enter a valid phone number (6–15 digits, optional leading '+').")

    queryset = User.objects.filter(phone=value)
    if instance is not None and instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    if queryset.exists():
        raise serializers.ValidationError("A user with this phone number already exists.")
    return value
