"""Email notifications for concierge enquiries."""

import logging

from django.core.mail import mail_admins

logger = logging.getLogger(__name__)


def notify_enquiry_received(enquirer) -> None:
    """Notify the OpenShiksha team that a new enquiry has been submitted."""
    try:
        mail_admins(
            subject=f"New OpenShiksha enquiry from {enquirer.school}",
            message=(
                f"Name: {enquirer.name}\n"
                f"School: {enquirer.school}\n"
                f"Email: {enquirer.email}\n"
                f"Phone: {enquirer.phone or '—'}\n\n"
                f"Message:\n{enquirer.message or '(none)'}\n\n"
                f"Enquiry ID: {enquirer.pk}"
            ),
            fail_silently=True,
        )
        logger.info("notify_enquiry_received: enquiry %s from %s", enquirer.pk, enquirer.school)
    except Exception:
        logger.exception("notify_enquiry_received: failed for enquiry %s", enquirer.pk)
