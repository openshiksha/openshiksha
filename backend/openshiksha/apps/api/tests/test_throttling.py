"""Rate-limiting (throttle) tests.

The suite disables throttling globally (settings/test.py) so the ~370 other tests
don't trip 429s. Here we re-enable it with tiny rates via ``override_settings`` and
assert the sensitive endpoints actually cut over to HTTP 429.
"""

import pytest

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient

from openshiksha.apps.core.models import User, UserRole

# Re-enable throttling with very low rates so a handful of requests trips it.
_THROTTLED = {
    **settings.REST_FRAMEWORK,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "openshiksha.apps.api.throttling.PathScopedThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "1000/min",  # high — we're testing the scoped limits, not the baseline
        "user": "1000/min",
        "login": "3/min",
        "ai": "2/min",
    },
}

LOGIN_URL = "/api/v1/auth/login/"
AI_URL = "/api/v1/ai/learning-gaps/"


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@override_settings(REST_FRAMEWORK=_THROTTLED)
@pytest.mark.django_db
def test_login_is_rate_limited():
    client = APIClient()
    payload = {"username": "nobody", "password": "wrong"}

    # First 3 attempts go through to the view (invalid creds -> 401), counting
    # against the per-IP login budget.
    for _ in range(3):
        resp = client.post(LOGIN_URL, payload, format="json")
        assert resp.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    # The 4th is throttled before the view runs.
    resp = client.post(LOGIN_URL, payload, format="json")
    assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@override_settings(REST_FRAMEWORK=_THROTTLED)
@pytest.mark.django_db
def test_ai_endpoints_are_rate_limited():
    user = User.objects.create_user(username="ai_user", password="pw12345", role=UserRole.STUDENT)
    client = APIClient()
    client.force_authenticate(user=user)

    for _ in range(2):
        resp = client.get(AI_URL)
        assert resp.status_code != status.HTTP_429_TOO_MANY_REQUESTS

    resp = client.get(AI_URL)
    assert resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS


@override_settings(REST_FRAMEWORK=_THROTTLED)
@pytest.mark.django_db
def test_non_sensitive_path_not_scoped_throttled():
    """A normal endpoint isn't subject to the tight login/ai scopes — only the
    generous baseline — so a few requests never 429."""
    user = User.objects.create_user(username="plain_user", password="pw12345", role=UserRole.STUDENT)
    client = APIClient()
    client.force_authenticate(user=user)

    for _ in range(5):
        resp = client.get("/api/v1/users/me/")
        assert resp.status_code != status.HTTP_429_TOO_MANY_REQUESTS
