"""Small helpers shared between the user model, its serializers and the auth backend."""
import re

#: How many trailing digits identify a phone number.
#:
#: A Bangladeshi mobile is written both as ``01700000000`` and as
#: ``+8801700000000`` — same number, different digits. The last ten are the
#: part that never changes, so they are what we compare and what we check for
#: uniqueness. Ten digits is long enough that a collision between two genuinely
#: different numbers is not a practical concern.
PHONE_KEY_DIGITS = 10


def normalise_phone(value: str) -> str:
    """Digits only, so ``+880 1700-000000`` and ``01700000000`` compare equal."""
    return re.sub(r"\D", "", value or "")


def phone_key(value: str) -> str:
    """
    The comparable identity of a phone number.

    Two numbers are the same number when their keys match, whether or not the
    person typed a country code. Numbers shorter than
    :data:`PHONE_KEY_DIGITS` are compared whole.
    """
    digits = normalise_phone(value)
    return digits[-PHONE_KEY_DIGITS:] if len(digits) > PHONE_KEY_DIGITS else digits


def clean_phone(value: str) -> str:
    """
    The form a phone number is stored in: no spaces, dashes or brackets, with a
    leading ``+`` kept when the caller supplied one.

    The stored string keeps whatever the office typed — it is what gets printed
    on a form — while :func:`phone_key` is what decides identity.
    """
    value = (value or "").strip()
    if not value:
        return ""
    digits = normalise_phone(value)
    return f"+{digits}" if value.startswith("+") else digits


def users_matching_phone(value: str, *, exclude_pk=None):
    """
    Every user whose number is the same number as ``value``.

    The ``endswith`` filter only narrows the scan — formatting differs between
    records, so the key comparison in Python is what actually decides.
    """
    from apps.accounts.models import User

    key = phone_key(value)
    if len(key) < 6:
        return []

    queryset = User.objects.filter(phone__endswith=key[-6:]).select_related("role")
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    return [user for user in queryset if phone_key(user.phone) == key]


def validate_phone_value(value: str, *, instance=None, required: bool = False) -> str:
    """
    Shared phone validation: shape, then uniqueness.

    Raises ``rest_framework.serializers.ValidationError`` so every serializer
    reports the same message for the same mistake, and so a duplicate number
    surfaces as a field error rather than a database ``IntegrityError``.

    Uniqueness is checked on :func:`phone_key`, not on the stored string:
    letting one person register ``01700000000`` and another ``+8801700000000``
    would make the number useless as a login identifier for both of them.
    """
    from rest_framework import serializers

    value = clean_phone(value)
    if not value:
        if required:
            raise serializers.ValidationError("A phone number is required.")
        return ""

    digits = normalise_phone(value)
    if not (6 <= len(digits) <= 15):
        raise serializers.ValidationError("Enter a valid phone number (6–15 digits, optional leading '+').")

    exclude_pk = instance.pk if instance is not None and instance.pk else None
    if users_matching_phone(value, exclude_pk=exclude_pk):
        raise serializers.ValidationError("A user with this phone number already exists.")
    return value
