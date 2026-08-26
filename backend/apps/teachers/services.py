"""Staff-side operations kept out of the view layer.

Two things happen when a teacher joins the register: they are issued an
employee ID, and — when there is enough on file to sign in with — a login
account.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.accounts.constants import ROLE_TEACHER
from apps.accounts.models import Role, User
from apps.accounts.utils import clean_phone, users_matching_phone
from apps.common.identifiers import next_code
from apps.teachers.models import Teacher

#: Staff numbering does not restart each year — an employee ID follows the
#: person for as long as they are on the register.
EMPLOYEE_ID_PREFIX = "THC-T-"

#: Shared by the serializer and the live check behind the form, so the message
#: a clerk sees while typing is the one they see on save.
EMPLOYEE_ID_MESSAGE = "A teacher with this employee ID already exists."

#: The role every auto-issued staff account is given.
ACCOUNT_ROLE_SLUG = ROLE_TEACHER


def next_employee_id() -> str:
    """e.g. ``THC-T-0001``."""
    return next_code(Teacher, "employee_id", EMPLOYEE_ID_PREFIX)


def employee_id_clash(value: str, exclude=None) -> str | None:
    """The clash message when ``value`` is already on the register, else ``None``."""
    value = (value or "").strip()
    if not value:
        return None

    queryset = Teacher.objects.filter(employee_id__iexact=value)
    if exclude:
        queryset = queryset.exclude(pk=exclude)
    return EMPLOYEE_ID_MESSAGE if queryset.exists() else None


def provision_account(teacher: Teacher) -> User | None:
    """
    The login account a teacher is given as they join the register.

    Their own email is the login identifier and their phone number is the first
    password — it is what the office reads out to them, and it is meant to be
    changed on first sign-in. The password validators that guard a
    self-chosen password are deliberately not applied to it: a phone number
    would fail every one of them, and this is a handover credential, not a
    password anyone chose.

    Without both an email and a phone number there is nothing to sign in with,
    so the teacher is recorded without an account — which the register has
    always allowed.

    An email already on file is adopted rather than duplicated, so a teacher
    who was a system user first keeps their account and their existing
    password. It is only an error when that account is already somebody else's
    staff record.
    """
    email = (teacher.email or "").strip().lower()
    password = clean_phone(teacher.phone)
    if not email or not password:
        return None

    existing = User.objects.filter(email__iexact=email).first()
    if existing is not None:
        owner = Teacher.objects.filter(user=existing).exclude(pk=teacher.pk).first()
        if owner is not None:
            raise serializers.ValidationError(
                {"email": f"This email already signs in as {owner.full_name} ({owner.employee_id})."}
            )
        return existing

    if users_matching_phone(teacher.phone):
        raise serializers.ValidationError({"phone": "A user with this phone number already exists."})

    fields = {
        "full_name": teacher.full_name,
        "phone": teacher.phone,
        "address": teacher.address,
        "role": Role.objects.filter(slug=ACCOUNT_ROLE_SLUG, is_deleted=False).first(),
    }
    if teacher.gender in User.Gender.values:
        fields["gender"] = teacher.gender
    if teacher.date_of_birth:
        fields["date_of_birth"] = teacher.date_of_birth

    try:
        return User.objects.create_user(email=email, password=password, **fields)
    except DjangoValidationError as exc:
        # Raised by ``full_clean`` inside ``create_user``; re-raised as a field
        # error so the staff form marks the offending box rather than showing a 500.
        raise serializers.ValidationError(exc.message_dict or {"detail": exc.messages}) from exc
