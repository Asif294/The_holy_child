from collections import OrderedDict

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Permission
from apps.accounts.serializers import PermissionSerializer
from apps.common.schema import PROTECTED_RESPONSES
from apps.common.viewsets import RBACReadOnlyViewSet


@extend_schema(tags=["Permissions"])
class PermissionViewSet(RBACReadOnlyViewSet):
    """
    Read-only catalogue of every granular capability the platform understands.

    Permissions describe what the software *can* do and are seeded from code;
    roles decide who may do it. The `grouped` action returns the same catalogue
    shaped for the permission-matrix UI.
    """

    permission_module = "permission"
    serializer_class = PermissionSerializer
    queryset = Permission.objects.filter(is_deleted=False)
    search_fields = ["code", "name", "module", "module_label"]
    ordering_fields = ["code", "module", "group"]
    ordering = ["group", "module", "action"]
    filterset_fields = ["module", "action", "group"]
    pagination_class = None

    @extend_schema(
        summary="List permissions",
        description="Every permission code, optionally filtered by `module`, `action` or `group`.",
        parameters=[
            OpenApiParameter("module", str, description="Filter by resource family, e.g. `student`."),
            OpenApiParameter("group", str, description="Filter by UI group, e.g. `Academics`."),
        ],
        responses={200: PermissionSerializer(many=True), **PROTECTED_RESPONSES},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a permission",
        responses={200: PermissionSerializer, **PROTECTED_RESPONSES},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Permissions grouped for the role matrix",
        description=(
            "Returns permissions nested as `group -> module -> permissions`, which is "
            "exactly the layout the role editor renders as a checkbox matrix."
        ),
        responses={
            200: OpenApiResponse(
                description="Nested permission catalogue.",
                examples=[
                    OpenApiExample(
                        "Grouped permissions",
                        value=[
                            {
                                "group": "Academics",
                                "modules": [
                                    {
                                        "module": "student",
                                        "label": "Students",
                                        "permissions": [
                                            {"id": 1, "code": "student.view", "name": "View Students", "action": "view"}
                                        ],
                                    }
                                ],
                            }
                        ],
                        response_only=True,
                    )
                ],
            ),
            **PROTECTED_RESPONSES,
        },
    )
    @action(detail=False, methods=["get"], url_path="grouped")
    def grouped(self, request):
        grouped: "OrderedDict[str, OrderedDict[str, dict]]" = OrderedDict()
        for permission in self.filter_queryset(self.get_queryset()):
            modules = grouped.setdefault(permission.group, OrderedDict())
            module = modules.setdefault(
                permission.module,
                {"module": permission.module, "label": permission.module_label or permission.module, "permissions": []},
            )
            module["permissions"].append(
                {
                    "id": permission.id,
                    "code": permission.code,
                    "name": permission.name,
                    "action": permission.action,
                }
            )
        payload = [{"group": group, "modules": list(modules.values())} for group, modules in grouped.items()]
        return Response(payload)
