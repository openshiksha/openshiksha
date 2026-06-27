"""
Prometheus metrics exposition (MET-1, Observability Batch 2).

Uses the **process-global default registry** (``prometheus_client.REGISTRY``) so
the runtime collectors prometheus_client auto-registers — process CPU/RSS, open
fds, Python GC — are exposed for free, and later increments' module-level
collectors (business gauges, request histogram) land on the same registry without
extra plumbing.

Process-model assumption (verified 2026-06-27): prod runs a **single daphne ASGI
process** (`CMD ["daphne", ...]` in Dockerfile.prod), so the default in-process
registry is correct — no ``PROMETHEUS_MULTIPROC_DIR`` is needed. A future move to
a multi-worker server (e.g. gunicorn with >1 worker) would require multiprocess
mode; this comment is the flag for that.

This module owns the ``openshiksha_build_info`` identity gauge and the rendering
helper the gated ``/metrics`` view calls. Nothing here runs unless the operator
sets ``METRICS_ENABLED=true`` and the endpoint is scraped.
"""

import os

from prometheus_client import CONTENT_TYPE_LATEST, Gauge, generate_latest

from django.conf import settings

# build_info: a value-1 gauge whose labels carry the live build identity — the
# conventional Prometheus pattern for static metadata. Registered on the default
# registry at import (harmless when metrics are disabled: it's just a series that
# is never scraped). The same identity the /api/v1/version/ endpoint surfaces.
_build_info = Gauge(
    "openshiksha_build_info",
    "Live build identity (always 1); version / git sha / environment ride on the labels.",
    ["version", "git_sha", "environment"],
)


def _refresh_build_info():
    """(Re)set the build_info series from current settings/env.

    Called at scrape time so test ``override_settings`` is reflected and the gauge
    never holds a stale label set (``.clear()`` drops prior label combinations).
    """
    _build_info.clear()
    _build_info.labels(
        version=getattr(settings, "APP_VERSION", "unknown"),
        git_sha=os.getenv("GIT_SHA", "unknown"),
        environment=getattr(settings, "ENVIRONMENT", "unknown"),
    ).set(1)


def metrics_enabled() -> bool:
    """Whether the ``/metrics`` endpoint should serve (env-gated, default off)."""
    return bool(getattr(settings, "METRICS_ENABLED", False))


def render_latest() -> tuple[bytes, str]:
    """Return ``(payload, content_type)`` for the Prometheus text exposition."""
    _refresh_build_info()
    return generate_latest(), CONTENT_TYPE_LATEST
