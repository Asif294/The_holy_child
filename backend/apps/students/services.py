"""The enrolment codes and numbers the office issues: student ID, admission number, roll."""
from django.db.models import Max

from apps.common.identifiers import academic_year, next_code
from apps.students.models import Student

#: One wording per clash, shared by the serializer and the live check behind the
#: form, so the message a clerk sees while typing is the one they see on save.
IDENTIFIER_MESSAGES = {
    "student_id": "A student with this ID already exists.",
    "admission_number": "This admission number is already in use.",
}


def student_id_prefix() -> str:
    return f"THC-{academic_year()}-"


def admission_number_prefix() -> str:
    return f"ADM-{academic_year()}-"


def next_student_id() -> str:
    """e.g. ``THC-2026-0001``."""
    return next_code(Student, "student_id", student_id_prefix())


def next_admission_number() -> str:
    """e.g. ``ADM-2026-0001``."""
    return next_code(Student, "admission_number", admission_number_prefix())


def next_enrolment_identifiers() -> dict[str, str]:
    """Both codes the admission form pre-fills, in one call."""
    return {
        "student_id": next_student_id(),
        "admission_number": next_admission_number(),
    }


def identifier_clashes(values: dict, exclude=None) -> dict[str, str]:
    """
    Which of the given codes are already taken, as ``{field: message}``.

    Soft-deleted enrolments count: they still hold their code, and the database
    constraint that would reject a duplicate does not care that a row is
    deleted. Empty values are skipped — a blank field means "issue me one".
    """
    clashes = {}
    for field, message in IDENTIFIER_MESSAGES.items():
        value = (values.get(field) or "").strip()
        if not value:
            continue
        queryset = Student.objects.filter(**{f"{field}__iexact": value})
        if exclude:
            queryset = queryset.exclude(pk=exclude)
        if queryset.exists():
            clashes[field] = message
    return clashes


def next_roll_number(section_id) -> int:
    """
    The roll after the highest one in use in a section.

    Rolls are only unique *within* a section, so this is answered per section
    rather than school-wide. Soft-deleted enrolments are ignored here — unlike
    a student ID, the constraint on ``(section, roll_number)`` excludes them, so
    a pupil who has left frees their roll for the next arrival.
    """
    highest = (
        Student.objects.filter(section_id=section_id, is_deleted=False)
        .aggregate(highest=Max("roll_number"))["highest"]
    )
    return (highest or 0) + 1
