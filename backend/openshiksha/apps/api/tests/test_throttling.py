"""Rate-limiting (throttle) tests.

DRF binds throttle classes/rates onto the views at import time, so toggling them
via ``override_settings`` after the fact doesn't take effect. The suite therefore
keeps the throttle *classes* bound but sets every rate to ``None`` (a no-op — see
settings/test.py); here we re-enable a single scope by monkeypatching its rate on
the already-bound throttle class, which the per-request ``get_rate()`` reads live.
"""

import pytest

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from openshiksha.apps.core.models import User, UserRole

LOGIN_URL = "/api/v1/auth/login/"
AI_URL = "/api/v1/ai/learning-gaps/"
PLAIN_URL = "/api/v1/users/me/"


@pytest.fixture
def tight_rates(monkeypatch):
    """Re-enable the login/ai scopes with tiny rates; leave anon/user off so they
    don't interfere. THROTTLE_RATES is shared by every throttle class, and
    monkeypatch restores it afterwards."""
    cache.clear()
    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, "login", "3/min")
    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, "ai", "2/min")
    yield
    cache.clear()


@pytest.mark.django_db
def test_login_is_rate_limited(tight_rates):
    client = APIClient()
    payload = {"username": "nobody", "password": "wrong"}

    # First 3 attempts reach the view (invalid creds -> 401) but count against the
    # per-IP login budget; the 4th is throttled before the view runs.
    for _ in range(3):
        resp = client.post(LOGIN_URL, payload, format="json")
        assert resp.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    resp = client.post(LOGIN_URL, payload, format="json")
    assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_ai_endpoints_are_rate_limited(tight_rates):
    user = User.objects.create_user(username="ai_user", password="pw12345", role=UserRole.STUDENT)
    client = APIClient()
    client.force_authenticate(user=user)

    for _ in range(2):
        resp = client.get(AI_URL)
        assert resp.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    resp = client.get(AI_URL)
    assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@pytest.mark.django_db
def test_non_sensitive_path_not_scoped_throttled(tight_rates):
    """A normal endpoint isn't subject to the tight login/ai scopes (anon/user
    rates stay off), so repeated requests never 429."""
    user = User.objects.create_user(username="plain_user", password="pw12345", role=UserRole.STUDENT)
    client = APIClient()
    client.force_authenticate(user=user)

    for _ in range(5):
        resp = client.get(PLAIN_URL)
        assert resp.status_code != status.HTTP_429_TOO_MANY_REQUESTS
