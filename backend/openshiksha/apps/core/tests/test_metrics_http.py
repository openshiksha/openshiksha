"""
Tests for the gated HTTP request-metrics middleware (MET-4).

Verifies the gated-ON path (a request through the stack increments the counter and
observes a latency sample) and the gated-OFF path (the middleware is a pure
pass-through that touches no metric object).
"""

from prometheus_client import REGISTRY

from django.urls import reverse

from openshiksha.apps.core.middleware import MetricsMiddleware


def _requests_total(method="GET", status_class="2xx"):
    """Current counter value (or 0.0 if the series has no samples yet)."""
    value = REGISTRY.get_sample_value(
        "openshiksha_http_requests_total", {"method": method, "status_class": status_class}
    )
    return value or 0.0


class TestMetricsMiddlewareEnabled:
    def test_request_increments_counter_and_observes_latency(self, client, settings):
        settings.METRICS_ENABLED = True
        before = _requests_total()
        # Drive one request through the full middleware stack.
        assert client.get(reverse("healthz")).status_code == 200
        after = _requests_total()
        assert after == before + 1.0

        # A latency sample was recorded for GET.
        count = REGISTRY.get_sample_value("openshiksha_http_request_duration_seconds_count", {"method": "GET"})
        assert count is not None and count >= 1.0

    def test_metrics_endpoint_exposes_http_family(self, client, settings):
        settings.METRICS_ENABLED = True
        client.get(reverse("healthz"))
        body = client.get(reverse("metrics")).content.decode()
        assert "openshiksha_http_requests_total" in body
        assert "openshiksha_http_request_duration_seconds_bucket" in body


class TestMetricsMiddlewareDisabled:
    def test_pure_passthrough_records_nothing(self, settings):
        settings.METRICS_ENABLED = False
        before = _requests_total(status_class="2xx")

        calls = {"n": 0}

        def get_response(request):
            calls["n"] += 1
            return _FakeResponse(200)

        mw = MetricsMiddleware(get_response)

        class _Req:
            method = "GET"

        result = mw(_Req())
        assert calls["n"] == 1  # downstream was called (pass-through)
        assert isinstance(result, _FakeResponse)
        # No counter movement while disabled.
        assert _requests_total(status_class="2xx") == before


class _FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code
