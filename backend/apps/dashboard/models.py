from django.db import models

from apps.common.models import BaseModel


class SchoolEvent(BaseModel):
    """A dated item on the school calendar — surfaced as "Upcoming events"."""

    class Category(models.TextChoices):
        ACADEMIC = "academic", "Academic"
        EXAM = "exam", "Exam"
        HOLIDAY = "holiday", "Holiday"
        SPORTS = "sports", "Sports"
        CULTURAL = "cultural", "Cultural"
        MEETING = "meeting", "Meeting"
        OTHER = "other", "Other"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.ACADEMIC, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=150, blank=True, default="")
    is_holiday = models.BooleanField(default=False)

    class Meta:
        db_table = "school_events"
        ordering = ["start_date", "start_time"]

    def __str__(self):
        return f"{self.title} ({self.start_date})"


class ActivityLog(BaseModel):
    """
    A human-readable audit trail powering the dashboard's "Recent activity" feed.

    Written explicitly by the services that care about being visible, rather than
    by a blanket signal — a feed of every row touched is noise, not activity.
    """

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        DELETED = "deleted", "Deleted"
        LOGIN = "login", "Signed in"
        PAYMENT = "payment", "Payment recorded"
        ATTENDANCE = "attendance", "Attendance marked"
        PUBLISHED = "published", "Published"

    actor = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, related_name="activities", null=True, blank=True
    )
    actor_name = models.CharField(max_length=150, blank=True, default="", help_text="Kept for deleted accounts.")
    action = models.CharField(max_length=20, choices=Action.choices, db_index=True)
    module = models.CharField(max_length=50, db_index=True, help_text='e.g. "student" | "fee"')
    description = models.CharField(max_length=255)
    object_id = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        db_table = "activity_logs"
        ordering = ["-created_at"]
        verbose_name = "Activity log"

    def __str__(self):
        return self.description

    @classmethod
    def record(cls, actor, action: str, module: str, description: str, object_id="") -> "ActivityLog":
        return cls.objects.create(
            actor=actor if actor and getattr(actor, "is_authenticated", False) else None,
            actor_name=getattr(actor, "full_name", "") or "",
            action=action,
            module=module,
            description=description,
            object_id=str(object_id or ""),
        )


class SchoolProfile(BaseModel):
    """
    The school's own identity — name, contact details, crest.

    A single row: there is one school. It used to live in ``settings.SCHOOL``
    (read from ``SCHOOL_*`` environment variables), which meant a rename or a
    new phone number needed a file edit and an API restart. Holding it in the
    database lets an administrator with ``setting.update`` change it from the
    Settings screen, and keeps the environment for things that are genuinely
    per-deployment.

    Reach for it through :meth:`load` — never ``objects.get(...)`` — so a fresh
    database seeds itself from the environment defaults on first read.
    """

    name_en = models.CharField(max_length=200, verbose_name="Name (English)")
    name_bn = models.CharField(max_length=200, blank=True, default="", verbose_name="Name (Bangla)")
    short_name = models.CharField(max_length=100, blank=True, default="")
    brand_name = models.CharField(
        max_length=100,
        blank=True,
        default="SmartSchool",
        help_text="Product wordmark shown beside the crest in the sidebar.",
    )

    village = models.CharField(max_length=100, blank=True, default="")
    upazila = models.CharField(max_length=100, blank=True, default="")
    district = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="Bangladesh")

    established = models.CharField(max_length=20, blank=True, default="")
    grade_range = models.CharField(max_length=150, blank=True, default="")
    grade_range_bn = models.CharField(max_length=150, blank=True, default="")

    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=30, blank=True, default="")
    website = models.URLField(blank=True, default="")

    logo = models.ImageField(
        upload_to="school/",
        null=True,
        blank=True,
        help_text="Square crest. Falls back to the built-in drawn logo when empty.",
    )

    class Meta:
        db_table = "school_profile"
        verbose_name = "School profile"
        verbose_name_plural = "School profile"

    def __str__(self):
        return self.name_en

    @property
    def address(self) -> str:
        """Village, upazila, district, country — skipping whichever are blank."""
        parts = [self.village, self.upazila, self.district, self.country]
        return ", ".join(part for part in parts if part)

    def save(self, *args, **kwargs):
        # Pin the singleton to one row so a stray create() can never fork the
        # school's identity into two competing records.
        if self._state.adding and not self.pk:
            self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise NotImplementedError("The school profile is a singleton and cannot be deleted.")

    @classmethod
    def load(cls) -> "SchoolProfile":
        """The one profile row, seeded from ``settings.SCHOOL`` if it is missing."""
        from django.conf import settings

        existing = cls.objects.filter(pk=1).first()
        if existing is not None:
            return existing

        source = getattr(settings, "SCHOOL", {})
        return cls.objects.create(
            pk=1,
            name_en=source.get("NAME_EN", ""),
            name_bn=source.get("NAME_BN", ""),
            short_name=source.get("SHORT_NAME", ""),
            village=source.get("VILLAGE", ""),
            upazila=source.get("UPAZILA", ""),
            district=source.get("DISTRICT", ""),
            country=source.get("COUNTRY", ""),
            established=source.get("ESTABLISHED", ""),
            grade_range=source.get("GRADE_RANGE", ""),
            grade_range_bn=source.get("GRADE_RANGE_BN", ""),
            email=source.get("EMAIL", ""),
            phone=source.get("PHONE", ""),
        )
