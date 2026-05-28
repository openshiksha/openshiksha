"""
Announcement endpoints.

    GET  /api/v1/announcements/                   — list announcements visible to the user
    GET  /api/v1/announcements/?subject_room=<id> — filter to one subject room
    POST /api/v1/announcements/                   — create (teachers, own rooms only)
    PATCH/DELETE /api/v1/announcements/<id>/      — update/remove (author only)
"""

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied

from openshiksha.apps.core.models import UserRole

from .models import Announcement
from .serializers import AnnouncementSerializer


class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    filterset_fields = ["subject_room"]

    def get_queryset(self):
        user = self.request.user
        qs = Announcement.objects.filter(is_active=True).select_related("subject_room", "author")
        role = getattr(user, "role", None)

        if role == UserRole.TEACHER:
            qs = qs.filter(subject_room__teacher=user)
        elif role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            qs = qs.filter(subject_room__students=user)
        elif role == UserRole.PARENT:
            qs = qs.filter(subject_room__students__in=user.children.all())
        else:
            qs = qs.none()

        return qs.distinct()

    def perform_create(self, serializer):
        if getattr(self.request.user, "role", None) != UserRole.TEACHER:
            raise PermissionDenied("Only teachers can post announcements.")
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.author_id != self.request.user.id:
            raise PermissionDenied("You can only edit your own announcements.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author_id != self.request.user.id:
            raise PermissionDenied("You can only delete your own announcements.")
        instance.delete()
