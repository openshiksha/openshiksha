"""
URL Configuration for OpenShiksha

The `urlpatterns` list routes URLs to views.
"""

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def healthz(_request):
    """Liveness/readiness probe target for k8s + Docker HEALTHCHECK.

    Returns 200 OK as long as the WSGI/ASGI app is wired up — does NOT hit the
    DB or Redis on purpose. A failing DB shouldn't take the pod down (it'll
    just return 5xx to /api/ requests), and a Redis hiccup shouldn't either.
    DB-aware probes belong on a separate /readyz that the LB can use as a
    drain signal; we keep this probe path cheap and reliable.
    """
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    # Cheap liveness probe — no DB / Redis / auth. See healthz() above.
    path("healthz/", healthz, name="healthz"),
    # Django Admin
    path("admin/", admin.site.urls),
    # API v1 endpoints
    path("api/v1/", include("openshiksha.apps.api.urls")),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug Toolbar — guard on INSTALLED_APPS, not just DEBUG. In debug_toolbar
    # v5+ importing its URLconf also loads a model (HistoryEntry), which raises
    # if the app isn't registered. The test settings run with DEBUG=True but
    # drop debug_toolbar from INSTALLED_APPS, so an unconditional import breaks
    # `manage.py check` and test collection. Only mount it when installed.
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

# Custom admin configuration
admin.site.site_header = "OpenShiksha Administration"
admin.site.site_title = "OpenShiksha Admin"
admin.site.index_title = "Welcome to OpenShiksha Admin Portal"
