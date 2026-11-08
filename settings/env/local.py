"""Development settings: SQLite, DEBUG enabled."""

from settings.base import *  # noqa: F403, F405
from settings.conf import BASE_DIR

DEBUG = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
}
