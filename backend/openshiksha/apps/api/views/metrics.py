"""
Prometheus ``/metrics`` exposition view (MET-1, Observability Batch 2).

Strictly env-gated: returns **404** unless ``settings.METRICS_ENABLED`` is true, so
the endpoint is invisible (byte-for-byte today's behaviour) in dev / test / CI.
When enabled it is meant to live on an internal network and be scraped by
Prometheus; an optional ``METRICS_TOKEN`` adds a bearer-token gate for defence in
depth. No auth framework, no DB — kept cheap like the health probes.
"""

import hmac

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

from openshiksha.apps.core import metrics


def _token_ok(request) -> bool:
    """True if no token is configured, or the request carries the matching bearer."""
    expected = getattr(settings, "METRICS_TOKEN", "") or ""
    if not expected:
        return True
    auth = request.headers.get("Authorization", "")
    presented = auth[7:] if auth.startswith("Bearer ") else ""
    # Constant-time compare so the gate can't be probed by timing.
    return hmac.compare_digest(presented, expected)


@csrf_exempt
def metrics_view(request):
    """Serve the Prometheus text exposition when metrics are enabled.

    GET /metrics/  →  404 (disabled), 403 (bad token), or 200 text exposition.
    """
    if not metrics.metrics_enabled():
        return HttpResponseNotFound("metrics disabled")
    if not _token_ok(request):
        return HttpResponseForbidden("forbidden")
    payload, content_type = metrics.render_latest()
    return HttpResponse(payload, content_type=content_type)
