"""
Django signals for the Core app.
"""

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender="core.Submission")
def trigger_grading_on_submit(sender, instance, created, update_fields, **kwargs):
    """
    Trigger async grading when a student submits (i.e. submitted_at is first set).

    Guards:
    - Only fires when submitted_at is non-null
    - Only fires when update_fields includes 'submitted_at' (explicit save) OR
      on initial create if submitted_at is already set
    - Does NOT re-grade if the submission is simply updated for other fields
    """
    if not instance.submitted_at:
        return

    # If update_fields is specified, only trigger when submitted_at was explicitly saved
    if update_fields is not None and "submitted_at" not in update_fields:
        return

    # On create with submitted_at already set, or on explicit submitted_at update
    from openshiksha.apps.core.tasks import grade_submission

    logger.info(f"Submission {instance.pk} submitted — queuing grade_submission task")
    grade_submission.delay(instance.pk)


@receiver(post_save, sender="core.Submission")
def update_student_streak(sender, instance, update_fields, **kwargs):
    """
    When a student submits (submitted_at set), record activity on their streak.
    Mirrors the guard logic of trigger_grading_on_submit so both fire together.
    """
    if not instance.submitted_at:
        return
    if update_fields is not None and "submitted_at" not in update_fields:
        return

    from openshiksha.apps.core.models import StudentStreak

    streak, _ = StudentStreak.objects.get_or_create(student_id=instance.student_id)
    streak.record_activity(instance.submitted_at.date())
