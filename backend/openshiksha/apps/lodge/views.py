"""
Video content endpoints.

    GET  /api/v1/videos/?chapter=<id>   — list active videos for a chapter (any authenticated user)
    POST /api/v1/videos/                — create (teachers only)
    PATCH/DELETE /api/v1/videos/<id>/   — update/remove (teachers only)
"""

from rest_framework import viewsets

from openshiksha.apps.api.views.core import IsTeacherOrReadOnly

from .models import Video
from .serializers import VideoSerializer


class VideoViewSet(viewsets.ModelViewSet):
    serializer_class = VideoSerializer
    permission_classes = [IsTeacherOrReadOnly]
    filterset_fields = ["chapter"]

    def get_queryset(self):
        qs = Video.objects.select_related("chapter")
        # Non-teachers only ever see active videos.
        if getattr(self.request.user, "role", None) != "teacher":
            qs = qs.filter(is_active=True)
        chapter = self.request.query_params.get("chapter")
        if chapter:
            qs = qs.filter(chapter_id=chapter)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
