from django.db import models


class ActiveQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, is_deleted=False)


class ActiveManager(models.Manager):
    """Default manager that hides soft-deleted / deactivated rows."""

    def get_queryset(self):
        return ActiveQuerySet(self.model, using=self._db).active()
