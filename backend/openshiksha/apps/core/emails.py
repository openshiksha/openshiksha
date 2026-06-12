"""
Email notification helpers for OpenShiksha.

All functions are silent on failure (fail_silently=True) so email errors
never surface as grading or task errors.

Localization (LA-7): every email renders in the recipient's
``User.preferred_language`` (en/hi, default en) via a tiny per-module string
catalog — mirroring the frontend's deliberately dependency-free i18n module
(docs/initiatives/2026-language-access.md, principle 2). No gettext/.po
machinery for two languages of plain-text email.
"""

import logging

from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def format_email_string(catalog: dict, user, key: str, **kwargs) -> str:
    """
    Render ``catalog[lang][key]`` for the user's preferred language with
    ``str.format`` interpolation. Falls back to English when the language or
    the key is missing — an untranslated email beats a broken one
    (initiative principle 3).
    """
    lang = getattr(user, "preferred_language", "en") or "en"
    template = catalog.get(lang, {}).get(key) or catalog["en"][key]
    return template.format(**kwargs)


_STRINGS = {
    "en": {
        "remedial.subject": "You have a new practice assignment",
        "remedial.body": (
            "Hi {name},\n\n"
            "Your teacher has created a practice assignment to help you strengthen "
            "'{chapter_name}' before {due_date}.\n\n"
            "Log in to OpenShiksha to start practising.\n\n"
            "— OpenShiksha"
        ),
        "reminder.subject": "Reminder: '{assignment_title}' is due {due_date}",
        "reminder.body": (
            "Hi {name},\n\n"
            "This is a friendly reminder that your assignment '{assignment_title}' "
            "is due {due_date}.\n\n"
            "Log in to OpenShiksha to complete it before the deadline.\n\n"
            "— OpenShiksha\n\n"
            "(You can turn off these reminders in your profile settings.)"
        ),
        "graded.subject": "Your assignment has been graded: {score_pct}%",
        "graded.body": (
            "Hi {name},\n\n"
            "Your submission for '{assignment_title}' has been graded.\n\n"
            "Score: {score_pct}%\n\n"
            "Log in to OpenShiksha to review your results.\n\n"
            "— OpenShiksha"
        ),
    },
    "hi": {
        "remedial.subject": "आपके लिए एक नया अभ्यास असाइनमेंट है",
        "remedial.body": (
            "नमस्ते {name},\n\n"
            "आपके शिक्षक ने '{chapter_name}' को मज़बूत करने के लिए एक अभ्यास "
            "असाइनमेंट बनाया है — अंतिम तिथि {due_date}।\n\n"
            "अभ्यास शुरू करने के लिए OpenShiksha पर लॉग इन करें।\n\n"
            "— OpenShiksha"
        ),
        "reminder.subject": "याद दिलाना: '{assignment_title}' की अंतिम तिथि {due_date} है",
        "reminder.body": (
            "नमस्ते {name},\n\n"
            "यह एक दोस्ताना याद दिलाना है कि आपके असाइनमेंट '{assignment_title}' "
            "की अंतिम तिथि {due_date} है।\n\n"
            "समय रहते पूरा करने के लिए OpenShiksha पर लॉग इन करें।\n\n"
            "— OpenShiksha\n\n"
            "(आप प्रोफ़ाइल सेटिंग्स में ये रिमाइंडर बंद कर सकते हैं।)"
        ),
        "graded.subject": "आपका असाइनमेंट जाँच लिया गया है: {score_pct}%",
        "graded.body": (
            "नमस्ते {name},\n\n"
            "'{assignment_title}' के लिए आपका जमा किया गया काम जाँच लिया गया है।\n\n"
            "स्कोर: {score_pct}%\n\n"
            "अपने परिणाम देखने के लिए OpenShiksha पर लॉग इन करें।\n\n"
            "— OpenShiksha"
        ),
    },
}


def _s(user, key: str, **kwargs) -> str:
    return format_email_string(_STRINGS, user, key, **kwargs)


def notify_remedial_assigned(student, chapter_name: str, due_date_str: str) -> None:
    """Email a student when a remedial practice assignment is created for them."""
    if not student.email:
        return
    name = student.first_name or student.username
    try:
        send_mail(
            subject=_s(student, "remedial.subject"),
            message=_s(student, "remedial.body", name=name, chapter_name=chapter_name, due_date=due_date_str),
            from_email=None,
            recipient_list=[student.email],
            fail_silently=False,
        )
        logger.info("notify_remedial_assigned: sent to %s", student.email)
    except Exception:
        logger.exception("notify_remedial_assigned: failed for %s", student.email)


def notify_due_date_reminder(student, assignment_title: str, due_date_str: str) -> None:
    """Email a student reminding them an assignment is due soon."""
    if not student.email:
        return
    name = student.first_name or student.username
    try:
        send_mail(
            subject=_s(student, "reminder.subject", assignment_title=assignment_title, due_date=due_date_str),
            message=_s(student, "reminder.body", name=name, assignment_title=assignment_title, due_date=due_date_str),
            from_email=None,
            recipient_list=[student.email],
            fail_silently=False,
        )
        logger.info("notify_due_date_reminder: sent to %s", student.email)
    except Exception:
        logger.exception("notify_due_date_reminder: failed for %s", student.email)


def notify_grading_complete(student, assignment_title: str, score_pct: int) -> None:
    """Email a student when their submission has been graded."""
    if not student.email:
        return
    name = student.first_name or student.username
    try:
        send_mail(
            subject=_s(student, "graded.subject", score_pct=score_pct),
            message=_s(student, "graded.body", name=name, assignment_title=assignment_title, score_pct=score_pct),
            from_email=None,
            recipient_list=[student.email],
            fail_silently=False,
        )
        logger.info("notify_grading_complete: sent to %s", student.email)
    except Exception:
        logger.exception("notify_grading_complete: failed for %s", student.email)
