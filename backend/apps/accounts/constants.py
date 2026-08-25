"""
The catalogue of granular permission codes and the default role definitions.

This module is the single source of truth consumed by ``seed_initial_data``.
Adding a module here and re-running the seed is all it takes to extend the
permission surface — no code elsewhere needs to change.
"""

# --------------------------------------------------------------------------- #
# Permission groups (used to organise the permission-matrix UI)
# --------------------------------------------------------------------------- #
GROUP_ACADEMICS = "Academics"
GROUP_ADMINISTRATION = "Administration"
GROUP_FINANCE = "Finance"
GROUP_REPORTS = "Reports"
GROUP_SYSTEM = "System"

CRUD = (
    ("view", "View"),
    ("create", "Create"),
    ("update", "Update"),
    ("delete", "Delete"),
)

#: module -> (label, group, actions)
PERMISSION_MODULES: dict[str, dict] = {
    "student": {"label": "Students", "group": GROUP_ACADEMICS, "actions": CRUD},
    "teacher": {"label": "Teachers", "group": GROUP_ACADEMICS, "actions": CRUD},
    "class": {"label": "Classes", "group": GROUP_ACADEMICS, "actions": CRUD},
    "subject": {"label": "Subjects", "group": GROUP_ACADEMICS, "actions": CRUD},
    "attendance": {"label": "Attendance", "group": GROUP_ACADEMICS, "actions": CRUD},
    "exam": {"label": "Exams", "group": GROUP_ACADEMICS, "actions": CRUD},
    "result": {"label": "Results", "group": GROUP_ACADEMICS, "actions": CRUD + (("publish", "Publish"),)},
    "admission": {"label": "Admissions", "group": GROUP_ADMINISTRATION, "actions": CRUD},
    "notice": {"label": "Notices", "group": GROUP_ADMINISTRATION, "actions": CRUD},
    "content": {
        "label": "Website Content",
        "group": GROUP_ADMINISTRATION,
        "actions": CRUD,
    },
    "achiever": {
        "label": "Successful Students",
        "group": GROUP_ADMINISTRATION,
        "actions": CRUD,
    },
    "principal": {
        "label": "Principal Office",
        "group": GROUP_ADMINISTRATION,
        "actions": (
            ("view", "View"),
            ("update", "Update"),
            ("approve", "Approve requests"),
        ),
    },
    "fee": {"label": "Fees", "group": GROUP_FINANCE, "actions": CRUD},
    "payment": {"label": "Payments", "group": GROUP_FINANCE, "actions": CRUD},
    "report": {
        "label": "Reports",
        "group": GROUP_REPORTS,
        "actions": (("view", "View"), ("export", "Export")),
    },
    "dashboard": {"label": "Dashboard", "group": GROUP_SYSTEM, "actions": (("view", "View"),)},
    "user": {"label": "Users", "group": GROUP_SYSTEM, "actions": CRUD},
    "role": {"label": "Roles", "group": GROUP_SYSTEM, "actions": CRUD},
    "permission": {"label": "Permissions", "group": GROUP_SYSTEM, "actions": (("view", "View"),)},
    "setting": {
        "label": "Settings",
        "group": GROUP_SYSTEM,
        "actions": (("view", "View"), ("update", "Update")),
    },
}


def build_permission_catalogue() -> list[dict]:
    """Flatten :data:`PERMISSION_MODULES` into row dicts ready for bulk creation."""
    catalogue: list[dict] = []
    for module, meta in PERMISSION_MODULES.items():
        for action, action_label in meta["actions"]:
            catalogue.append(
                {
                    "code": f"{module}.{action}",
                    "name": f"{action_label} {meta['label']}",
                    "module": module,
                    "module_label": meta["label"],
                    "action": action,
                    "group": meta["group"],
                }
            )
    return catalogue


ALL_PERMISSION_CODES: list[str] = [row["code"] for row in build_permission_catalogue()]


def codes_for(*modules: str) -> list[str]:
    """Every code belonging to the given modules."""
    return [code for code in ALL_PERMISSION_CODES if code.split(".", 1)[0] in modules]


