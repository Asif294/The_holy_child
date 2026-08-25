"""Base viewsets that wire RBAC, soft-delete and the response envelope together."""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.common.models import BaseModel
from apps.common.permissions import HasActionPermission


class RBACMixin:
    """
    Declares the permission code family a view belongs to.

    Set ``permission_module = "student"`` and the view automatically requires
    ``student.view`` / ``student.create`` / ``student.update`` / ``student.delete``
    for the matching actions. Individual actions can be overridden through
    ``permission_map``.
    """

    permission_module: str | None = None
    permission_map: dict[str, str] | None = None
    permission_classes = [IsAuthenticated, HasActionPermission]


class SoftDeleteMixin:
    """DELETE marks the row inactive rather than removing it."""

    def perform_destroy(self, instance):
        if isinstance(instance, BaseModel):
            instance.soft_delete()
        else:
            instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"success": True, "message": "Deleted successfully."},
            status=status.HTTP_200_OK,
        )


class RBACModelViewSet(RBACMixin, SoftDeleteMixin, ModelViewSet):
    """Full CRUD viewset with permission-code enforcement and soft delete."""

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get("include_inactive", "false").lower() in {"true", "1", "yes"}:
            return queryset
        return queryset.filter(is_deleted=False)


class RBACReadOnlyViewSet(RBACMixin, ReadOnlyModelViewSet):
    """List/retrieve only, still permission-gated."""
