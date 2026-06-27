"""
Django settings for OpenShiksha project - Base Configuration

This contains all settings common to all environments.
Environment-specific settings are in development.py and production.py
"""

import os
from datetime import timedelta
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-CHANGE-THIS-IN-PRODUCTION")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Build / deploy identity — surfaced by the /api/v1/version/ build-info endpoint
# (OBS-2). APP_VERSION is the human-facing release; GIT_SHA / BUILD_TIME are baked
# into the prod image at build time; ENVIRONMENT names the running env (dev/qa/prod).
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Prometheus metrics exposition (MET-1). Strictly env-gated: the /metrics endpoint
# 404s unless METRICS_ENABLED is true, so default dev/test/CI behaviour is
# unchanged. When enabled behind an internal network, an optional METRICS_TOKEN
# adds a bearer-token gate (Prometheus passes it via the Authorization header).
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "false").lower() == "true"
METRICS_TOKEN = os.getenv("METRICS_TOKEN", "")

# Custom User Model
AUTH_USER_MODEL = "core.User"

# Application definition
INSTALLED_APPS = [
    # Django core apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    # Celery
    "django_celery_beat",
    "django_celery_results",
    # Our apps
    "openshiksha.apps.core",
    "openshiksha.apps.edge",
    "openshiksha.apps.cabinet",
    "openshiksha.apps.api",
    "openshiksha.apps.ai",
    "openshiksha.apps.concierge",
    "openshiksha.apps.lodge",
    "openshiksha.apps.announcements",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Request-correlation id (OBS-4) — early so the id is available to every
    # downstream middleware/view/log record for the whole request lifecycle.
    "openshiksha.apps.core.middleware.RequestIDMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS - must be before CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "openshiksha.urls"

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

WSGI_APPLICATION = "openshiksha.wsgi.application"
ASGI_APPLICATION = "openshiksha.asgi.application"

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
import dj_database_url  # noqa: E402

DATABASES = {
    "default": dj_database_url.config(
        default="postgresql://openshiksha:openshiksha@localhost:5432/openshiksha_dev",
        conn_max_age=int(os.getenv("DB_CONN_MAX_AGE", 600)),
    )
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"  # Indian Standard Time
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS: list[Path] = []

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # For browsable API
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "openshiksha.apps.api.exceptions.custom_exception_handler",
    # Rate limiting (cache-backed; Redis in prod). Baseline anon/user limits on
    # every endpoint, plus tighter per-path limits on login/register (brute force)
    # and AI (paid LLM calls). See apps/api/throttling.py. Tests disable these
    # (settings/test.py) to stay fast and deterministic.
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "openshiksha.apps.api.throttling.PathScopedThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("THROTTLE_ANON", "60/min"),
        "user": os.getenv("THROTTLE_USER", "300/min"),
        "login": os.getenv("THROTTLE_LOGIN", "10/min"),
        "ai": os.getenv("THROTTLE_AI", "30/min"),
    },
}

# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(seconds=int(os.getenv("JWT_ACCESS_TOKEN_LIFETIME", 3600))),
    "REFRESH_TOKEN_LIFETIME": timedelta(seconds=int(os.getenv("JWT_REFRESH_TOKEN_LIFETIME", 604800))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": os.getenv("JWT_ALGORITHM", "HS256"),
    "SIGNING_KEY": os.getenv("JWT_SECRET_KEY", SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
CORS_ALLOW_CREDENTIALS = True

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Periodic tasks (Celery beat)
from celery.schedules import crontab  # noqa: E402

CELERY_BEAT_SCHEDULE = {
    "send-due-date-reminders": {
        "task": "openshiksha.apps.core.tasks.send_due_date_reminders",
        # Daily at 06:00 (CELERY_TIMEZONE = Asia/Kolkata). Reminds students about
        # assignments due in the next 24h.
        "schedule": crontab(hour=6, minute=0),
        "kwargs": {"window_hours": 24},
    },
    "weekly-parent-summaries": {
        "task": "openshiksha.apps.ai.tasks.enqueue_weekly_parent_summaries",
        # Monday 07:00 (Asia/Kolkata). Generates and emails last week's progress
        # summary to every parent for each of their children.
        "schedule": crontab(hour=7, minute=0, day_of_week="monday"),
    },
}

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Caching
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "openshiksha",
        "TIMEOUT": 300,  # 5 minutes default
    }
}

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# AI / LLM Configuration
# Provider cascade for natural language explanations:
#   1. Anthropic Claude  — set ANTHROPIC_API_KEY
#   2. Google Gemma 4    — set GOOGLE_AI_API_KEY (free via Google AI Studio)
#   3. Ollama (local)    — set OLLAMA_BASE_URL or run Ollama at localhost:11434
#   4. Stub              — plain text fallback (dev/test, no keys needed)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Email Configuration
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 25))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "OpenShiksha <noreply@openshiksha.edu.in>")
EMAIL_SUBJECT_PREFIX = "[OpenShiksha] "

