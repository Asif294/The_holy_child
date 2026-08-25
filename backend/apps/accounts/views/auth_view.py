import logging

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.serializers import (
    ChangePasswordSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    ProfileUpdateSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
    UserCompactSerializer,
    UserSerializer,
    token_pair_for,
)
from apps.common.schema import UNAUTHORIZED, VALIDATION_ERROR
from apps.common.serializers import MessageResponseSerializer

logger = logging.getLogger(__name__)


def issue_tokens(user, context=None) -> dict:
    """Mint a refresh/access pair and bundle the caller's identity with it."""
    return {
        **token_pair_for(user),
        "user": UserCompactSerializer(user, context=context or {}).data,
    }


@extend_schema(
    tags=["Authentication"],
    summary="Register a new account",
    description=(
        "Creates a self-service account and immediately returns a JWT pair.\n\n"
        "**The role is assigned by the server** (the default self-registration role). "
        "Any role supplied in the request body is ignored — privileged roles such as "
        "*Super Admin* or *School Admin* can only be granted by an administrator "
        "through `POST /api/v1/users/`."
    ),
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(response=RegisterResponseSerializer, description="Account created."),
        422: VALIDATION_ERROR,
    },
    examples=[
        OpenApiExample(
            "Registration request",
            value={
                "full_name": "Rahim Uddin",
                "email": "rahim@example.com",
                "password": "StrongPass!2026",
                "password_confirmation": "StrongPass!2026",
                "phone": "+8801700000000",
            },
            request_only=True,
        )
    ],
)
class RegisterAPIView(GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("New account registered: %s", user.email)
        return Response(
            {
                "success": True,
                "message": "Registration successful.",
                "data": issue_tokens(user, context=self.get_serializer_context()),
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    tags=["Authentication"],
    summary="Log in and obtain a JWT pair",
    description=(
        "Authenticates with **email address, phone number or username** in the "
        "single `identifier` field, plus the password. `email`, `phone` and "
        "`username` are accepted as aliases for `identifier`.\n\n"
        "The response embeds the user's role and the full list of permission codes "
        "so the client can build its navigation without a second round trip."
    ),
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(response=LoginResponseSerializer, description="Authenticated."),
        401: UNAUTHORIZED,
        422: VALIDATION_ERROR,
    },
    examples=[
        OpenApiExample(
            "Login with an email address",
            value={"identifier": "admin@holychildschool.edu.bd", "password": "••••••••"},
            request_only=True,
        ),
        OpenApiExample(
            "Login with a phone number",
            value={"identifier": "01700000000", "password": "••••••••"},
            request_only=True,
        ),
        OpenApiExample(
            "Login response",
            value={
                "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user": {
                    "id": 1,
                    "name": "Nasrin Akter",
                    "email": "teacher@holychildschool.edu.bd",
                    "role": "Teacher",
                    "permissions": ["student.view", "attendance.create"],
                },
            },
            response_only=True,
        ),
    ],
)
class LoginAPIView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    www_authenticate_realm = "api"

    def get_authenticate_header(self, request) -> str:
        # The view runs without authenticators, and DRF downgrades an
        # AuthenticationFailed to 403 unless the view can name a challenge.
        # Bad credentials on the login endpoint are a 401, so name one.
        return f'Bearer realm="{self.www_authenticate_realm}"'

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentication"],
    summary="Refresh an access token",
    description=(
        "Exchanges a valid refresh token for a fresh access token. Refresh tokens "
        "rotate on every use and the consumed token is blacklisted, so the previous "
        "refresh token stops working once this call succeeds."
    ),
    responses={200: OpenApiResponse(description="A new access (and rotated refresh) token."), 401: UNAUTHORIZED},
)
class TokenRefreshAPIView(TokenRefreshView):
    permission_classes = [AllowAny]
    authentication_classes = []


@extend_schema(
    tags=["Authentication"],
    summary="Log out",
    description="Blacklists the supplied refresh token so it can no longer mint access tokens.",
    request=LogoutSerializer,
    responses={
        200: OpenApiResponse(response=MessageResponseSerializer, description="Logged out."),
        401: UNAUTHORIZED,
        422: VALIDATION_ERROR,
    },
)
class LogoutAPIView(GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Logged out successfully."}, status=status.HTTP_200_OK)


@extend_schema(tags=["Authentication"])
class MeAPIView(GenericAPIView):
    """The signed-in user's own profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_object(self):
        return self.request.user

    @extend_schema(
        summary="Current user",
        description=(
            "Returns the authenticated user together with the resolved permission "
            "codes. Clients call this on boot to rehydrate their auth state from a "
            "stored token."
        ),
        responses={200: UserSerializer, 401: UNAUTHORIZED},
    )
    def get(self, request, *args, **kwargs):
        return Response(self.get_serializer(request.user).data)

    @extend_schema(
        summary="Update own profile",
        description="Updates the caller's own profile. A user can never change their own role here.",
        request=ProfileUpdateSerializer,
        responses={200: UserSerializer, 401: UNAUTHORIZED, 422: VALIDATION_ERROR},
    )
    def patch(self, request, *args, **kwargs):
        serializer = ProfileUpdateSerializer(
            instance=request.user, data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema(
    tags=["Authentication"],
    summary="Change own password",
    description="Verifies the current password, then applies a new one validated against the password policy.",
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(response=MessageResponseSerializer, description="Password updated."),
        401: UNAUTHORIZED,
        422: VALIDATION_ERROR,
    },
)
class ChangePasswordAPIView(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "message": "Password changed successfully."}, status=status.HTTP_200_OK)
