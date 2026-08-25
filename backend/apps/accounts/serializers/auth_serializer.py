from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.constants import DEFAULT_SELF_REGISTRATION_ROLE
from apps.accounts.models import Role, User
from apps.accounts.serializers.user_serializer import UserCompactSerializer
from apps.accounts.utils import validate_phone_value


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
        return validate_phone_value(value, required=True)

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


#: Request keys that mean "the thing the user typed into the identity box".
IDENTIFIER_ALIASES = ("identifier", "email", "phone", "username")


def token_pair_for(user) -> dict:
    """A refresh/access pair carrying the claims the frontend reads on boot."""
    refresh = RefreshToken.for_user(user)
    refresh["email"] = user.email
    refresh["full_name"] = user.full_name
    refresh["role"] = user.role.slug if user.role_id and user.role else None
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class LoginSerializer(serializers.Serializer):
    """
    Exchanges credentials for a JWT pair plus the caller's identity and
    permission codes, so the frontend can render its navigation immediately.

    One ``identifier`` field takes an email address, a phone number or a
    username; :class:`~apps.accounts.backends.EmailPhoneOrUsernameBackend`
    decides which it is. ``email``, ``phone`` and ``username`` are accepted as
    aliases for the same field so older clients keep working unchanged.

    This is written against ``authenticate()`` rather than SimpleJWT's
    ``TokenObtainPairSerializer`` because that class types its identity field
    from ``USERNAME_FIELD`` — an ``EmailField``, which rejects a phone number
    before any backend ever sees it.
    """

    identifier = serializers.CharField(
        help_text="Email address, phone number or username.",
        required=False,
        allow_blank=True,
    )
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def to_internal_value(self, data):
        # Fold whichever alias the client sent into `identifier`. `copy()` keeps
        # a QueryDict a QueryDict — `dict(QueryDict)` would turn every value
        # into a list.
        if hasattr(data, "get") and not data.get("identifier"):
            data = data.copy()
            for alias in IDENTIFIER_ALIASES[1:]:
                if data.get(alias):
                    data["identifier"] = data[alias]
                    break
        return super().to_internal_value(data)

    def validate_identifier(self, value: str) -> str:
        return (value or "").strip()

    def validate(self, attrs):
        identifier = attrs.get("identifier", "")
        if not identifier:
            raise serializers.ValidationError(
                {"identifier": "Enter your email address or phone number."}
            )

        request = self.context.get("request")
        user = authenticate(request=request, username=identifier, password=attrs["password"])
        if user is None:
            # One message for every failure: a distinct "no such account" reply
            # would turn the login form into an account-existence oracle.
            raise AuthenticationFailed(
                "No active account was found with the given credentials.", code="no_active_account"
            )

        if request is not None:
            user.record_login(ip_address=_client_ip(request))

        return {
            **token_pair_for(user),
            "user": UserCompactSerializer(user, context=self.context).data,
        }


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