# --------------------------------------------------------------------------- #
# Role slugs
# --------------------------------------------------------------------------- #
ROLE_SUPER_ADMIN = "super-admin"
ROLE_SCHOOL_ADMIN = "school-admin"
ROLE_PRINCIPAL = "principal"
ROLE_TEACHER = "teacher"
ROLE_ACCOUNTANT = "accountant"
ROLE_RECEPTIONIST = "receptionist"
ROLE_STUDENT = "student"
ROLE_PARENT = "parent"

#: The role assigned to self-registered users. Privileged roles can only be
#: granted by an administrator through the user-management APIs.
DEFAULT_SELF_REGISTRATION_ROLE = ROLE_STUDENT

#: Roles a self-registering user may never assign to themselves.
PROTECTED_ROLE_SLUGS = {
    ROLE_SUPER_ADMIN,
    ROLE_SCHOOL_ADMIN,
    ROLE_PRINCIPAL,
    ROLE_ACCOUNTANT,
    ROLE_RECEPTIONIST,
    ROLE_TEACHER,
}

#: System roles cannot be renamed or deleted through the API.
SYSTEM_ROLE_SLUGS = {ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN}

DEFAULT_ROLES: list[dict] = [
    {
        "name": "Super Admin",
        "slug": ROLE_SUPER_ADMIN,
        "description": "Unrestricted access to every module and system setting.",
        "is_system": True,
        "permissions": ALL_PERMISSION_CODES,
    },
    {
        "name": "School Admin",
        "slug": ROLE_SCHOOL_ADMIN,
        "description": "Runs day-to-day school operations across every academic and finance module.",
        "is_system": True,
        "permissions": codes_for(
            "student", "teacher", "class", "subject", "attendance", "exam", "result",
            "admission", "notice", "fee", "payment", "report", "dashboard", "user", "principal",
            "content", "achiever",
        ) + ["setting.view", "role.view", "permission.view"],
    },
    {
        "name": "Principal",
        "slug": ROLE_PRINCIPAL,
        "description": "Head of institution: full academic oversight, approvals and notices.",
        "is_system": False,
        "permissions": codes_for("principal", "notice", "report", "dashboard", "content", "achiever")
        + [
            "student.view", "student.create", "student.update",
            "teacher.view", "teacher.create", "teacher.update",
            "class.view", "subject.view", "attendance.view",
            "exam.view", "exam.create", "exam.update",
            "result.view", "result.publish",
            "fee.view", "payment.view", "admission.view", "user.view",
        ],
    },
    {
        "name": "Teacher",
        "slug": ROLE_TEACHER,
        "description": "Classroom staff: takes attendance, records marks and views their classes.",
        "is_system": False,
        "permissions": [
            "dashboard.view",
            "student.view",
            "class.view",
            "subject.view",
            "attendance.view", "attendance.create", "attendance.update",
            "exam.view",
            "result.view", "result.create", "result.update",
            "notice.view",
            "content.view", "achiever.view",
        ],
    },
    {
        "name": "Accountant",
        "slug": ROLE_ACCOUNTANT,
        "description": "Manages fee structures, invoices, payments and financial reports.",
        "is_system": False,
        "permissions": codes_for("fee", "payment")
        + ["dashboard.view", "student.view", "class.view", "report.view", "report.export", "notice.view"],
    },
    {
        "name": "Receptionist",
        "slug": ROLE_RECEPTIONIST,
        "description": "Front desk: admissions intake and student directory.",
        "is_system": False,
        "permissions": [
            "dashboard.view",
            "student.view", "student.create", "student.update",
            "admission.view", "admission.create", "admission.update",
            "class.view", "teacher.view", "notice.view",
        ],
    },
    {
        "name": "Student",
        "slug": ROLE_STUDENT,
        "description": "Read-only access to their own academic information.",
        "is_system": False,
        "permissions": [
            "dashboard.view", "class.view", "subject.view",
            "attendance.view", "exam.view", "result.view", "fee.view", "notice.view",
        ],
    },
    {
        "name": "Parent",
        "slug": ROLE_PARENT,
        "description": "Read-only access to their children's academic and fee information.",
        "is_system": False,
        "permissions": [
            "dashboard.view", "attendance.view", "exam.view",
            "result.view", "fee.view", "payment.view", "notice.view",
        ],
    },
]
