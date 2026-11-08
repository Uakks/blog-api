"""WSGI application for the chosen BLOG_ENV_ID."""

import os

from settings.conf import BLOG_ENV_ID

os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{BLOG_ENV_ID}")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
