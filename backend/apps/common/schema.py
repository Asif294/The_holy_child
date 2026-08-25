"""Shared drf-spectacular fragments so error documentation is written once."""
from drf_spectacular.utils import OpenApiExample, OpenApiResponse

from apps.common.serializers import ErrorResponseSerializer


def _error(description: str, message: str, code: str) -> OpenApiResponse:
    return OpenApiResponse(
        response=ErrorResponseSerializer,
        description=description,
        examples=[
            OpenApiExample(
                code,
                value={"success": False, "message": message, "code": code, "errors": {}},
                response_only=True,
            )
        ],
    )


UNAUTHORIZED = _error(
    "Missing or invalid JWT access token.",
    "Authentication credentials were not provided or are invalid.",
    "AUTHENTICATION_FAILED",
)

FORBIDDEN = _error(
    "Authenticated, but the user's role lacks the required permission code.",
    "You do not have permission to perform this action.",
    "PERMISSION_DENIED",
)

NOT_FOUND = _error(
    "The requested resource does not exist.",
    "The requested resource was not found.",
    "NOT_FOUND",
)

VALIDATION_ERROR = OpenApiResponse(
    response=ErrorResponseSerializer,
    description="One or more fields failed validation.",
    examples=[
        OpenApiExample(
            "VALIDATION_ERROR",
            value={
                "success": False,
                "message": "email: A user with this email already exists.",
                "code": "VALIDATION_ERROR",
                "errors": {"email": ["A user with this email already exists."]},
            },
            response_only=True,
        )
    ],
)

#: Attach to any protected endpoint: ``responses={**PROTECTED_RESPONSES, 200: ...}``
PROTECTED_RESPONSES = {401: UNAUTHORIZED, 403: FORBIDDEN}

#: Attach to write endpoints.
WRITE_RESPONSES = {401: UNAUTHORIZED, 403: FORBIDDEN, 422: VALIDATION_ERROR}

#: Attach to detail endpoints.
DETAIL_RESPONSES = {401: UNAUTHORIZED, 403: FORBIDDEN, 404: NOT_FOUND}

#: Attach to detail write endpoints.
DETAIL_WRITE_RESPONSES = {401: UNAUTHORIZED, 403: FORBIDDEN, 404: NOT_FOUND, 422: VALIDATION_ERROR}


def crud_schema(*, tag: str, resource: str, serializer, plural: str | None = None, descriptions: dict | None = None):
    """
    Decorator that documents the five standard CRUD actions of a ModelViewSet.

    Writing the same five ``@extend_schema`` blocks on every viewset is noise;
    this keeps the summaries, status codes and error responses consistent while
    still letting a viewset override any single action with its own decorator.

        @crud_schema(tag="Students", resource="student", serializer=StudentSerializer)
        class StudentViewSet(RBACModelViewSet):
            ...
    """
    from drf_spectacular.utils import extend_schema, extend_schema_view

    from apps.common.serializers import MessageResponseSerializer

    plural = plural or f"{resource}s"
    descriptions = descriptions or {}

    def described(action: str, fallback: str) -> str:
        return descriptions.get(action, fallback)

    return extend_schema_view(
        list=extend_schema(
            tags=[tag],
            summary=f"List {plural}",
            description=described(
                "list",
                f"Paginated list of {plural}. Supports `search`, `ordering`, `page`, `page_size` "
                f"and `paginated=false`. Requires the `{resource}.view` permission.",
            ),
            responses={200: serializer(many=True), **PROTECTED_RESPONSES},
        ),
        create=extend_schema(
            tags=[tag],
            summary=f"Create a {resource}",
            description=described("create", f"Requires the `{resource}.create` permission."),
            responses={201: serializer, **WRITE_RESPONSES},
        ),
        retrieve=extend_schema(
            tags=[tag],
            summary=f"Retrieve a {resource}",
            description=described("retrieve", f"Requires the `{resource}.view` permission."),
            responses={200: serializer, **DETAIL_RESPONSES},
        ),
        update=extend_schema(
            tags=[tag],
            summary=f"Replace a {resource}",
            description=described("update", f"Full update. Requires the `{resource}.update` permission."),
            responses={200: serializer, **DETAIL_WRITE_RESPONSES},
        ),
        partial_update=extend_schema(
            tags=[tag],
            summary=f"Partially update a {resource}",
            description=described("partial_update", f"Requires the `{resource}.update` permission."),
            responses={200: serializer, **DETAIL_WRITE_RESPONSES},
        ),
        destroy=extend_schema(
            tags=[tag],
            summary=f"Delete a {resource}",
            description=described(
                "destroy",
                f"Soft-deletes the record so history stays intact. Requires the `{resource}.delete` permission.",
            ),
            responses={
                200: OpenApiResponse(response=MessageResponseSerializer, description="Deleted."),
                **DETAIL_WRITE_RESPONSES,
            },
        ),
    )
