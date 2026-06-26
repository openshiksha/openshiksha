"""
Error tracking / observability wiring (OBS-3).

Sentry is **strictly env-gated**: it initialises only when ``SENTRY_DSN`` is set,
so dev / test / local runs never send events and behaviour is byte-for-byte
today's. Factored out of ``settings/production.py`` so the init + scrubber are
unit-testable without importing the whole settings module.
"""

import logging
import os
import re

logger = logging.getLogger("apps")

# Data keys whose *value* must never leave the process.
_SENSITIVE_KEY_RE = re.compile(r"password|token|secret|api[_-]?key|anthropic|authorization", re.IGNORECASE)

# Request headers stripped wholesale.
_SENSITIVE_HEADERS = {"authorization", "cookie", "x-api-key"}

_FILTERED = "[Filtered]"


def _scrub_mapping(data):
    """Recursively replace sensitive values in a dict; non-dicts pass through."""
    if not isinstance(data, dict):
        return data
    cleaned = {}
    for key, value in data.items():
        if isinstance(key, str) and _SENSITIVE_KEY_RE.search(key):
            cleaned[key] = _FILTERED
        elif isinstance(value, dict):
            cleaned[key] = _scrub_mapping(value)
        else:
            cleaned[key] = value
    return cleaned


def _scrub(event, _hint):
    """Sentry ``before_send`` hook — strip secrets before an event is transmitted.

    Removes sensitive request headers (Authorization/Cookie/X-API-Key), cookies,
    and any data/extra key matching ``password|token|secret|api_key|anthropic``.
    Returns the mutated event (Sentry sends ``None`` events nowhere, but we always
    keep the event — just sanitised).
    """
    request = event.get("request")
    if isinstance(request, dict):
        headers = request.get("headers")
        if isinstance(headers, dict):
            request["headers"] = {
                k: (_FILTERED if (k.lower() in _SENSITIVE_HEADERS or _SENSITIVE_KEY_RE.search(k)) else v)
                for k, v in headers.items()
            }
        if "cookies" in request:
            request["cookies"] = _FILTERED
        if isinstance(request.get("data"), dict):
            request["data"] = _scrub_mapping(request["data"])

    if isinstance(event.get("extra"), dict):
        event["extra"] = _scrub_mapping(event["extra"])

    return event


def init_sentry():
    """Initialise Sentry iff ``SENTRY_DSN`` is set. Returns ``True`` if initialised.

    Lazy-imports the SDK so the dependency is never touched when Sentry is
    disabled. Django/Celery/Redis integrations are wired; PII is off; the
    ``before_send`` scrubber strips secrets.
    """
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.redis import RedisIntegration
    except ImportError:
        logger.warning("SENTRY_DSN is set but sentry-sdk is not installed; error tracking disabled.")
        return False

    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration(), CeleryIntegration(), RedisIntegration()],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0")),
        send_default_pii=False,
        environment=os.getenv("ENVIRONMENT", "production"),
        release=os.getenv("GIT_SHA") or None,
        before_send=_scrub,
    )
    logger.info("Sentry error tracking initialised (environment=%s).", os.getenv("ENVIRONMENT", "production"))
    return True
