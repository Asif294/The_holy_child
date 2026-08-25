"""
Reusable DRF permission classes backed by granular permission codes.

Nothing in this project branches on a role *name* — authorisation is always a
question of "does this user hold permission code X?", which is what makes roles
freely creatable at runtime.

Usage
-----
Single code::

    class StudentViewSet(ModelViewSet):
        permission_classes = [IsAuthenticated, HasPermission]
        required_permission = "student.view"

Per-action codes (the common case for CRUD)::

    class StudentViewSet(RBACModelViewSet):
        permission_module = "student"   # -> student.view / create / update / delete

Any / all semantics::

    permission_classes = [IsAuthenticated, HasAnyPermission]
    required_permissions = ["report.view", "report.export"]
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

# Maps a ViewSet action to the CRUD verb used in permission codes.
ACTION_TO_VERB = {
    "list": "view",
    "retrieve": "view",
    "create": "create",
    "update": "update",
    "partial_update": "update",
    "destroy": "delete",
}

# Fallback for plain APIViews that have no ``action``.
METHOD_TO_VERB = {
    "GET": "view",
    "HEAD": "view",
    "OPTIONS": "view",
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}


def user_permission_codes(user) -> set[str]:
    """All permission codes held by ``user`` (empty set when anonymous)."""
    if not user or not user.is_authenticated:
        return set()
    return user.get_permission_codes()


class _BaseCodePermission(BasePermission):
    message = "You do not have permission to perform this action."

    def _required(self, request, view) -> list[str]:
        raise NotImplementedError

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        required = [code for code in self._required(request, view) if code]
        if not required:
            # No code declared on the view: authentication alone is enough.
            return True
        return self._matches(set(required), user_permission_codes(user))

    @staticmethod
    def _matches(required: set[str], held: set[str]) -> bool:
        raise NotImplementedError


class HasPermission(_BaseCodePermission):
    """Requires the single code in ``view.required_permission``."""

    def _required(self, request, view):
        return [getattr(view, "required_permission", None)]

    @staticmethod
    def _matches(required, held):
        return required.issubset(held)


class HasAllPermissions(_BaseCodePermission):
    """Requires every code in ``view.required_permissions``."""

    def _required(self, request, view):
        return list(getattr(view, "required_permissions", []) or [])

    @staticmethod
    def _matches(required, held):
        return required.issubset(held)


class HasAnyPermission(_BaseCodePermission):
    """Requires at least one code in ``view.required_permissions``."""

    def _required(self, request, view):
        return list(getattr(view, "required_permissions", []) or [])

    @staticmethod
    def _matches(required, held):
        return bool(required & held)


class HasActionPermission(_BaseCodePermission):
    """
    Resolves the required code from the current action.

    Looks up ``view.permission_map`` first (explicit per-action overrides), then
    falls back to ``f"{view.permission_module}.{verb}"``.
    """

    def _required(self, request, view):
        action = getattr(view, "action", None)
        permission_map = getattr(view, "permission_map", None) or {}

        if action and action in permission_map:
            code = permission_map[action]
            return code if isinstance(code, (list, tuple)) else [code]

        module = getattr(view, "permission_module", None)
        if not module:
            return []

        verb = ACTION_TO_VERB.get(action) or METHOD_TO_VERB.get(request.method, "view")
        return [f"{module}.{verb}"]

    @staticmethod
    def _matches(required, held):
        return required.issubset(held)


def permission_required(*codes: str, require_all: bool = True) -> type[BasePermission]:
    """
    Build an inline permission class for one-off views::

        permission_classes = [IsAuthenticated, permission_required("report.export")]
    """
    base = HasAllPermissions if require_all else HasAnyPermission

    class _Inline(base):  # type: ignore[valid-type,misc]
        def _required(self, request, view):
            return list(codes)

    _Inline.__name__ = f"Requires{'All' if require_all else 'Any'}_{'_'.join(codes)}"
    return _Inline


class IsSuperAdmin(BasePermission):
    """Reserved for destructive system-level operations."""

    message = "This action is restricted to super administrators."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_super_admin))


class IsSelfOrHasPermission(HasActionPermission):
    """
    Lets a user act on their own record without holding the code, while still
    requiring the code for anybody else's record.
    """

    def has_permission(self, request, view):
        # Object-level check does the real work; allow the request through.
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        owner_id = getattr(obj, "user_id", None) or getattr(obj, "id", None)
        if user.is_superuser or owner_id == user.id:
            return True
        return super().has_permission(request, view)


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
