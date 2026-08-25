from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import Role, User
from apps.accounts.utils import validate_phone_value


class UserRoleBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("id", "name", "slug")
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    """Read representation of a user, including the resolved permission codes."""

    role = UserRoleBriefSerializer(read_only=True)
    permissions = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "full_name", "email", "username", "phone", "gender", "date_of_birth",
            "address", "profile_image", "profile_image_url", "role", "permissions",
            "is_active", "is_staff", "is_superuser", "last_login", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "permissions", "is_staff", "is_superuser", "last_login",
            "created_at", "updated_at", "profile_image_url",
        )

    def get_permissions(self, obj) -> list[str]:
        return sorted(obj.get_permission_codes())

    def get_profile_image_url(self, obj) -> str | None:
        if not obj.profile_image:
            return None
        request = self.context.get("request")
        url = obj.profile_image.url
        return request.build_absolute_uri(url) if request else url


class UserCompactSerializer(serializers.ModelSerializer):
    """Minimal shape embedded in login responses and activity feeds."""

    role = serializers.CharField(source="role_name", read_only=True, allow_null=True)
    role_slug = serializers.SerializerMethodField()
    name = serializers.CharField(source="full_name", read_only=True)
    permissions = serializers.SerializerMethodField()
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "name", "full_name", "email", "username", "phone",
            "role", "role_slug", "permissions", "profile_image_url", "is_active",
        )
        read_only_fields = fields

    def get_role_slug(self, obj) -> str | None:
        return obj.role.slug if obj.role_id and obj.role else None

    def get_permissions(self, obj) -> list[str]:
        return sorted(obj.get_permission_codes())

    def get_profile_image_url(self, obj) -> str | None:
        if not obj.profile_image:
            return None
        request = self.context.get("request")
        url = obj.profile_image.url
        return request.build_absolute_uri(url) if request else url


class UserWriteSerializer(serializers.ModelSerializer):
    """
    Administrator-facing create/update serializer.

    Unlike registration this *may* assign any role — the endpoint using it is
    itself gated behind ``user.create`` / ``user.update``.
    """

    password = serializers.CharField(write_only=True, required=False, allow_blank=False, style={"input_type": "password"})
    # Optional: derived from the email when omitted, so callers only need an email.
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role_id = serializers.PrimaryKeyRelatedField(
        source="role", queryset=Role.objects.filter(is_deleted=False), required=False, allow_null=True
    )

    class Meta:
        model = User
        fields = (
            "id", "full_name", "email", "username", "phone", "password", "role_id",
            "gender", "date_of_birth", "address", "profile_image", "is_active",
        )
        read_only_fields = ("id",)

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        queryset = User.objects.filter(email__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value: str) -> str:
        value = value.strip()
        if not value:
            return value
        queryset = User.objects.filter(username__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_phone(self, value: str) -> str:
        # Unique, because the login form accepts a phone number as the identifier.
        return validate_phone_value(value, instance=self.instance)

    def validate_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def validate(self, attrs):
        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError({"password": "A password is required when creating a user."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        if not validated_data.get("username"):
            validated_data.pop("username", None)
        return User.objects.create_user(password=password, **validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

    def to_representation(self, instance):
        return UserSerializer(instance, context=self.context).data


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """What a signed-in user may change about themselves — never their own role."""

    class Meta:
        model = User
        fields = ("full_name", "phone", "gender", "date_of_birth", "address", "profile_image")

    def validate_phone(self, value: str) -> str:
        return validate_phone_value(value, instance=self.instance)

    def to_representation(self, instance):
        return UserSerializer(instance, context=self.context).data


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password_confirmation = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your current password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirmation"]:
            raise serializers.ValidationError({"new_password_confirmation": "The two password fields do not match."})
        user = self.context["request"].user
        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)}) from exc
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        return user


class AssignRoleSerializer(serializers.Serializer):
    """Body for ``POST /api/v1/users/{id}/assign-role/``."""

    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_deleted=False, is_active=True),
        help_text="Primary key of the role to assign.",
    )
