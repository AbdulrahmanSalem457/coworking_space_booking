"""
Django settings for the Coworking Space Booking Platform.

Runs unchanged locally (SQLite, DEBUG on) and on a host like Render, where
DATABASE_URL, RENDER_EXTERNAL_HOSTNAME and DEBUG=False are supplied as
environment variables.
"""
import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load by absolute path: under a WSGI server the working directory is not the
# project root, and a bare load_dotenv() would silently find nothing.
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

# Render injects the service's public hostname at runtime; trust it so the
# deployment works without hardcoding the URL anywhere.
RENDER_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    f"https://{host}" for host in ALLOWED_HOSTS if host not in ("localhost", "127.0.0.1", "*")
]

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
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
    "drf_yasg",
    "corsheaders",
    "django_filters",
]

LOCAL_APPS = [
    "accounts",
    "spaces",
    "bookings",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Serves collected static files (including Swagger's own CSS/JS) in
    # production, where there's no separate web server in front of Django.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database — SQLite locally, whatever DATABASE_URL points at when hosted.
#
# Hosts like Render run on an ephemeral filesystem, so a SQLite file there
# would be wiped on every restart or redeploy. Attaching a managed Postgres
# instance sets DATABASE_URL and this picks it up automatically.
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.CustomUser"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
# Bookings are stored as naive date/time values matching the venue's wall clock,
# so this must be the timezone the space actually operates in — not UTC.
TIME_ZONE = os.getenv("TIME_ZONE", "Africa/Cairo")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Production hardening — only applied when DEBUG is off, so local dev over
# plain HTTP is unaffected.
# ---------------------------------------------------------------------------
if not DEBUG:
    # Hosts terminate TLS at their proxy and forward this header; without it
    # Django would think every request arrived over plain HTTP and redirect
    # forever.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # Escape hatch: if a host doesn't forward that header, the redirect above
    # turns into a loop. Set SECURE_SSL_REDIRECT=False in .env to break it
    # without editing code.
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # Managed hosts serve this domain over HTTPS only, so HSTS is safe here.
    # Deliberately without includeSubDomains/preload — those are the parts that
    # are painful to undo, and neither is needed for a single API host.
    SECURE_HSTS_SECONDS = 31536000

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# CORS
#
# This is a public, open API — any site should be able to call it from the
# browser, not just the bundled frontend. So origins are unrestricted by
# default. To lock it down (e.g. in production), list the permitted origins in
# CORS_ALLOWED_ORIGINS in .env and that list takes over.
# ---------------------------------------------------------------------------
_cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()

if _cors_origins:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]
else:
    CORS_ALLOW_ALL_ORIGINS = True

# Auth travels in the Authorization header, never in cookies, so credentialed
# cross-origin requests aren't needed — and the CORS spec forbids pairing them
# with a wildcard origin anyway.
CORS_ALLOW_CREDENTIALS = False

# ---------------------------------------------------------------------------
# drf-yasg (Swagger / Redoc)
# ---------------------------------------------------------------------------
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": (
                "Paste your access token here with the word Bearer in front.\n"
                "Example:  Bearer eyJhbGci..."
            ),
        }
    },
    "USE_SESSION_AUTH": False,
    "PERSIST_AUTH": False,
    "REFETCH_SCHEMA_WITH_AUTH": False,
    "REFETCH_SCHEMA_ON_LOGOUT": False,
    "DEFAULT_MODEL_RENDERING": "example",
    "DOC_EXPANSION": "list",
}

REDOC_SETTINGS = {
    "LAZY_RENDERING": False,
}

# ---------------------------------------------------------------------------
# Logging — print every request line to the console (visible in the terminal)
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{asctime}] {levelname} {message}",
            "datefmt": "%H:%M:%S",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            # StreamHandler defaults to stderr, which some terminals and
            # wrappers swallow. Django's own startup banner goes to stdout, so
            # send request logs there too — they then always show up together.
            "stream": "ext://sys.stdout",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
