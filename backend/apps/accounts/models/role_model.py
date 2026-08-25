from django.db import models
from django.utils.text import slugify

from apps.accounts.models.permission_model import Permission
from apps.common.models import BaseModel


class Role(BaseModel):
    """
    A named bundle of permissions that can be created and edited at runtime.

    Administrators compose roles freely; the application never checks a role by
    name, only the permission codes the role carries.
    """

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    is_system = models.BooleanField(
        default=False,
        help_text="System roles are seeded by the platform and cannot be renamed or deleted.",
    )
    permissions = models.ManyToManyField(
        Permission,
        related_name="roles",
        blank=True,
        db_table="role_permissions",
    )

    class Meta:
        db_table = "roles"
        ordering = ["name"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def permission_codes(self) -> list[str]:
        return list(self.permissions.values_list("code", flat=True))

    def set_permissions(self, codes) -> None:
        """Replace this role's permissions with the given codes."""
        self.permissions.set(Permission.objects.filter(code__in=set(codes)))
