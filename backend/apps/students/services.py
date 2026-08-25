"""The enrolment codes the office issues: student ID and admission number."""
from apps.common.identifiers import academic_year, next_code
from apps.students.models import Student


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
