"""
Base settings shared by every environment.

Everything that differs between machines is read from the environment (see
``.env.example``). Nothing secret is ever hardcoded here.
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")


def env(key: str, default=None):
    return os.getenv(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    return str(os.getenv(key, str(default))).strip().lower() in {"1", "true", "yes", "on"}


def env_list(key: str, default: str = "") -> list[str]:
    raw = os.getenv(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #
SECRET_KEY = env("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set. Copy .env.example to .env and fill it in.")

DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
APPEND_SLASH = True

# --------------------------------------------------------------------------- #
# Applications
# --------------------------------------------------------------------------- #
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.common",
    "apps.accounts",
    "apps.students",
    "apps.teachers",
    "apps.principal",
    "apps.classes",
    "apps.subjects",
    "apps.attendance",
    "apps.fees",
    "apps.exams",
    "apps.dashboard",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.CurrentUserMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --------------------------------------------------------------------------- #
# Database — PostgreSQL
# --------------------------------------------------------------------------- #
DATABASES = {
    "default": {
        "ENGINE": env("DATABASE_ENGINE", "django.db.backends.postgresql"),
        "NAME": env("DATABASE_NAME", "holychild"),
        "USER": env("DATABASE_USER", ""),
        "PASSWORD": env("DATABASE_PASSWORD", ""),
        "HOST": env("DATABASE_HOST", "localhost"),
        "PORT": env("DATABASE_PORT", "5432"),
        "CONN_MAX_AGE": int(env("DATABASE_CONN_MAX_AGE", "60")),
    }
}

# A sqlite escape hatch so the project stays runnable on a machine without a
# provisioned PostgreSQL role. PostgreSQL remains the default and the target.
if env("DATABASE_ENGINE", "").endswith("sqlite3"):
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / env("DATABASE_NAME", "db.sqlite3"),
    }

# --------------------------------------------------------------------------- #
# Authentication
# --------------------------------------------------------------------------- #
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# --------------------------------------------------------------------------- #
# Django REST Framework
# --------------------------------------------------------------------------- #
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.common.exception_handler.api_exception_handler",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(env("JWT_ACCESS_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(env("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env("JWT_SIGNING_KEY") or SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.LoginSerializer",
}

# --------------------------------------------------------------------------- #
# OpenAPI / Swagger
# --------------------------------------------------------------------------- #
SPECTACULAR_SETTINGS = {
    "TITLE": "The Holy Child Pre-Cadet & High School — Management API",
    "DESCRIPTION": (
        "REST API for the school management platform of **The Holy Child Pre-Cadet & "
        "High School**, Longorpara, Sribordi, Sherpur.\n\n"
        "### Authentication\n"
        "All endpoints except the landing/auth endpoints require a JWT access token:\n\n"
        "```\nAuthorization: Bearer <access_token>\n```\n\n"
        "Obtain a token pair from `POST /api/v1/auth/login/` and refresh it with "
        "`POST /api/v1/auth/token/refresh/`.\n\n"
        "### Authorization\n"
        "Access is governed by granular permission codes (e.g. `student.view`, "
        "`attendance.create`) that a user inherits from their assigned **Role**. "
        "Endpoints return `401` when unauthenticated and `403` when the authenticated "
        "user lacks the required permission code.\n\n"
        "### Error format\n"
        "```json\n"
        "{\n"
        '  "success": false,\n'
        '  "message": "You do not have permission to perform this action.",\n'
        '  "code": "PERMISSION_DENIED",\n'
        '  "errors": {}\n'
        "}\n"
        "```"
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v1",
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": False,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "docExpansion": "none",
    },
    # Several models expose a `category` / `status` field with different choice
    # sets; naming them explicitly keeps the generated components readable.
    "ENUM_NAME_OVERRIDES": {
        "EventCategoryEnum": "apps.dashboard.models.SchoolEvent.Category",
        "ApprovalCategoryEnum": "apps.principal.models.ApprovalRequest.Category",
        "SubjectCategoryEnum": "apps.subjects.models.Subject.Category",
        "FeeFrequencyEnum": "apps.fees.models.FeeCategory.Frequency",
        "StudentStatusEnum": "apps.students.models.Student.Status",
        "TeacherStatusEnum": "apps.teachers.models.Teacher.Status",
        "ExamStatusEnum": "apps.exams.models.Exam.Status",
        "InvoiceStatusEnum": "apps.fees.models.Invoice.Status",
        "ApprovalStatusEnum": "apps.principal.models.ApprovalRequest.Status",
        "AttendanceStatusEnum": "apps.attendance.models.AttendanceStatus",
    },
    "TAGS": [
        {"name": "Authentication", "description": "Register, login, refresh, logout and current user."},
        {"name": "Users", "description": "User administration and role assignment."},
        {"name": "Roles", "description": "Dynamic role management with permission assignment."},
        {"name": "Permissions", "description": "Read-only catalogue of granular permission codes."},
        {"name": "Dashboard", "description": "Aggregated statistics and activity feeds."},
        {"name": "Principal", "description": "Principal office: profile, notices and approvals."},
        {"name": "Teachers", "description": "Teaching staff records, designations and assignments."},
        {"name": "Students", "description": "Student enrolment records and guardians."},
        {"name": "Classes", "description": "Classes, sections and academic sessions."},
        {"name": "Subjects", "description": "Subject catalogue and class-subject mapping."},
        {"name": "Attendance", "description": "Daily attendance capture and summaries."},
        {"name": "Fees", "description": "Fee structures, invoices and payments."},
        {"name": "Exams", "description": "Exams, schedules and results."},
    ],
}

# --------------------------------------------------------------------------- #
# CORS
# --------------------------------------------------------------------------- #
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

# --------------------------------------------------------------------------- #
# Internationalization
# --------------------------------------------------------------------------- #
LANGUAGE_CODE = env("LANGUAGE_CODE", "en-us")
TIME_ZONE = env("TIME_ZONE", "Asia/Dhaka")
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- #
# Static & media
# --------------------------------------------------------------------------- #
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --------------------------------------------------------------------------- #
# School identity (surfaced by the API for the frontend)
# --------------------------------------------------------------------------- #
SCHOOL = {
    "NAME_EN": env("SCHOOL_NAME_EN", "The Holy Child Pre-Cadet & High School"),
    "NAME_BN": env("SCHOOL_NAME_BN", "দি হলি চাইল্ড প্রি-ক্যাডেট এন্ড হাই স্কুল"),
    "SHORT_NAME": env("SCHOOL_SHORT_NAME", "Holy Child"),
    "VILLAGE": env("SCHOOL_VILLAGE", "Longorpara"),
    "UPAZILA": env("SCHOOL_UPAZILA", "Sribordi"),
    "DISTRICT": env("SCHOOL_DISTRICT", "Sherpur"),
    "COUNTRY": env("SCHOOL_COUNTRY", "Bangladesh"),
    "ESTABLISHED": env("SCHOOL_ESTABLISHED", "2006"),
    "GRADE_RANGE": env("SCHOOL_GRADE_RANGE", "Play Group to Class 10"),
    "GRADE_RANGE_BN": env("SCHOOL_GRADE_RANGE_BN", "প্লে-গ্রুপ থেকে ১০ম শ্রেণি পর্যন্ত"),
    "EMAIL": env("SCHOOL_EMAIL", "info@holychildschool.edu.bd"),
    "PHONE": env("SCHOOL_PHONE", "+880 1700-000000"),
}

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "[{asctime}] {levelname} {name}: {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
    "loggers": {
        "django.db.backends": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
