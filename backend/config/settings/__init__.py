"""
Settings package entry point.

The active settings module is selected with the ``DJANGO_ENV`` environment
variable (``development`` by default) so that ``DJANGO_SETTINGS_MODULE`` can
stay pinned to ``config.settings`` everywhere.
"""
import os

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

DJANGO_ENV = os.getenv("DJANGO_ENV", "development").lower()

if DJANGO_ENV == "production":
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
