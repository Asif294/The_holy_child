from django.db import transaction
from rest_framework import serializers

from apps.accounts.constants import SYSTEM_ROLE_SLUGS
from apps.accounts.models import Permission, Role


class RoleListSerializer(serializers.ModelSerializer):
    """Compact role representation for list views and dropdowns."""

    permission_count = serializers.IntegerField(read_only=True)
    user_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Role
        fields = (
            "id", "name", "slug", "description", "is_system",
            "is_active", "permission_count", "user_count", "created_at", "updated_at",
        )
        read_only_fields = fields


class RoleSerializer(serializers.ModelSerializer):
    """
    Full role representation.

    Reads back the assigned permissions both as codes (handy for the frontend)
    and as expanded objects (handy for the permission matrix). Writes accept a
    plain list of permission codes.
    """

    permissions = serializers.SlugRelatedField(
        slug_field="code",
        many=True,
        required=False,
        queryset=Permission.objects.all(),
        help_text="List of permission codes, e.g. [\"student.view\", \"attendance.create\"].",
    )
    permission_details = serializers.SerializerMethodField(read_only=True)
    user_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Role
        fields = (
            "id", "name", "slug", "description", "is_system", "is_active",
            "permissions", "permission_details", "user_count", "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "is_system", "permission_details", "user_count",
                            "created_at", "updated_at")

    def get_permission_details(self, obj) -> list[dict]:
        from apps.accounts.serializers.permission_serializer import PermissionSerializer

        return PermissionSerializer(obj.permissions.all(), many=True).data

    def get_user_count(self, obj) -> int:
        return obj.users.filter(is_deleted=False).count()

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Role name cannot be blank.")
        queryset = Role.objects.filter(name__iexact=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A role with this name already exists.")
        return value

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.slug in SYSTEM_ROLE_SLUGS:
            if "name" in attrs and attrs["name"].strip() != instance.name:
                raise serializers.ValidationError(
                    {"name": "System roles cannot be renamed."}
                )
            if instance.slug == "super-admin" and "permissions" in attrs:
                raise serializers.ValidationError(
                    {"permissions": "The Super Admin role always holds every permission."}
                )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        permissions = validated_data.pop("permissions", [])
        role = Role.objects.create(**validated_data)
        role.permissions.set(permissions)
        return role

    @transaction.atomic
    def update(self, instance, validated_data):
        permissions = validated_data.pop("permissions", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if permissions is not None:
            instance.permissions.set(permissions)
        return instance
