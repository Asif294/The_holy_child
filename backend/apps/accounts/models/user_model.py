import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models, transaction
from django.utils import timezone

from apps.accounts.constants import ROLE_SUPER_ADMIN
from apps.accounts.models.role_model import Role
from apps.accounts.utils import clean_phone
from apps.common.models import BaseModel


def profile_image_path(instance, filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower()
    return f"profiles/{uuid.uuid4().hex}.{extension}"


class UserManager(BaseUserManager):
    """Email-first manager. Username is optional and derived when omitted."""

    use_in_migrations = True

    def _derive_username(self, email: str) -> str:
        base = email.split("@", 1)[0][:120] or "user"
        username, suffix = base, 1
        while self.model.objects.filter(username__iexact=username).exists():
            suffix += 1
            username = f"{base}{suffix}"
        return username

    @transaction.atomic
    def create_user(self, email: str, password: str, **extra_fields):
        if not email:
            raise ValueError("An email address is required to create a user.")
        if not password:
            raise ValueError("A password is required to create a user.")

        email = self.normalize_email(email).lower()
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        if not extra_fields.get("username"):
            extra_fields["username"] = self._derive_username(email)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.full_clean(exclude=["password"])
        user.save(using=self._db)
        return user

    @transaction.atomic
    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.update(is_staff=True, is_superuser=True, is_active=True)
        if not extra_fields.get("full_name"):
            extra_fields["full_name"] = "Super Admin"
        user = self.create_user(email=email, password=password, **extra_fields)
        role = Role.objects.filter(slug=ROLE_SUPER_ADMIN).first()
        if role and user.role_id is None:
            user.role = role
            user.save(update_fields=["role", "updated_at"])
        return user


class User(AbstractBaseUser, BaseModel):
    """
    Custom user for the whole platform.

    Authentication is email-first (``USERNAME_FIELD = "email"``) but the login
    endpoint also accepts the phone number or the username — see
    :class:`apps.accounts.backends.EmailPhoneOrUsernameBackend`. That is why
    ``phone`` is unique whenever it is filled in: a number that identified two
    accounts could not identify either.

    A user holds exactly one :class:`~apps.accounts.models.role_model.Role`, and
    every capability check resolves through that role's permission codes.
    """

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    email = models.EmailField(max_length=254, unique=True, db_index=True, verbose_name="Email address")
    username = models.CharField(max_length=150, unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        db_index=True,
        help_text="Stored without spaces or dashes. Doubles as a login identifier.",
    )
    profile_image = models.ImageField(upload_to=profile_image_path, null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True, default="")
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, default="")

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        related_name="users",
        null=True,
        blank=True,
        help_text="The role this user inherits permissions from.",
    )

    is_staff = models.BooleanField(default=False, help_text="Can sign in to the Django admin site.")
    is_superuser = models.BooleanField(default=False, help_text="Bypasses every permission check.")
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"
        constraints = [
            # Blank is the "no number on file" case and stays freely repeatable;
            # a real number must point at exactly one account so it can be used
            # to sign in.
            models.UniqueConstraint(
                fields=["phone"],
                condition=~models.Q(phone=""),
                name="unique_user_phone",
            ),
        ]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    # ----------------------------------------------------------------- #
    # Normalisation
    # ----------------------------------------------------------------- #
    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        if self.username:
            self.username = self.username.strip()
        self.phone = clean_phone(self.phone)
        super().save(*args, **kwargs)

    # ----------------------------------------------------------------- #
    # RBAC
    # ----------------------------------------------------------------- #
    def get_permission_codes(self) -> set[str]:
        """
        Every permission code this user holds.

        Superusers implicitly hold everything; everyone else inherits exactly the
        codes attached to their (active) role.
        """
        if self.is_superuser:
            from apps.accounts.models.permission_model import Permission

            return set(Permission.objects.values_list("code", flat=True))
        if not self.role_id or not self.role or not self.role.is_active:
            return set()
        return set(self.role.permissions.values_list("code", flat=True))

    def has_permission(self, code: str) -> bool:
        return self.is_superuser or code in self.get_permission_codes()

    def has_any_permission(self, *codes: str) -> bool:
        if self.is_superuser:
            return True
        held = self.get_permission_codes()
        return any(code in held for code in codes)

    def has_all_permissions(self, *codes: str) -> bool:
        if self.is_superuser:
            return True
        held = self.get_permission_codes()
        return all(code in held for code in codes)

    @property
    def role_name(self) -> str | None:
        return self.role.name if self.role_id and self.role else None

    @property
    def is_super_admin(self) -> bool:
        return self.is_superuser or (self.role_id is not None and self.role.slug == ROLE_SUPER_ADMIN)

    # ----------------------------------------------------------------- #
    # Django admin compatibility
    # ----------------------------------------------------------------- #
    def has_perm(self, perm, obj=None) -> bool:
        return self.is_active and self.is_superuser

    def has_module_perms(self, app_label) -> bool:
        return self.is_active and self.is_superuser

    def record_login(self, ip_address: str | None = None) -> None:
        self.last_login = timezone.now()
        fields = ["last_login"]
        if ip_address:
            self.last_login_ip = ip_address
            fields.append("last_login_ip")
        self.save(update_fields=fields)
