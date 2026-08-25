"""Development settings — verbose errors, permissive CORS, no HTTPS enforcement."""
from .base import *  # noqa: F401,F403
from .base import env_bool, env_list

DEBUG = env_bool("DEBUG", True)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0") or ["*"]

# Browsable API is handy locally; JSON stays the default renderer.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# Plain static storage locally so `runserver` does not need `collectstatic`.
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}  # noqa: F405

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
