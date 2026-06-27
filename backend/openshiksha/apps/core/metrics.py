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

import logging
import os

from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Gauge, generate_latest
from prometheus_client.core import GaugeMetricFamily

from django.conf import settings

logger = logging.getLogger("apps")

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


class BusinessMetricsCollector:
    """Scrape-time, read-only DB gauges for product / operational signals (MET-2).

    Implements the ``prometheus_client`` custom-collector protocol: ``collect()``
    runs a handful of single ``COUNT`` queries at scrape time and yields gauges.
    Computing on-scrape (rather than event counters) keeps these stateless — no
    cross-process aggregation, no drift — which is the right pattern for
    "current size of X" business signals.

    Gauges (idiomatically *without* the ``_total`` counter suffix):
      * ``openshiksha_assignments_active`` — open, not past due,
      * ``openshiksha_submissions_pending_grading`` — grade-queue depth,
      * ``openshiksha_users{role=...}`` — accounts grouped by role,
      * ``openshiksha_classrooms`` / ``openshiksha_subjectrooms`` — totals.

    Registered lazily on the first real scrape (see ``_ensure_collectors``), so no
    DB work happens — and the collector is never even registered — while the
    endpoint is disabled (it 404s before ``render_latest`` is called).
    """

    def collect(self):
        # Defensive: a DB hiccup mid-scrape degrades to "no business gauges this
        # scrape" rather than 500-ing the metrics endpoint (build_info + runtime
        # series still serve).
        try:
            yield from self._collect()
        except Exception:  # pragma: no cover - defensive; never break a scrape
            logger.warning("metrics: BusinessMetricsCollector failed; skipping business gauges", exc_info=True)

    def _collect(self):
        from django.db.models import Count
        from django.utils import timezone

        from openshiksha.apps.core.models import Assignment, ClassRoom, SubjectRoom, Submission, User

        now = timezone.now()

        active = Assignment.objects.filter(closed_at__isnull=True, due_at__gte=now).count()
        yield GaugeMetricFamily(
            "openshiksha_assignments_active",
            "Assignments that are open (not closed) and not past their due date.",
            value=active,
        )

        pending = Submission.objects.filter(submitted_at__isnull=False, score__isnull=True).count()
        yield GaugeMetricFamily(
            "openshiksha_submissions_pending_grading",
            "Submitted submissions still awaiting a grade (grade-queue depth).",
            value=pending,
        )

        users = GaugeMetricFamily(
            "openshiksha_users",
            "User accounts grouped by role.",
            labels=["role"],
        )
        for row in User.objects.values("role").annotate(n=Count("id")):
            users.add_metric([row["role"] or "unknown"], row["n"])
        yield users

        yield GaugeMetricFamily(
            "openshiksha_classrooms",
            "Total classrooms.",
            value=ClassRoom.objects.count(),
        )
        yield GaugeMetricFamily(
            "openshiksha_subjectrooms",
            "Total subject rooms.",
            value=SubjectRoom.objects.count(),
        )


# Lazy, idempotent registration of the on-scrape collectors. Guarded so we only
# touch the registry on a real (enabled) scrape and never double-register.
_collectors_registered = False


def _ensure_collectors():
    global _collectors_registered
    if _collectors_registered:
        return
    REGISTRY.register(BusinessMetricsCollector())
    _collectors_registered = True


def metrics_enabled() -> bool:
    """Whether the ``/metrics`` endpoint should serve (env-gated, default off)."""
    return bool(getattr(settings, "METRICS_ENABLED", False))


def render_latest() -> tuple[bytes, str]:
    """Return ``(payload, content_type)`` for the Prometheus text exposition."""
    _refresh_build_info()
    _ensure_collectors()
    return generate_latest(), CONTENT_TYPE_LATEST
