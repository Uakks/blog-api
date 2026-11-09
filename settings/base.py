"""Settings shared between the local and production environments."""

from django.urls import reverse_lazy

from settings.conf import BASE_DIR, BLOG_ALLOWED_HOSTS, BLOG_SECRET_KEY


SECRET_KEY = BLOG_SECRET_KEY
ALLOWED_HOSTS = BLOG_ALLOWED_HOSTS

UNFOLD = {
    "SITE_TITLE": "Blog Admin",
    "SITE_HEADER": "My Blog",
    "SITE_SUBHEADER": "Content Management System",
    "SITE_SYMBOL": "article",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
    },
    "COLORS": {
        "primary": {
            "50": "#eff6ff",
            "100": "#dbeafe",
            "200": "#bfdbfe",
            "300": "#93c5fd",
            "400": "#60a5fa",
            "500": "#3b82f6",
            "600": "#2563eb",
            "700": "#1d4ed8",
            "800": "#1e40af",
            "900": "#1e3a8a",
            "950": "#172554",
        },
    },
    "ENVIRONMENT": "apps.blog.admin_callbacks.environment_callback",
    "SITE_DROPDOWN": [
    {
        "icon": "code",
        "title": "GitHub Repository",
        "link": "https://github.com/YOUR_USERNAME/YOUR_REPO",
    },
    {
        "icon": "description",
        "title": "Unfold Documentation",
        "link": "https://unfoldadmin.com/docs/",
    },
],
    "COMMAND": {
        "search_models": True,
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": "apps.blog.admin_callbacks.sidebar_navigation",
    },
    "DASHBOARD_CALLBACK": (
        "apps.blog.admin_callbacks.dashboard_callback"
    ),
}

# Application packages are explicitly registered, like the CRM reference.
DJANGO_AND_THIRD_PARTY_APPS = [
    "unfold",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
]

PROJECT_APPS = [
    "apps.auths.apps.AuthsConfig",
    "apps.blog.apps.BlogConfig",
]

INSTALLED_APPS = DJANGO_AND_THIRD_PARTY_APPS + PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "settings.urls"
WSGI_APPLICATION = "settings.wsgi.application"
ASGI_APPLICATION = "settings.asgi.application"
AUTH_USER_MODEL = "auths.User"

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

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
}
