"""The staff code the office issues: the employee ID."""
from apps.common.identifiers import next_code
from apps.teachers.models import Teacher

#: Staff numbering does not restart each year — an employee ID follows the
#: person for as long as they are on the register.
EMPLOYEE_ID_PREFIX = "THC-T-"

#: Shared by the serializer and the live check behind the form, so the message
#: a clerk sees while typing is the one they see on save.
EMPLOYEE_ID_MESSAGE = "A teacher with this employee ID already exists."


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
