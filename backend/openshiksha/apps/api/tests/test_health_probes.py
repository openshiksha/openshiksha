"""
Tests for the k8s probe endpoints (OBS-1).

Covers:
- /healthz/ — cheap liveness probe (no DB / cache touched)
- /readyz/  — deep readiness probe (DB + cache check; 503 on failure)
"""

import pytest

from django.test import Client
from django.urls import reverse


@pytest.fixture
def client():
    return Client()


# ---------------------------------------------------------------------------
# /healthz/ — cheap liveness
# ---------------------------------------------------------------------------


class TestHealthz:
    def test_healthz_returns_200(self, client):
        response = client.get(reverse("healthz"))
        assert response.status_code == 200
        assert response.content == b"ok"

    def test_healthz_does_no_db_queries(self, client, db, django_assert_num_queries):
        """Liveness must stay cheap — it must not hit the database."""
        with django_assert_num_queries(0):
            client.get(reverse("healthz"))

    def test_healthz_public(self, client):
        response = client.get(reverse("healthz"))
        assert response.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# /readyz/ — deep readiness
# ---------------------------------------------------------------------------


class TestReadyz:
    def test_readyz_returns_200_when_up(self, client, db):
        response = client.get(reverse("readyz"))
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["database"] == "connected"
        assert body["cache"] == "connected"

    def test_readyz_public(self, client, db):
        response = client.get(reverse("readyz"))
        assert response.status_code not in (401, 403)

    def test_readyz_503_when_check_unhealthy(self, client, monkeypatch):
        """When the deep check reports unhealthy the probe returns 503 (drain)."""
        from openshiksha.apps.api.views import health

        monkeypatch.setattr(
            health,
            "deep_health_status",
            lambda: ({"status": "unhealthy", "database": "error: db down", "cache": "connected"}, False),
        )
        response = client.get(reverse("readyz"))
        assert response.status_code == 503
        body = response.json()
        assert body["status"] == "unhealthy"


# ---------------------------------------------------------------------------
# deep_health_status() — unit (no live DB/cache touched)
# ---------------------------------------------------------------------------


class TestDeepHealthStatus:
    def test_reports_db_error(self, monkeypatch):
        from openshiksha.apps.api.views import health

        class FakeConn:
            def ensure_connection(self):
                raise RuntimeError("db down")

        class FakeCache:
            def set(self, *a, **k):
                return None

            def get(self, *a, **k):
                return "ok"

        monkeypatch.setattr(health, "connection", FakeConn())
        monkeypatch.setattr(health, "cache", FakeCache())
        status_dict, healthy = health.deep_health_status()
        assert healthy is False
        assert status_dict["status"] == "unhealthy"
        assert status_dict["database"].startswith("error:")

    def test_reports_cache_error(self, monkeypatch):
        from openshiksha.apps.api.views import health

        class FakeConn:
            def ensure_connection(self):
                return None

        class FakeCache:
            def set(self, *a, **k):
                raise RuntimeError("cache down")

            def get(self, *a, **k):
                return None

        monkeypatch.setattr(health, "connection", FakeConn())
        monkeypatch.setattr(health, "cache", FakeCache())
        status_dict, healthy = health.deep_health_status()
        assert healthy is False
        assert status_dict["status"] == "unhealthy"
        assert status_dict["cache"].startswith("error:")
