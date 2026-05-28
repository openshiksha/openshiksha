"""
Concierge — public enquiries from prospective schools.

Ported from the legacy ``concierge.Enquirer`` model. A prospective school
fills out the public enquiry form; the submission is persisted and the
OpenShiksha team is notified by email.
"""

from django.db import models


class Enquirer(models.Model):
    """A prospective school or individual enquiring about OpenShiksha."""

    name = models.CharField(max_length=255, help_text="Contact person's name")
    school = models.CharField(max_length=255, help_text="School or organization name")
    email = models.EmailField(help_text="Contact email address")
    phone = models.CharField(max_length=15, blank=True, default="", help_text="Contact phone number")
    message = models.TextField(blank=True, default="", help_text="Optional message from the enquirer")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Enquiry"
        verbose_name_plural = "Enquiries"

    def __str__(self) -> str:
        return f"{self.name} ({self.school})"
