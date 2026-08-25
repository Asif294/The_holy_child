from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.constants import DEFAULT_SELF_REGISTRATION_ROLE
from apps.accounts.models import Role, User
from apps.accounts.serializers.user_serializer import UserCompactSerializer


class RegisterSerializer(serializers.ModelSerializer):
    """
    Public self-registration.

    The role is decided by the backend — a registrant can never grant themselves
    a privileged role, whatever they put in the request body.
    """

    password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"},
        help_text="At least 8 characters; validated against Django's password policy.",
    )
    password_confirmation = serializers.CharField(
        write_only=True, style={"input_type": "password"},
        help_text="Must match `password`.",
    )
    phone = serializers.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ("full_name", "email", "password", "password_confirmation", "phone")
        extra_kwargs = {
            "full_name": {"required": True, "allow_blank": False},
            "email": {"required": True, "allow_blank": False},
        }

    def validate_full_name(self, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 3:
            raise serializers.ValidationError("Full name must be at least 3 characters long.")
        return value

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_phone(self, value: str) -> str:
        value = value.strip()
        digits = value.lstrip("+").replace(" ", "").replace("-", "")
        if not digits.isdigit() or not (6 <= len(digits) <= 15):
            raise serializers.ValidationError("Enter a valid phone number (6–15 digits, optional leading '+').")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError(
                {"password_confirmation": "The two password fields do not match."}
            )
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        password = validated_data.pop("password")
        # Role assignment is server-controlled — never read from the request.
        default_role = Role.objects.filter(slug=DEFAULT_SELF_REGISTRATION_ROLE).first()
        return User.objects.create_user(password=password, role=default_role, **validated_data)


class LoginSerializer(TokenObtainPairSerializer):
    """
    Exchanges credentials for a JWT pair plus the caller's identity and
    permission codes, so the frontend can render its navigation immediately.
    """

    default_error_messages = {
        "no_active_account": "No active account was found with the given credentials."
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["full_name"] = user.full_name
        token["role"] = user.role.slug if user.role_id and user.role else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        request = self.context.get("request")
        if request is not None:
            self.user.record_login(ip_address=_client_ip(request))
        data["user"] = UserCompactSerializer(self.user, context=self.context).data
        return data


class LoginResponseSerializer(serializers.Serializer):
    """Documents the shape returned by ``POST /api/v1/auth/login/``."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserCompactSerializer()


class RegisterResponseSerializer(serializers.Serializer):
    """Documents the shape returned by ``POST /api/v1/auth/register/``."""

    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = LoginResponseSerializer()


class LogoutSerializer(serializers.Serializer):
    """Blacklists a refresh token so it can no longer mint access tokens."""

    refresh = serializers.CharField(help_text="The refresh token issued at login.")

    def validate_refresh(self, value: str) -> str:
        try:
            self.token = RefreshToken(value)
        except TokenError as exc:
            raise serializers.ValidationError("This refresh token is invalid or has already expired.") from exc
        return value

    def save(self, **kwargs):
        try:
            self.token.blacklist()
        except AttributeError:  # pragma: no cover - blacklist app always installed
            pass
        return True


def _client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
