"""
Lodge — instructional video content.

Improves on the legacy ``lodge.Video`` model (which stored only a bare embed
URL) by linking each video to a Chapter, giving it a title/description, and an
explicit ordering so students see a curated playlist per chapter.
"""

from django.db import models

from openshiksha.apps.core.models import Chapter, User


class Video(models.Model):
    """An instructional video linked to a chapter."""

    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name="videos",
        help_text="The chapter this video supports",
    )
    title = models.CharField(max_length=255, help_text="Video title")
    embed_url = models.URLField(help_text="Embeddable video URL (e.g. YouTube embed link)")
    description = models.TextField(blank=True, default="", help_text="Optional description of the video")
    order = models.PositiveIntegerField(default=0, help_text="Display order within the chapter (ascending)")
    is_active = models.BooleanField(default=True, help_text="Hide without deleting when False")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lodge_videos",
        help_text="Teacher/admin who added this video",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.title
