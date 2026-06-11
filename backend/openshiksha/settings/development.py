"""
Development-specific Django settings for OpenShiksha
"""

from .base import *  # noqa: F403

# DEBUG mode ON for development
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Additional apps for development
INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
    "debug_toolbar",
]

# Debug Toolbar Middleware
MIDDLEWARE += [  # noqa: F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Debug Toolbar Configuration
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Logging - More verbose in development
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405  # type: ignore[index]
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # noqa: F405  # type: ignore[index]
# django.template at DEBUG floods the console with internal VariableDoesNotExist
# tracebacks every time Django renders its own technical 404/500 pages — pages
# whose templates probe optional context keys by design. The flood buries the
# *real* exception several screens up, so keep this one logger at INFO.
LOGGING["loggers"]["django.template"] = {  # noqa: F405  # type: ignore[index]
    "handlers": ["console"],
    "level": "INFO",
    "propagate": False,
}

# Email - Console backend for development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable some security features for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# Django Extensions Configuration
SHELL_PLUS = "ipython"
SHELL_PLUS_PRINT_SQL = True

# Celery - Eager execution in development (synchronous)
CELERY_TASK_ALWAYS_EAGER = True  # Synchronous task execution in development (no Celery worker needed)
CELERY_TASK_EAGER_PROPAGATES = True

print("[OK] Development settings loaded")
