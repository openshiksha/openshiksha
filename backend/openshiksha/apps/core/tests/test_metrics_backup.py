"""
Tests for the backup-freshness gauge and the record_backup_run command (BAK-4).

Seeds a ``BackupRun`` via the management command, scrapes the gated /metrics
endpoint, and asserts ``openshiksha_backup_age_seconds`` /
``openshiksha_backup_last_success_timestamp`` reflect it. Also asserts the honest
empty-history behaviour (age family omitted, timestamp 0) rather than a
misleading fresh-zero.
"""

from datetime import timedelta
from io import StringIO

import pytest

from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from openshiksha.apps.core.models import BackupRun


def _scrape(client):
    response = client.get(reverse("metrics"))
    assert response.status_code == 200
    return response.content.decode()


@pytest.mark.django_db
class TestBackupFreshnessGauge:
    def test_record_backup_run_writes_row(self):
        out = StringIO()
        call_command(
            "record_backup_run", "--status", "success", "--size", "4242", "--key", "postgres/x.dump.gz", stdout=out
        )
        run = BackupRun.objects.get()
        assert run.status == BackupRun.Status.SUCCESS
        assert run.size_bytes == 4242
        assert run.object_key == "postgres/x.dump.gz"
        assert "Recorded" in out.getvalue()

    def test_gauge_present_when_backup_recorded(self, client, settings):
        settings.METRICS_ENABLED = True
        BackupRun.objects.create(status=BackupRun.Status.SUCCESS, size_bytes=10)
        body = _scrape(client)
        assert "openshiksha_backup_age_seconds" in body
        assert "openshiksha_backup_last_success_timestamp" in body

    def test_age_is_reasonable(self, client, settings):
        settings.METRICS_ENABLED = True
        run = BackupRun.objects.create(status=BackupRun.Status.SUCCESS)
        BackupRun.objects.filter(pk=run.pk).update(created_at=timezone.now() - timedelta(hours=2))
        body = _scrape(client)
        line = next(ln for ln in body.splitlines() if ln.startswith("openshiksha_backup_age_seconds "))
        age = float(line.split()[1])
        # ~2h = 7200s; allow generous slack for test wall-clock.
        assert 7000 < age < 7400

    def test_empty_history_is_honest(self, client, settings):
        settings.METRICS_ENABLED = True
        body = _scrape(client)
        # No successful backup → age family OMITTED (not a fake-fresh 0)...
        assert "openshiksha_backup_age_seconds" not in body
        # ...and the last-success timestamp reads 0.
        assert "openshiksha_backup_last_success_timestamp 0.0" in body

    def test_failure_runs_do_not_count(self, client, settings):
        settings.METRICS_ENABLED = True
        BackupRun.objects.create(status=BackupRun.Status.FAILURE)
        body = _scrape(client)
        # Only failures recorded → still treated as "no successful backup".
        assert "openshiksha_backup_age_seconds" not in body
