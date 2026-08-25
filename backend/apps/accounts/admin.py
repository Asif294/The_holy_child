from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm

from apps.accounts.models import Permission, Role, User


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "module", "action", "group", "is_active")
    list_filter = ("group", "module", "action", "is_active")
    search_fields = ("code", "name", "module")
    ordering = ("group", "module", "action")


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_system", "is_active", "permission_total", "user_total")
    list_filter = ("is_system", "is_active")
    search_fields = ("name", "slug", "description")
    filter_horizontal = ("permissions",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="Permissions")
    def permission_total(self, obj):
        return obj.permissions.count()

    @admin.display(description="Users")
    def user_total(self, obj):
        return obj.users.count()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    change_password_form = AdminPasswordChangeForm
    list_display = ("email", "full_name", "username", "role", "is_active", "is_staff", "created_at")
    list_filter = ("is_active", "is_staff", "is_superuser", "role")
    search_fields = ("email", "full_name", "username", "phone")
    ordering = ("-created_at",)
    filter_horizontal = ()
    readonly_fields = ("created_at", "updated_at", "last_login", "last_login_ip")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Profile", {"fields": ("full_name", "phone", "gender", "date_of_birth", "address", "profile_image")}),
        ("Access control", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Audit", {"fields": ("last_login", "last_login_ip", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "full_name", "phone", "role", "password1", "password2"),
            },
        ),
    )
