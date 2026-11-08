"""Load BLOG_-prefixed variables from settings/.env with python-decouple."""

from pathlib import Path

from decouple import AutoConfig, Csv


SETTINGS_DIR = Path(__file__).resolve().parent
BASE_DIR = SETTINGS_DIR.parent
CONFIG = AutoConfig(search_path=str(SETTINGS_DIR))

BLOG_ENV_ID = CONFIG("BLOG_ENV_ID", default="local")
BLOG_SECRET_KEY = CONFIG("BLOG_SECRET_KEY")
BLOG_ALLOWED_HOSTS = CONFIG(
    "BLOG_ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv()
)

BLOG_DB_NAME = CONFIG("BLOG_DB_NAME", default="blog_api")
BLOG_DB_USER = CONFIG("BLOG_DB_USER", default="blog_api")
BLOG_DB_PASSWORD = CONFIG("BLOG_DB_PASSWORD", default="")
BLOG_DB_HOST = CONFIG("BLOG_DB_HOST", default="127.0.0.1")
BLOG_DB_PORT = CONFIG("BLOG_DB_PORT", default=5432, cast=int)
