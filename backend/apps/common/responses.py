"""Success-envelope helpers so every endpoint answers in the same shape."""
from rest_framework import status
from rest_framework.response import Response


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK, **extra):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return Response(payload, status=status_code)


def created_response(data=None, message="Created successfully."):
    return success_response(data=data, message=message, status_code=status.HTTP_201_CREATED)


def deleted_response(message="Deleted successfully."):
    return Response({"success": True, "message": message}, status=status.HTTP_200_OK)


def error_response(message, code="BAD_REQUEST", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response(
        {"success": False, "message": message, "code": code, "errors": errors or {}},
        status=status_code,
    )
