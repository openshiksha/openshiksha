"""
Tests for the Celery task-health gauges (MET-3).

Derived on-scrape from ``django_celery_results.TaskResult``. Because the table is
only meaningful when Celery persists results to the DB, the gauges are gated on
the result backend — verified here both ways.
"""

from datetime import timedelta

import pytest
from django_celery_results.models import TaskResult

from django.urls import reverse
from django.utils import timezone


@pytest.fixture
def db_result_backend(db, settings):
    settings.METRICS_ENABLED = True
    settings.CELERY_RESULT_BACKEND = "django-db"
    return settings


def _seed_tasks():
    now = timezone.now()
    TaskResult.objects.create(task_id="ok-1", task_name="t.ok", status="SUCCESS", date_created=now, date_done=now)
    TaskResult.objects.create(task_id="ok-2", task_name="t.ok", status="SUCCESS", date_created=now, date_done=now)
    TaskResult.objects.create(task_id="bad-1", task_name="t.bad", status="FAILURE", date_created=now, date_done=now)
    # A non-terminal task ~5 min old → drives oldest_pending_seconds > 0.
    # date_created is auto_now_add, so backdate it via .update() (bypasses it).
    pending = TaskResult.objects.create(task_id="pending-1", task_name="t.slow", status="STARTED")
    TaskResult.objects.filter(pk=pending.pk).update(date_created=now - timedelta(minutes=5))


def _scrape(client):
    response = client.get(reverse("metrics"))
    assert response.status_code == 200
    return response.content.decode()


class TestTaskGauges:
    def test_counts_by_status(self, client, db_result_backend):
        _seed_tasks()
        body = _scrape(client)
        assert 'openshiksha_celery_tasks{status="SUCCESS"} 2.0' in body
        assert 'openshiksha_celery_tasks{status="FAILURE"} 1.0' in body

    def test_oldest_pending_seconds_positive(self, client, db_result_backend):
        _seed_tasks()
        body = _scrape(client)
        line = next(ln for ln in body.splitlines() if ln.startswith("openshiksha_celery_oldest_pending_seconds "))
        value = float(line.split()[1])
        # ~5 minutes old; allow generous slack for clock/window.
        assert value >= 200.0

    def test_oldest_pending_zero_when_none(self, client, db_result_backend):
        now = timezone.now()
        TaskResult.objects.create(task_id="ok", task_name="t.ok", status="SUCCESS", date_created=now, date_done=now)
        body = _scrape(client)
        assert "openshiksha_celery_oldest_pending_seconds 0.0" in body

    def test_gauges_absent_with_redis_backend(self, client, db, settings):
        # Default (redis) result backend ⇒ TaskResult is not authoritative ⇒ no
        # task gauges, even if rows happen to exist (honest no-op, not a false 0).
        settings.METRICS_ENABLED = True
        settings.CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
        _seed_tasks()
        body = _scrape(client)
        assert "openshiksha_celery_tasks" not in body
        assert "openshiksha_celery_oldest_pending_seconds" not in body
