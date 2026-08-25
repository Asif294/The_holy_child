from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.constants import SYSTEM_ROLE_SLUGS
from apps.accounts.models import Role
from apps.accounts.serializers import RoleListSerializer, RoleSerializer
from apps.common.schema import DETAIL_RESPONSES, DETAIL_WRITE_RESPONSES, PROTECTED_RESPONSES, WRITE_RESPONSES
from apps.common.serializers import MessageResponseSerializer
from apps.common.viewsets import RBACModelViewSet

ROLE_REQUEST_EXAMPLE = OpenApiExample(
    "Create the Teacher role",
    value={
        "name": "Teacher",
        "description": "Classroom staff.",
        "permissions": ["student.view", "attendance.view", "attendance.create", "class.view"],
    },
    request_only=True,
)


@extend_schema(tags=["Roles"])
class RoleViewSet(RBACModelViewSet):
    """
    Dynamic role management.

    A role is nothing more than a named bundle of permission codes, so new roles
    can be invented at runtime without touching the codebase. Assign the role to
    a user and their access — and the navigation the frontend renders — changes
    immediately.
    """

    permission_module = "role"
    # Swapping a role's permission set is an update, not a create.
    permission_map = {"set_permissions": "role.update"}
    serializer_class = RoleSerializer
    search_fields = ["name", "slug", "description"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["name"]
    filterset_fields = ["is_active", "is_system"]

    def get_queryset(self):
        return (
            Role.objects.filter(is_deleted=False)
            .prefetch_related("permissions")
            .annotate(
                permission_count=Count("permissions", distinct=True),
                user_count=Count("users", filter=Q(users__is_deleted=False), distinct=True),
            )
        )

    def get_serializer_class(self):
        return RoleListSerializer if self.action == "list" else RoleSerializer

    @extend_schema(
        summary="List roles",
        description="Paginated list of roles with their permission and user counts. "
                    "Pass `?paginated=false` to fetch every role (useful for dropdowns).",
        responses={200: RoleListSerializer(many=True), **PROTECTED_RESPONSES},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a role",
        description="Creates a role and assigns the given permission codes in one call.",
        request=RoleSerializer,
        responses={201: RoleSerializer, **WRITE_RESPONSES},
        examples=[ROLE_REQUEST_EXAMPLE],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a role",
        description="Returns the role with its permission codes and expanded permission objects.",
        responses={200: RoleSerializer, **DETAIL_RESPONSES},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Replace a role",
        description="Full update. Supplying `permissions` replaces the role's entire permission set.",
        responses={200: RoleSerializer, **DETAIL_WRITE_RESPONSES},
        examples=[ROLE_REQUEST_EXAMPLE],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Partially update a role",
        description="Patch selected fields. Omitting `permissions` leaves the existing set untouched.",
        responses={200: RoleSerializer, **DETAIL_WRITE_RESPONSES},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete a role",
        description=(
            "Soft-deletes the role. System roles and roles still assigned to users "
            "cannot be deleted — reassign those users first."
        ),
        responses={200: OpenApiResponse(response=MessageResponseSerializer, description="Role deleted."),
                   **DETAIL_WRITE_RESPONSES},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        if instance.is_system or instance.slug in SYSTEM_ROLE_SLUGS:
            raise ValidationError({"detail": "System roles cannot be deleted."})
        if instance.users.filter(is_deleted=False).exists():
            raise ValidationError(
                {"detail": "This role is still assigned to one or more users. Reassign them before deleting."}
            )
        instance.soft_delete()

    @extend_schema(
        summary="Replace a role's permissions",
        description="Convenience endpoint that swaps the role's permission set without touching its other fields.",
        request={"application/json": {"type": "object", "properties": {
            "permissions": {"type": "array", "items": {"type": "string"}, "example": ["student.view", "class.view"]}
        }, "required": ["permissions"]}},
        responses={200: RoleSerializer, **DETAIL_WRITE_RESPONSES},
    )
    @action(detail=True, methods=["post"], url_path="permissions")
    def set_permissions(self, request, pk=None):
        role = self.get_object()
        codes = request.data.get("permissions")
        if not isinstance(codes, list):
            raise ValidationError({"permissions": "Expected a list of permission codes."})
        if role.slug == "super-admin":
            raise ValidationError({"permissions": "The Super Admin role always holds every permission."})
        role.set_permissions(codes)
        return Response(RoleSerializer(role, context=self.get_serializer_context()).data)
