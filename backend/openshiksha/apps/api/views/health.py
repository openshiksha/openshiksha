"""
Health check endpoints
"""

from django.core.cache import cache
from django.db import connection
from django.urls import path
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


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
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["cache"] = f"error: {str(e)}"

    status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

    return Response(health_status, status=status_code)


urlpatterns = [
    path("", health_check, name="health_check"),
]
