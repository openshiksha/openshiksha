"""
Test-specific Django settings for OpenShiksha.

Uses SQLite so tests can run without a running PostgreSQL instance.
Intended for local test runs and CI environments without Docker.

Usage:
  pytest --ds=openshiksha.settings.test
  or set DJANGO_SETTINGS_MODULE=openshiksha.settings.test
"""

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Override DB to SQLite — no PostgreSQL required for unit/integration tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Silence password hashing — much faster for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Skip debug toolbar and extensions — not needed for tests
INSTALLED_APPS = [
    app
    for app in INSTALLED_APPS  # noqa: F405
    if app
    not in (
        "django_extensions",
        "debug_toolbar",
    )
]
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]  # noqa: F405

# Celery: run tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Silence Redis cache errors in tests — use local memory cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Disable API rate limiting in the suite — tests fire many requests and the
# throttle cache would otherwise accumulate and cause spurious 429s. The throttle
# behaviour itself is covered by apps/api/tests/test_throttling.py, which
# re-enables it via override_settings.
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405


# Suppress migration output during tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


# Don't disable migrations — we need them for the test DB schema
# MIGRATION_MODULES = DisableMigrations()
