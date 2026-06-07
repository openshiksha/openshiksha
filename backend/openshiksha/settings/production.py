"""
Production-specific Django settings for OpenShiksha
"""

from .base import *  # noqa: F403

# DEBUG mode OFF for production
DEBUG = False

# SECURITY WARNING: Update ALLOWED_HOSTS with your production domain
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")  # noqa: F405

# Security Settings
SECURE_SSL_REDIRECT = True
# When deployed behind a TLS-terminating ingress (Traefik on k3s, ALB, etc.),
# Django sees plain HTTP at the socket. It has to trust the proxy's
# X-Forwarded-Proto header to know the original request was HTTPS, otherwise
# SECURE_SSL_REDIRECT triggers an infinite redirect loop. Only safe when the
# ingress strips this header from client input (Traefik does by default).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Only JSON renderer in production (no browsable API)
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
]

# Logging - Less verbose in production
LOGGING["root"]["level"] = "WARNING"  # noqa: F405  # type: ignore[index]
LOGGING["loggers"]["django"]["level"] = "WARNING"  # noqa: F405  # type: ignore[index]
LOGGING["loggers"]["apps"]["level"] = "INFO"  # noqa: F405  # type: ignore[index]

# Email - Use real email backend in production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Static files - Use WhiteNoise or CDN in production
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Database - Production database should be managed/replicated
DATABASES["default"]["CONN_MAX_AGE"] = 600  # noqa: F405

# Celery - Production configuration
CELERY_TASK_ALWAYS_EAGER = False

# Cache - Use Redis with longer timeouts
CACHES["default"]["TIMEOUT"] = 600  # 10 minutes  # noqa: F405

print("⚠️  Production settings loaded - ensure all environment variables are set!")
