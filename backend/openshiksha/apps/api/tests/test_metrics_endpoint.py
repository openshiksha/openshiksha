"""
Tests for the env-gated Prometheus /metrics endpoint (MET-1).

Covers both the gated-OFF default (404, behaviour byte-for-byte today's) and the
gated-ON path (exposition + optional bearer-token gate).
"""

from django.test import override_settings
from django.urls import reverse


class TestMetricsGating:
    def test_disabled_by_default_returns_404(self, client):
        # No override → settings.METRICS_ENABLED is the default (False in test settings).
        response = client.get(reverse("metrics"))
        assert response.status_code == 404

    @override_settings(METRICS_ENABLED=True)
    def test_enabled_returns_prometheus_exposition(self, client):
        response = client.get(reverse("metrics"))
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/plain")
        body = response.content.decode()
        # Valid Prometheus text exposition (HELP/TYPE banners present).
        assert "# HELP" in body
        assert "# TYPE" in body
        # build_info series is always present and carries the live identity.
        assert "openshiksha_build_info" in body

    @override_settings(METRICS_ENABLED=True, APP_VERSION="9.9.9", ENVIRONMENT="prod")
    def test_build_info_reflects_settings(self, client):
        body = client.get(reverse("metrics")).content.decode()
        assert 'version="9.9.9"' in body
        assert 'environment="prod"' in body

    def test_endpoint_is_public_no_auth_redirect(self, client):
        # Even disabled, it must not 302 to login — it's a probe-style path.
        response = client.get(reverse("metrics"))
        assert response.status_code == 404


class TestMetricsTokenGate:
    @override_settings(METRICS_ENABLED=True, METRICS_TOKEN="s3cret")
    def test_missing_token_forbidden(self, client):
        assert client.get(reverse("metrics")).status_code == 403

    @override_settings(METRICS_ENABLED=True, METRICS_TOKEN="s3cret")
    def test_wrong_token_forbidden(self, client):
        response = client.get(reverse("metrics"), HTTP_AUTHORIZATION="Bearer nope")
        assert response.status_code == 403

    @override_settings(METRICS_ENABLED=True, METRICS_TOKEN="s3cret")
    def test_correct_token_allowed(self, client):
        response = client.get(reverse("metrics"), HTTP_AUTHORIZATION="Bearer s3cret")
        assert response.status_code == 200

    @override_settings(METRICS_ENABLED=True, METRICS_TOKEN="")
    def test_no_token_configured_allows_anonymous(self, client):
        assert client.get(reverse("metrics")).status_code == 200
