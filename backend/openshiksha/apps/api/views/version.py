"""
Build-info endpoint (OBS-2).

Surfaces which build is live so an operator can correlate a prod incident with a
specific image. Deliberately trivial and DB-free; **never** returns secrets —
only the release version, git sha, build time, and environment name.
"""

import os

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def version_info(_request):
    """
    Build / version info.

    GET /api/v1/version/

    Returns:
        - version:     human-facing release (settings.APP_VERSION)
        - git_sha:     commit baked into the image at build time ("unknown" if unset)
        - built_at:    image build timestamp ("unknown" if unset)
        - environment: running environment name (dev/qa/prod)
    """
    return Response(
        {
            "version": getattr(settings, "APP_VERSION", "unknown"),
            "git_sha": os.getenv("GIT_SHA", "unknown"),
            "built_at": os.getenv("BUILD_TIME", "unknown"),
            "environment": getattr(settings, "ENVIRONMENT", "unknown"),
        }
    )
