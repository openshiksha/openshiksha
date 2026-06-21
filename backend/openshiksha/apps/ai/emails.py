"""
Email helpers for the Parent Intelligence Dashboard.

Sends a parent a plain-text digest of their child's weekly progress summary.
Follows the fail-soft convention used in core.emails: an SMTP error is logged,
never raised, so one bad address can't break the weekly Celery batch.

Localization (LA-7): the static chrome renders in the parent's
``preferred_language`` (the AI ``summary_text`` is already generated in that
language by ``generate_parent_progress_summary``).
"""

import logging

from django.core.mail import send_mail

from openshiksha.apps.core import email_layout as layout
from openshiksha.apps.core.emails import format_email_string

logger = logging.getLogger(__name__)

# Highest-priority severity is surfaced first in the email lead line.
_SEVERITY_RANK = {"urgent": 0, "attention": 1, "info": 2}

_STRINGS = {
    "en": {
        "subject": "{child_name}'s weekly learning summary ({week_range})",
        "html_heading": "{child_name}'s learning summary",
        "open_insights": "Open Insights",
        "attention_title": "Needs attention",
        "activity_title": "Try this at home",
        "greeting": "Hi {parent_name},",
        "intro": "Here is {child_name}'s learning summary for the week of {week_range}.",
        "needs_attention": "Needs attention — {label}: {detail}",
        "home_activity": "Try this at home — {title}: {desc}",
        "activity_default_title": "This week",
        "cta": "Log in to OpenShiksha and open Insights for {child_name} to see the full dashboard.",
        "signature": "— OpenShiksha",
        "footer": "(You can turn off these weekly emails in your profile settings.)",
    },
    "hi": {
        "subject": "{child_name} की साप्ताहिक लर्निंग समरी ({week_range})",
        "html_heading": "{child_name} की लर्निंग समरी",
        "open_insights": "इनसाइट्स खोलें",
        "attention_title": "ध्यान दें",
        "activity_title": "घर पर आज़माएँ",
        "greeting": "नमस्ते {parent_name},",
        "intro": "{week_range} के सप्ताह की {child_name} की सीखने की समरी यह रही।",
        "needs_attention": "ध्यान दें — {label}: {detail}",
        "home_activity": "घर पर आज़माएँ — {title}: {desc}",
        "activity_default_title": "इस सप्ताह",
        "cta": "पूरा डैशबोर्ड देखने के लिए OpenShiksha पर लॉग इन करके {child_name} के लिए इनसाइट्स खोलें।",
        "signature": "— OpenShiksha",
        "footer": "(आप प्रोफ़ाइल सेटिंग्स में ये साप्ताहिक ईमेल बंद कर सकते हैं।)",
    },
}


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

    def _s(key: str, **kwargs) -> str:
        return format_email_string(_STRINGS, parent, key, **kwargs)

    child_name = child.first_name or child.username
    parent_name = parent.first_name or parent.username
    week_range = f"{summary.week_start.strftime('%b %d')} – {summary.week_end.strftime('%b %d')}"

    lines = [
        _s("greeting", parent_name=parent_name),
        "",
        _s("intro", child_name=child_name, week_range=week_range),
        "",
        (summary.summary_text or "").strip(),
        "",
    ]

    lead = _lead_alert(summary.alerts or [])
    if lead:
        label = (lead.get("label") or "").strip()
        detail = (lead.get("detail") or "").strip()
        lines += [_s("needs_attention", label=label, detail=detail).strip(": ").strip(), ""]

    activities = summary.home_activities or []
    if activities:
        act = activities[0]
        title = (act.get("title") or _s("activity_default_title")).strip()
        desc = (act.get("description") or "").strip()
        lines += [_s("home_activity", title=title, desc=desc).strip(": ").strip(), ""]

    lines += [
        _s("cta", child_name=child_name),
        "",
        _s("signature"),
        "",
        _s("footer"),
    ]

    # Branded HTML alternative — the plain-text ``lines`` above stay the fallback.
    panels_html = ""
    if lead:
        panels_html += layout.info_panel(
            _s("attention_title"),
            f"<b>{label}</b> — {detail}" if detail else f"<b>{label}</b>",
            accent=layout.WARN_AMBER,
            bg=layout.WARN_AMBER_BG,
        )
    if activities:
        panels_html += layout.info_panel(
            _s("activity_title"),
            f"<b>{title}</b> — {desc}" if desc else f"<b>{title}</b>",
            accent=layout.BRAND_600,
            bg=layout.BRAND_50,
        )
    body_html = (
        layout.paragraph(_s("greeting", parent_name=parent_name))
        + layout.paragraph(_s("intro", child_name=child_name, week_range=week_range))
        + layout.paragraph((summary.summary_text or "").strip(), color=layout.INK_700)
        + panels_html
    )
    html_message = layout.render_branded_email(
        lang=getattr(parent, "preferred_language", "en") or "en",
        preheader=_s("intro", child_name=child_name, week_range=week_range),
        badge_emoji="📊",
        accent=layout.BRAND_600,
        eyebrow=week_range,
        heading=_s("html_heading", child_name=child_name),
        body_html=body_html,
        cta_label=_s("open_insights"),
    )

    try:
        send_mail(
            subject=_s("subject", child_name=child_name, week_range=week_range),
            message="\n".join(lines),
            from_email=None,
            recipient_list=[parent.email],
            fail_silently=False,
            html_message=html_message,
        )
        logger.info("notify_parent_weekly_summary: sent to %s (child=%d)", parent.email, child.pk)
        return True
    except Exception:
        logger.exception("notify_parent_weekly_summary: failed for %s", parent.email)
        return False
