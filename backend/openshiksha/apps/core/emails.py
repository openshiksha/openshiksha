"""
Email notification helpers for OpenShiksha.

All functions are silent on failure (fail_silently=True) so email errors
never surface as grading or task errors.
"""

import logging

from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def notify_remedial_assigned(student, chapter_name: str, due_date_str: str) -> None:
    """Email a student when a remedial practice assignment is created for them."""
    if not student.email:
        return
    name = student.first_name or student.username
    try:
        send_mail(
            subject="You have a new practice assignment",
            message=(
                f"Hi {name},\n\n"
                f"Your teacher has created a practice assignment to help you strengthen "
                f"'{chapter_name}' before {due_date_str}.\n\n"
                f"Log in to OpenShiksha to start practising.\n\n"
                f"— OpenShiksha"
            ),
            from_email=None,
            recipient_list=[student.email],
            fail_silently=False,
        )
        logger.info("notify_remedial_assigned: sent to %s", student.email)
    except Exception:
        logger.exception("notify_remedial_assigned: failed for %s", student.email)


def notify_grading_complete(student, assignment_title: str, score_pct: int) -> None:
    """Email a student when their submission has been graded."""
    if not student.email:
        return
    name = student.first_name or student.username
    try:
        send_mail(
            subject=f"Your assignment has been graded: {score_pct}%",
            message=(
                f"Hi {name},\n\n"
                f"Your submission for '{assignment_title}' has been graded.\n\n"
                f"Score: {score_pct}%\n\n"
                f"Log in to OpenShiksha to review your results.\n\n"
                f"— OpenShiksha"
            ),
            from_email=None,
            recipient_list=[student.email],
            fail_silently=False,
        )
        logger.info("notify_grading_complete: sent to %s", student.email)
    except Exception:
        logger.exception("notify_grading_complete: failed for %s", student.email)
