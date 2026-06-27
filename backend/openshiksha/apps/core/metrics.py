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
from datetime import timedelta

from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Gauge, Histogram, generate_latest
from prometheus_client.core import GaugeMetricFamily

from django.conf import settings

logger = logging.getLogger("apps")

# HTTP request metrics (MET-4), recorded by ``MetricsMiddleware``. Module-level
# singletons (defined once at import) so they're never recreated per request,
# which would raise a "Duplicated timeseries" registry error. Labelled by method
# and status class (2xx/3xx/4xx/5xx) only — never raw path — to avoid unbounded
# cardinality from per-id URLs. The middleware only records when metrics are
# enabled, so these stay sample-less (zero overhead) by default.
http_requests_total = Counter(
    "openshiksha_http_requests",
    "HTTP requests handled, by method and status class.",
    ["method", "status_class"],
)
http_request_duration_seconds = Histogram(
    "openshiksha_http_request_duration_seconds",
    "HTTP request latency in seconds, by method.",
    ["method"],
)

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


# Non-terminal Celery states — a task in any of these is still in the queue or
# mid-flight, i.e. it contributes to "oldest pending" staleness.
_PENDING_TASK_STATES = ("PENDING", "RECEIVED", "STARTED", "RETRY")

# How far back the task-health window looks, so the COUNT stays bounded.
_TASK_WINDOW = timedelta(hours=24)


def _celery_results_in_db() -> bool:
    """True only when Celery persists results to the DB (``django_celery_results``).

    The default result backend is Redis, where the ``TaskResult`` table stays
    empty — emitting task gauges then would be a *misleading constant zero*. So
    MET-3 stays a documented no-op unless ``CELERY_RESULT_BACKEND`` is the
    database backend; flipping it lights the gauges up automatically.
    """
    backend = str(getattr(settings, "CELERY_RESULT_BACKEND", "") or "")
    return "django-db" in backend or "django_celery_results" in backend


class TaskMetricsCollector:
    """Scrape-time Celery health derived from ``django_celery_results.TaskResult`` (MET-3).

    Celery runs as a **separate worker process**, so in-worker counters can't be
    scraped from the web process without a pushgateway/second exporter (out of
    scope per the operability bar). Instead we read task health on-scrape from the
    already-installed ``TaskResult`` table — but only when results are actually
    persisted there (see ``_celery_results_in_db``).

    Gauges (windowed to the last 24h by ``date_created``):
      * ``openshiksha_celery_tasks{status=...}`` — task counts by status,
      * ``openshiksha_celery_oldest_pending_seconds`` — age of the oldest
        non-terminal task (``0`` when none) — the async grade-queue-staleness analogue.
    """

    def collect(self):
        if not _celery_results_in_db():
            return
        try:
            yield from self._collect()
        except Exception:  # pragma: no cover - defensive; never break a scrape
            logger.warning("metrics: TaskMetricsCollector failed; skipping celery gauges", exc_info=True)

    def _collect(self):
        from django_celery_results.models import TaskResult

        from django.db.models import Count
        from django.utils import timezone

        now = timezone.now()
        since = now - _TASK_WINDOW

        by_status = GaugeMetricFamily(
            "openshiksha_celery_tasks",
            "Celery task counts by status over the last 24h (requires the django-db result backend).",
            labels=["status"],
        )
        for row in TaskResult.objects.filter(date_created__gte=since).values("status").annotate(n=Count("id")):
            by_status.add_metric([row["status"] or "UNKNOWN"], row["n"])
        yield by_status

        oldest = (
            TaskResult.objects.filter(date_created__gte=since, status__in=_PENDING_TASK_STATES)
            .order_by("date_created")
            .values_list("date_created", flat=True)
            .first()
        )
        age = (now - oldest).total_seconds() if oldest else 0.0
        yield GaugeMetricFamily(
            "openshiksha_celery_oldest_pending_seconds",
            "Age in seconds of the oldest non-terminal Celery task in the window (0 when none).",
            value=age,
        )


# Lazy, idempotent registration of the on-scrape collectors. Guarded so we only
# touch the registry on a real (enabled) scrape and never double-register.
_collectors_registered = False


def _ensure_collectors():
    global _collectors_registered
    if _collectors_registered:
        return
    REGISTRY.register(BusinessMetricsCollector())
    REGISTRY.register(TaskMetricsCollector())
    _collectors_registered = True


def metrics_enabled() -> bool:
    """Whether the ``/metrics`` endpoint should serve (env-gated, default off)."""
    return bool(getattr(settings, "METRICS_ENABLED", False))


def render_latest() -> tuple[bytes, str]:
    """Return ``(payload, content_type)`` for the Prometheus text exposition."""
    _refresh_build_info()
    _ensure_collectors()
    return generate_latest(), CONTENT_TYPE_LATEST
