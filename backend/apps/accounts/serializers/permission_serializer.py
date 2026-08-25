from rest_framework import serializers

from apps.accounts.models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    """A single granular capability."""

    class Meta:
        model = Permission
        fields = ("id", "code", "name", "module", "module_label", "action", "group", "description")
        read_only_fields = fields


class PermissionGroupSerializer(serializers.Serializer):
    """Permissions nested by UI group and module — powers the role permission matrix."""

    group = serializers.CharField()
    modules = serializers.ListField(child=serializers.DictField())
