"""
Everything the public landing page renders.

The site a visitor sees is content, not configuration: an administrator with the
right permission codes edits it from the dashboard, and nothing here needs a
deploy to change. Each model maps to exactly one section of the landing page.
"""
from django.db import models

from apps.common.models import BaseModel


class HeroSlide(BaseModel):
    """
    One image in the landing page's hero slider.

    Slides rotate automatically and can be stepped through manually; ``order``
    decides the sequence, and a soft-deleted or inactive slide simply drops out
    of the rotation without disturbing the rest.
    """

    title = models.CharField(max_length=150, blank=True, default="", help_text="Headline drawn over the image.")
    subtitle = models.CharField(max_length=255, blank=True, default="")
    caption = models.CharField(max_length=120, blank=True, default="", help_text="Small eyebrow label above the title.")
    image = models.ImageField(upload_to="website/hero/")
    alt_text = models.CharField(
        max_length=200, blank=True, default="", help_text="Described for screen readers; falls back to the title."
    )
    link_url = models.CharField(max_length=300, blank=True, default="", help_text="Optional call-to-action target.")
    link_label = models.CharField(max_length=60, blank=True, default="")
    order = models.PositiveSmallIntegerField(default=0, db_index=True, help_text="Lower numbers appear first.")

    class Meta:
        db_table = "hero_slides"
        ordering = ["order", "-created_at"]
        verbose_name = "Hero slide"

    def __str__(self):
        return self.title or f"Slide {self.pk}"


class AboutSection(BaseModel):
    """
    The "About the School" copy — history, mission, vision.

    A singleton, pinned to ``pk=1`` the same way the school profile is: there is
    one school and one story to tell about it. Reach for it through
    :meth:`load` so a fresh database returns an empty, editable record rather
    than raising ``DoesNotExist``.
    """

    headline = models.CharField(max_length=200, blank=True, default="", verbose_name="Section headline")
    summary = models.TextField(blank=True, default="", help_text="One or two paragraphs introducing the school.")
    history = models.TextField(blank=True, default="")
    mission = models.TextField(blank=True, default="")
    vision = models.TextField(blank=True, default="")
    motto = models.CharField(max_length=200, blank=True, default="")
    image = models.ImageField(upload_to="website/about/", null=True, blank=True)

    class Meta:
        db_table = "about_section"
        verbose_name = "About the school"
        verbose_name_plural = "About the school"

    def __str__(self):
        return self.headline or "About the school"

    def save(self, *args, **kwargs):
        if self._state.adding and not self.pk:
            self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise NotImplementedError("The about section is a singleton and cannot be deleted.")

    @classmethod
    def load(cls) -> "AboutSection":
        existing = cls.objects.filter(pk=1).first()
        return existing if existing is not None else cls.objects.create(pk=1)


class Achievement(BaseModel):
    """A milestone shown alongside the About section — awards, records, results."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    year = models.CharField(max_length=20, blank=True, default="", db_index=True)
    metric = models.CharField(
        max_length=60, blank=True, default="", help_text='A number worth showing large, e.g. "100%" or "42".'
    )
    order = models.PositiveSmallIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "school_achievements"
        ordering = ["order", "-year", "title"]

    def __str__(self):
        return self.title


class SuccessfulStudent(BaseModel):
    """
    A student whose result the school wants to celebrate publicly.

    Deliberately independent of :class:`~apps.students.models.Student`: the roll
    is for enrolled pupils, while this board keeps honouring alumni long after
    they have left. ``student`` links the two when the pupil is still on the
    roll, and is optional precisely so it can be left empty when they are not.
    """

    academic_year = models.CharField(max_length=10, db_index=True, help_text='e.g. "2025"')
    full_name = models.CharField(max_length=150)
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.SET_NULL,
        related_name="public_achievements",
        null=True,
        blank=True,
        help_text="Linked enrolment record, when the student is still on the roll.",
    )
    student_class = models.CharField(max_length=60, blank=True, default="", help_text='e.g. "Class 10"')
    section = models.CharField(max_length=30, blank=True, default="")
    roll_number = models.CharField(max_length=30, blank=True, default="")
    exam_name = models.CharField(max_length=100, blank=True, default="", help_text='e.g. "SSC" or "Annual Exam"')
    result = models.CharField(max_length=100, blank=True, default="", help_text='e.g. "GPA 5.00" or "1st place"')
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    achievement = models.CharField(
        max_length=255, blank=True, default="", help_text='e.g. "Talentpool scholarship" or "District champion".'
    )
    photo = models.ImageField(upload_to="website/students/", null=True, blank=True)
    remarks = models.TextField(blank=True, default="")
    is_featured = models.BooleanField(default=False, db_index=True, help_text="Pinned to the front of the year.")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "successful_students"
        ordering = ["-academic_year", "-is_featured", "order", "full_name"]
        verbose_name = "Successful student"

    def __str__(self):
        return f"{self.full_name} — {self.academic_year}"
