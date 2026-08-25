from django.db import models

from apps.common.models import BaseModel


class Principal(BaseModel):
    """
    A member of the school's administration — the principal or a vice principal.

    Kept as its own record — rather than a flag on ``Teacher`` — because the
    principal's office owns notices and approvals, carries a public-facing
    message on the landing page, and has a tenure history worth preserving.

    ``office`` distinguishes the two seats. One record per office is
    ``is_current`` at a time, so the public *Administration* section can show
    the sitting principal beside the sitting vice principal without either
    standing the other down.
    """

    class Office(models.TextChoices):
        PRINCIPAL = "principal", "Principal"
        VICE_PRINCIPAL = "vice_principal", "Vice Principal"

    office = models.CharField(
        max_length=20,
        choices=Office.choices,
        default=Office.PRINCIPAL,
        db_index=True,
        help_text="Which seat this record holds.",
    )

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="principal_profile",
        null=True,
        blank=True,
        help_text="Linked login account for the principal.",
    )
    teacher = models.OneToOneField(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        related_name="principal_record",
        null=True,
        blank=True,
        help_text="Staff record, when the principal is also on the teaching roll.",
    )

    full_name = models.CharField(max_length=150)
    designation = models.CharField(
        max_length=100, blank=True, default="", help_text='Free text, e.g. "Principal" or "Vice Principal".'
    )
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    photo = models.ImageField(upload_to="principal/", null=True, blank=True)
    signature = models.ImageField(upload_to="principal/signatures/", null=True, blank=True)

    qualification = models.CharField(max_length=255, blank=True, default="")
    experience_years = models.PositiveSmallIntegerField(default=0)
    message = models.TextField(
        blank=True, default="", help_text="Message from the principal, shown on the public site."
    )
    biography = models.TextField(blank=True, default="")

    tenure_start = models.DateField(null=True, blank=True)
    tenure_end = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "principals"
        ordering = ["office", "-is_current", "-tenure_start"]
        verbose_name = "Administrator"
        verbose_name_plural = "Administration"

    def __str__(self):
        return f"{self.full_name} — {self.designation}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            # Only the holder of the *same* office stands down.
            Principal.objects.exclude(pk=self.pk).filter(
                office=self.office, is_current=True
            ).update(is_current=False)

    @classmethod
    def current(cls, office: str = Office.PRINCIPAL):
        return cls.active_objects.filter(office=office, is_current=True).first()


class Notice(BaseModel):
    """A notice issued by the principal's office."""

    class Audience(models.TextChoices):
        ALL = "all", "Everyone"
        STAFF = "staff", "Staff only"
        TEACHERS = "teachers", "Teachers"
        STUDENTS = "students", "Students"
        PARENTS = "parents", "Parents"

    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        IMPORTANT = "important", "Important"
        URGENT = "urgent", "Urgent"

    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=Audience.choices, default=Audience.ALL, db_index=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    attachment = models.FileField(upload_to="notices/", null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False, db_index=True)
    issued_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, related_name="issued_notices", null=True, blank=True
    )

    class Meta:
        db_table = "notices"
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title


class ApprovalRequest(BaseModel):
    """
    A request routed to the principal for a decision — leave, expenses, results
    publication, and anything else the school wants signed off centrally.
    """

    class Category(models.TextChoices):
        LEAVE = "leave", "Leave request"
        EXPENSE = "expense", "Expense approval"
        RESULT = "result", "Result publication"
        ADMISSION = "admission", "Admission approval"
        EVENT = "event", "Event approval"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER, db_index=True)
    details = models.TextField(blank=True, default="")
    attachment = models.FileField(upload_to="approvals/", null=True, blank=True)

    requested_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, related_name="approval_requests", null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    decided_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, related_name="approval_decisions", null=True, blank=True
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_note = models.TextField(blank=True, default="")

    class Meta:
        db_table = "approval_requests"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.title}"

    @property
    def is_pending(self) -> bool:
        return self.status == self.Status.PENDING
