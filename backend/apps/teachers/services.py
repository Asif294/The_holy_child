"""The staff code the office issues: the employee ID."""
from apps.common.identifiers import next_code
from apps.teachers.models import Teacher

#: Staff numbering does not restart each year — an employee ID follows the
#: person for as long as they are on the register.
EMPLOYEE_ID_PREFIX = "THC-T-"


def next_employee_id() -> str:
    """e.g. ``THC-T-0001``."""
    return next_code(Teacher, "employee_id", EMPLOYEE_ID_PREFIX)
