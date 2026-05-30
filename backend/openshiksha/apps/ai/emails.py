"""
Email helpers for the Parent Intelligence Dashboard.

Sends a parent a plain-text digest of their child's weekly progress summary.
Follows the fail-soft convention used in core.emails: an SMTP error is logged,
never raised, so one bad address can't break the weekly Celery batch.
"""

import logging

from django.core.mail import send_mail

logger = logging.getLogger(__name__)

# Highest-priority severity is surfaced first in the email lead line.
_SEVERITY_RANK = {"urgent": 0, "attention": 1, "info": 2}


def _lead_alert(alerts: list[dict]) -> dict | None:
    """Return the most severe alert (urgent > attention > info), or None."""
    if not alerts:
        return None
    return sorted(alerts, key=lambda a: _SEVERITY_RANK.get(str(a.get("severity")), 9))[0]


def notify_parent_weekly_summary(parent, child, summary) -> bool:
    """
    Email ``parent`` their child's weekly progress narrative.

    ``summary`` is a persisted ParentProgressSummary instance. Returns True if an
    email was dispatched, False if it was skipped (no address) or failed.
    """
    if not parent.email:
        logger.info("notify_parent_weekly_summary: skipped, parent %d has no email", parent.pk)
        return False

    child_name = child.first_name or child.username
    parent_name = parent.first_name or parent.username
    week_range = f"{summary.week_start.strftime('%b %d')} – {summary.week_end.strftime('%b %d')}"

    lines = [
        f"Hi {parent_name},",
        "",
        f"Here is {child_name}'s learning summary for the week of {week_range}.",
        "",
        (summary.summary_text or "").strip(),
        "",
    ]

    lead = _lead_alert(summary.alerts or [])
    if lead:
        label = (lead.get("label") or "").strip()
        detail = (lead.get("detail") or "").strip()
        lines += [f"Needs attention — {label}: {detail}".strip(": ").strip(), ""]

    activities = summary.home_activities or []
    if activities:
        act = activities[0]
        title = (act.get("title") or "This week").strip()
        desc = (act.get("description") or "").strip()
        lines += [f"Try this at home — {title}: {desc}".strip(": ").strip(), ""]

    lines += [
        f"Log in to OpenShiksha and open Insights for {child_name} to see the full dashboard.",
        "",
        "— OpenShiksha",
        "",
        "(You can turn off these weekly emails in your profile settings.)",
    ]

    try:
        send_mail(
            subject=f"{child_name}'s weekly learning summary ({week_range})",
            message="\n".join(lines),
            from_email=None,
            recipient_list=[parent.email],
            fail_silently=False,
        )
        logger.info("notify_parent_weekly_summary: sent to %s (child=%d)", parent.email, child.pk)
        return True
    except Exception:
        logger.exception("notify_parent_weekly_summary: failed for %s", parent.email)
        return False
