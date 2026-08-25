"""
A single place that turns any raised exception into the project's error envelope:

    {
        "success": false,
        "message": "You do not have permission to perform this action.",
        "code": "PERMISSION_DENIED",
        "errors": {}
    }
"""
import logging

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

STATUS_CODE_MAP = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "AUTHENTICATION_FAILED",
    status.HTTP_403_FORBIDDEN: "PERMISSION_DENIED",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "UNSUPPORTED_MEDIA_TYPE",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
    status.HTTP_429_TOO_MANY_REQUESTS: "THROTTLED",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
}

DEFAULT_MESSAGES = {
    status.HTTP_400_BAD_REQUEST: "The request could not be processed.",
    status.HTTP_401_UNAUTHORIZED: "Authentication credentials were not provided or are invalid.",
    status.HTTP_403_FORBIDDEN: "You do not have permission to perform this action.",
    status.HTTP_404_NOT_FOUND: "The requested resource was not found.",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "The submitted data failed validation.",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "An unexpected error occurred. Please try again later.",
}


def _flatten_detail(detail):
    """Return (message, errors) from any DRF ``detail`` shape."""
    if isinstance(detail, dict):
        errors = {
            field: [str(item) for item in (value if isinstance(value, (list, tuple)) else [value])]
            for field, value in detail.items()
        }
        first_field, first_messages = next(iter(errors.items()), (None, []))
        if first_field in {"detail", "non_field_errors"} and first_messages:
            return first_messages[0], errors
        if first_field and first_messages:
            return f"{first_field}: {first_messages[0]}", errors
        return None, errors
    if isinstance(detail, (list, tuple)):
        messages = [str(item) for item in detail]
        return (messages[0] if messages else None), {"non_field_errors": messages}
    return str(detail), {}


def api_exception_handler(exc, context):
    """DRF ``EXCEPTION_HANDLER`` — normalises every error response."""
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(detail=getattr(exc, "message_dict", None) or list(exc.messages))
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()
    elif isinstance(exc, Http404):
        exc = exceptions.NotFound()

    response = drf_exception_handler(exc, context)

    if response is None:
        view = context.get("view").__class__.__name__ if context.get("view") else "unknown"
        logger.exception("Unhandled exception in %s", view, exc_info=exc)
        return Response(
            {
                "success": False,
                "message": DEFAULT_MESSAGES[status.HTTP_500_INTERNAL_SERVER_ERROR],
                "code": "INTERNAL_SERVER_ERROR",
                "errors": {},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Validation errors are reported as 422 so the frontend can branch cleanly
    # between "malformed request" (400) and "field-level problems" (422).
    if isinstance(exc, exceptions.ValidationError):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    message, errors = _flatten_detail(getattr(exc, "detail", response.data))
    code = getattr(exc, "default_code", None)
    code = code.upper() if isinstance(code, str) else None

    response.data = {
        "success": False,
        "message": message or DEFAULT_MESSAGES.get(response.status_code, "Request failed."),
        "code": STATUS_CODE_MAP.get(response.status_code, code or "ERROR"),
        "errors": errors,
    }
    return response
