#!/usr/bin/env python3
"""Django command-line utility."""

import os
import sys

from settings.conf import BLOG_ENV_ID

ENVIRONMENTS = ("local", "prod")


def main() -> None:
    """Run Django with the environment selected in settings/.env."""
    if BLOG_ENV_ID not in ENVIRONMENTS:
        raise ValueError(f"Unknown BLOG_ENV_ID: {BLOG_ENV_ID}")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"settings.env.{BLOG_ENV_ID}")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