# Branded HTML email assets. Mail clients can't load relative/app-local URLs, so
# the logo and CTA links must be absolute. Override per environment (e.g. point
# at the cloudflared tunnel for a local demo, or the real domain in prod).
EMAIL_LOGO_URL = os.getenv("EMAIL_LOGO_URL", "https://openshiksha.org/brand/logo-orange.png")
EMAIL_APP_URL = os.getenv("EMAIL_APP_URL", "https://openshiksha.org")


# Web Push (VAPID) — the mobile-native notification channel for the PWA. Keys are
# blank by default so dev/CI without VAPID keys simply disable push (the API
# returns an empty public key and the frontend hides the affordance) rather than
# erroring. Generate a keypair with: ``python -m py_vapid`` (or pywebpush docs).
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_ADMIN_EMAIL = os.getenv("VAPID_ADMIN_EMAIL", "admin@openshiksha.org")


# ADMINS — recipients of mail_admins() calls (concierge enquiries, error
# notifications). Set OPENSHIKSHA_ADMIN_EMAILS to a comma-separated list,
# optionally with "Name <email>" entries:
#   OPENSHIKSHA_ADMIN_EMAILS="Ops Team <ops@example.com>,founder@example.com"
# Without this, mail_admins() silently no-ops — enquiries still land in the
# DB (admin at /django-admin/concierge/enquirer/) but no email is sent.
def _parse_admin_emails(raw: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if "<" in entry and entry.endswith(">"):
            name, _, addr = entry.partition("<")
            out.append((name.strip(), addr.rstrip(">").strip()))
        else:
            out.append(("", entry))
    return out


ADMINS = _parse_admin_emails(os.getenv("OPENSHIKSHA_ADMIN_EMAILS", ""))
MANAGERS = ADMINS

# Logging Configuration
# Ensure the logs directory exists (CI environments and fresh checkouts won't have it)
(BASE_DIR / "logs").mkdir(exist_ok=True)

# Log format: "text" (default — today's human-readable formatters, byte-for-byte
# unchanged) or "json" (one JSON object per line, for log aggregators). OBS-4.
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")
_CONSOLE_FORMATTER = "json" if LOG_FORMAT == "json" else "simple"
_FILE_FORMATTER = "json" if LOG_FORMAT == "json" else "verbose"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        # Injects the per-request correlation id onto every record (OBS-4).
        "request_id": {"()": "openshiksha.apps.core.logging_utils.RequestIDFilter"},
    },
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
        "json": {
            "()": "openshiksha.apps.core.logging_utils.JSONFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": _CONSOLE_FORMATTER,
            "filters": ["request_id"],
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "openshiksha.log",
            "maxBytes": 1024 * 1024 * 10,  # 10 MB
            "backupCount": 5,
            "formatter": _FILE_FORMATTER,
            "filters": ["request_id"],
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# API Documentation (drf-spectacular)
SPECTACULAR_SETTINGS = {
    "TITLE": "OpenShiksha API",
    "DESCRIPTION": "Modern educational platform API",
    "VERSION": "2.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# Cabinet Service Configuration
CABINET_API_URL = os.getenv("CABINET_API_URL", "http://localhost:9000")
CABINET_API_KEY = os.getenv("CABINET_API_KEY", "dev-cabinet-key")
CABINET_TIMEOUT = int(os.getenv("CABINET_TIMEOUT", 30))
