"""Reusable account operations kept out of the view layer."""
from django.db import transaction

from apps.accounts.constants import build_permission_catalogue
from apps.accounts.models import Permission, Role, User


@transaction.atomic
def sync_permissions() -> tuple[int, int]:
    """
    Make the ``permissions`` table match the code catalogue.

    Returns ``(created, updated)``. Permissions are never destroyed here — a code
    removed from the catalogue is deactivated so historical role assignments stay
    readable.
    """
    catalogue = build_permission_catalogue()
    existing = {permission.code: permission for permission in Permission.objects.all()}
    created = updated = 0

    for row in catalogue:
        permission = existing.get(row["code"])
        if permission is None:
            Permission.objects.create(**row)
            created += 1
            continue

        changed_fields = [
            field for field in ("name", "module", "module_label", "action", "group")
            if getattr(permission, field) != row[field]
        ]
        if not permission.is_active or permission.is_deleted:
            permission.is_active, permission.is_deleted = True, False
            changed_fields.append("is_active")
        if changed_fields:
            for field in ("name", "module", "module_label", "action", "group"):
                setattr(permission, field, row[field])
            permission.save()
            updated += 1

    retired_codes = set(existing) - {row["code"] for row in catalogue}
    if retired_codes:
        Permission.objects.filter(code__in=retired_codes).update(is_active=False)

    return created, updated


@transaction.atomic
def sync_roles(role_definitions: list[dict]) -> tuple[int, int]:
    """Create missing roles and refresh the permission set of system roles."""
    created = updated = 0
    for definition in role_definitions:
        role, was_created = Role.objects.get_or_create(
            slug=definition["slug"],
            defaults={
                "name": definition["name"],
                "description": definition["description"],
                "is_system": definition["is_system"],
            },
        )
        if was_created:
            created += 1
        else:
            role.name = definition["name"]
            role.description = definition["description"]
            role.is_system = definition["is_system"]
            role.is_active, role.is_deleted = True, False
            role.save()
            updated += 1
        role.set_permissions(definition["permissions"])
    return created, updated


def create_or_update_admin(email: str, password: str, full_name: str, role_slug: str) -> tuple[User, bool]:
    """Idempotently provision the bootstrap administrator account."""
    role = Role.objects.filter(slug=role_slug).first()
    user = User.objects.filter(email__iexact=email).first()
    if user:
        user.role = role or user.role
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        return user, False

    user = User.objects.create_superuser(email=email, password=password, full_name=full_name)
    if role:
        user.role = role
        user.save(update_fields=["role", "updated_at"])
    return user, True
