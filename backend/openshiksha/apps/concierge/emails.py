"""Email notifications for concierge enquiries."""

import logging
from html import escape as _escape

from django.conf import settings
from django.core.mail import mail_admins

from openshiksha.apps.core import email_layout as layout

logger = logging.getLogger(__name__)


def _detail_row(label: str, value: str) -> str:
    return (
        f'<tr><td valign="top" style="padding:6px 16px 6px 0;font-family:{layout.FONT_SANS};'
        f'font-size:13px;font-weight:600;color:{layout.INK_400};white-space:nowrap;">{label}</td>'
        f'<td valign="top" style="padding:6px 0;font-family:{layout.FONT_SANS};font-size:15px;'
        f'color:{layout.INK_700};">{value}</td></tr>'
    )


def notify_enquiry_received(enquirer) -> None:
    """Notify the OpenShiksha team that a new enquiry has been submitted."""
    try:
        # Enquirer-supplied values are untrusted — escape before HTML interpolation.
        name = _escape(enquirer.name or "")
        school = _escape(enquirer.school or "")
        email = _escape(enquirer.email or "")
        phone = _escape(enquirer.phone or "") or "—"
        message = _escape((enquirer.message or "").strip()).replace("\n", "<br>")

        details = (
            '<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
            'style="margin:2px 0 4px;">'
            + _detail_row("Name", name)
            + _detail_row("School", school)
            + _detail_row("Email", f'<a href="mailto:{email}" style="color:{layout.BRAND_600};">{email}</a>')
            + _detail_row("Phone", phone)
            + "</table>"
        )
        body_html = (
            layout.paragraph("A new enquiry just came in through the OpenShiksha site.", color=layout.INK_500) + details
        )
        if message:
            body_html += layout.info_panel("Message", message)

        app_url = getattr(settings, "EMAIL_APP_URL", "https://openshiksha.org")
        html_message = layout.render_branded_email(
            lang="en",
            preheader=f"New enquiry from {school}",
            badge_emoji="📨",
            accent=layout.BRAND_600,
            eyebrow="New enquiry",
            heading=f"New enquiry from {school}",
            body_html=body_html,
            cta_label="View in admin",
            cta_url=f"{app_url}/django-admin/concierge/enquirer/{enquirer.pk}/change/",
        )

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
            html_message=html_message,
        )
        logger.info("notify_enquiry_received: enquiry %s from %s", enquirer.pk, enquirer.school)
    except Exception:
        logger.exception("notify_enquiry_received: failed for enquiry %s", enquirer.pk)
