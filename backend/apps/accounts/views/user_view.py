from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.serializers import AssignRoleSerializer, UserSerializer, UserWriteSerializer
from apps.common.schema import DETAIL_RESPONSES, DETAIL_WRITE_RESPONSES, PROTECTED_RESPONSES, WRITE_RESPONSES
from apps.common.serializers import MessageResponseSerializer
from apps.common.viewsets import RBACModelViewSet


@extend_schema(tags=["Users"])
class UserViewSet(RBACModelViewSet):
    """
    User administration.

    Creating a user here *may* assign any role — the endpoint itself is gated
    behind `user.create`, so only an administrator ever reaches it. Public
    self-registration goes through `POST /api/v1/auth/register/`, which always
    applies the server-controlled default role instead.
    """

    permission_module = "user"
    permission_map = {"assign_role": "user.update"}
    serializer_class = UserSerializer
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    search_fields = ["full_name", "email", "username", "phone"]
    ordering_fields = ["full_name", "email", "created_at", "last_login"]
    ordering = ["-created_at"]
    filterset_fields = ["is_active", "role", "gender"]

    def get_queryset(self):
        return User.objects.filter(is_deleted=False).select_related("role").prefetch_related("role__permissions")

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return UserWriteSerializer
        if self.action == "assign_role":
            return AssignRoleSerializer
        return UserSerializer

    @extend_schema(
        summary="List users",
        description="Paginated directory of users. Filter by `role`, `is_active`, or search by name/email/phone.",
        parameters=[
            OpenApiParameter("role", int, description="Filter by role primary key."),
            OpenApiParameter("search", str, description="Search across name, email, username and phone."),
        ],
        responses={200: UserSerializer(many=True), **PROTECTED_RESPONSES},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a user",
        description="Creates a staff or student account and assigns the requested role.",
        request=UserWriteSerializer,
        responses={201: UserSerializer, **WRITE_RESPONSES},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(summary="Retrieve a user", responses={200: UserSerializer, **DETAIL_RESPONSES})
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(summary="Replace a user", request=UserWriteSerializer,
                   responses={200: UserSerializer, **DETAIL_WRITE_RESPONSES})
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="Partially update a user", request=UserWriteSerializer,
                   responses={200: UserSerializer, **DETAIL_WRITE_RESPONSES})
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Deactivate a user",
        description="Soft-deletes the account so historical records stay intact. A user cannot delete themselves.",
        responses={200: OpenApiResponse(response=MessageResponseSerializer, description="User deactivated."),
                   **DETAIL_WRITE_RESPONSES},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError({"detail": "You cannot delete your own account."})
        if instance.is_superuser and not self.request.user.is_superuser:
            raise ValidationError({"detail": "Only a superuser can remove another superuser."})
        instance.soft_delete()

    @extend_schema(
        summary="Assign a role to a user",
        description="Replaces the user's role. The new permission set applies to their next request.",
        request=AssignRoleSerializer,
        responses={200: UserSerializer, **DETAIL_WRITE_RESPONSES},
    )
    @action(detail=True, methods=["post"], url_path="assign-role")
    def assign_role(self, request, pk=None):
        user = self.get_object()
        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.role = serializer.validated_data["role_id"]
        user.save(update_fields=["role", "updated_at"])
        return Response(UserSerializer(user, context=self.get_serializer_context()).data)
