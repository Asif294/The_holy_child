from django.db import models

from apps.common.managers import ActiveManager, ActiveQuerySet
from config.middleware import get_current_user


class BaseModel(models.Model):
    """
    Audit + soft-delete base for every domain model.

    ``objects`` returns everything; ``active_objects`` hides soft-deleted rows.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.BigIntegerField(null=True, blank=True, editable=False)
    updated_by = models.BigIntegerField(null=True, blank=True, editable=False)
    is_active = models.BooleanField(default=True, db_index=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    objects = models.Manager.from_queryset(ActiveQuerySet)()
    active_objects = ActiveManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        user = get_current_user()
        if user is not None and getattr(user, "is_authenticated", False):
            if self._state.adding and self.created_by is None:
                self.created_by = user.pk
            self.updated_by = user.pk
        super().save(*args, **kwargs)

    def soft_delete(self):
        """Deactivate instead of destroying — keeps historical records intact."""
        self.is_deleted = True
        self.is_active = False
        self.save(update_fields=["is_deleted", "is_active", "updated_at", "updated_by"])

    def restore(self):
        self.is_deleted = False
        self.is_active = True
        self.save(update_fields=["is_deleted", "is_active", "updated_at", "updated_by"])
