"""
Announcements — teacher broadcasts to a subject room.

Ports the legacy ``core.Announcement`` feature, which used a polymorphic
GenericForeignKey to target a school/classroom/subjectroom/user. This modern
version scopes an announcement to a single SubjectRoom — the primary teaching
unit — which covers the common case (a teacher messaging their class) while
keeping the data model simple and queryable. Students enrolled in the room and
their parents can read it.
"""

from django.db import models

from openshiksha.apps.core.models import SubjectRoom, User, UserRole


class Announcement(models.Model):
    """A message broadcast by a teacher to a subject room."""

    subject_room = models.ForeignKey(
        SubjectRoom,
        on_delete=models.CASCADE,
        related_name="announcements",
        help_text="The subject room this announcement targets",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="announcements",
        limit_choices_to={"role": UserRole.TEACHER},
        help_text="The teacher who posted this announcement",
    )
    message = models.TextField(help_text="The announcement text")
    is_active = models.BooleanField(default=True, help_text="Hide without deleting when False")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["subject_room", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"Announcement by {self.author_id} for room {self.subject_room_id}"
