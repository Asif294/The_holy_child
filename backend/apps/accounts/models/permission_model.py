from django.db import models

from apps.common.models import BaseModel


class Permission(BaseModel):
    """
    A single granular capability, addressed by its ``code`` (e.g. ``student.view``).

    Permissions are seeded from :mod:`apps.accounts.constants` and are read-only
    over the API — they describe what the software can do, while *roles* decide
    who may do it.
    """

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Dotted capability code, e.g. 'student.create'.",
    )
    name = models.CharField(max_length=150, help_text="Human readable label, e.g. 'Create Students'.")
    module = models.CharField(max_length=50, db_index=True, help_text="Resource family, e.g. 'student'.")
    module_label = models.CharField(max_length=100, blank=True, default="")
    action = models.CharField(max_length=50, help_text="Verb, e.g. 'view' | 'create' | 'update' | 'delete'.")
    group = models.CharField(
        max_length=50,
        db_index=True,
        default="System",
        help_text="UI grouping, e.g. 'Academics' | 'Finance' | 'System'.",
    )
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "permissions"
        ordering = ["group", "module", "action"]
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        indexes = [models.Index(fields=["module", "action"])]

    def __str__(self):
        return self.code
