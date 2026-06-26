"""
Health check endpoints
"""

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def deep_health_status():
    """Run the deep readiness check: DB connection + cache round-trip.

    Returns a ``(status_dict, healthy)`` tuple. Shared by the DRF
    ``/api/v1/health/`` endpoint and the top-level ``/readyz/`` k8s readiness
    probe so the two never drift apart.
    """
    health_status = {
        "status": "healthy",
        "database": "disconnected",
        "cache": "disconnected",
    }

    # Check database connection
    try:
        connection.ensure_connection()
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"error: {str(e)}"

    # Check cache connection
    try:
        cache.set("health_check", "ok", 10)
        if cache.get("health_check") == "ok":
            health_status["cache"] = "connected"
        else:
            health_status["status"] = "unhealthy"
            health_status["cache"] = "error: round-trip mismatch"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["cache"] = f"error: {str(e)}"

    return health_status, health_status["status"] == "healthy"


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify service is running

    GET /api/v1/health/

    Returns:
        - status: healthy/unhealthy
        - database: connected/disconnected
        - cache: connected/disconnected
    """
    health_status, healthy = deep_health_status()
    status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(health_status, status=status_code)


@csrf_exempt
def readyz(_request):
    """Deep readiness probe target for the k8s readinessProbe / LB drain signal.

    Unlike the cheap ``/healthz/`` liveness probe, this runs the same DB + cache
    check as ``/api/v1/health/`` and returns 503 if either is down — so a pod
    with a dead DB is drained from the load balancer (no traffic) instead of
    being killed and restart-looped (that's the liveness probe's job).

    Mounted at the top level (``/readyz/``) as a plain, auth-free, DB-aware view.
    """
    health_status, healthy = deep_health_status()
    status_code = 200 if healthy else 503
    return JsonResponse(health_status, status=status_code)


urlpatterns = [
    path("", health_check, name="health_check"),
]
