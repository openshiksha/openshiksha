"""
Celery tasks for AI analytics.

Each task is idempotent — safe to retry and to call multiple times.
Tasks use upsert (update_or_create) so they can be triggered after every
grading run without risk of duplicate rows.

Task hierarchy:
  analyze_student_subject_room(student_id, subject_room_id)
    → detect_learning_gaps_for_student(student_id, subject_room_id)
    → predict_performance_for_student(student_id, subject_room_id)
    → refresh_recommendations_for_student(student_id, subject_room_id)
    → update_student_mastery(student_id, subject_room_id)         [adaptive]
    → update_spaced_repetition_for_student(student_id, subject_room_id, score)  [adaptive]
    → rebuild_learning_path(student_id, subject_room_id)          [adaptive]

  analyze_class_insights(subject_room_id)
    → generate_class_insights_for_subject_room(subject_room_id)

Downstream trigger (intended usage):
  After grading completes for a Submission, enqueue:
    analyze_student_subject_room.delay(submission.student_id, submission.assignment.subject_room_id)
    analyze_class_insights.delay(submission.assignment.subject_room_id)
  After a student completes a LearningPathStep:
    update_spaced_repetition_for_student.delay(student_id, subject_room_id, node_id, score)
    rebuild_learning_path.delay(student_id, subject_room_id)
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def detect_learning_gaps_for_student(self, student_id: int, subject_room_id: int) -> dict:
    """
    Detect and persist learning gaps for a single student in a SubjectRoom.

    Returns a summary dict: {"upserted": int, "resolved": int}
    """
    try:
        from openshiksha.apps.ai.analytics import detect_gaps_for_student
        from openshiksha.apps.ai.models import LearningGap
        from openshiksha.apps.core.models import SubjectRoom, User

        student = User.objects.get(pk=student_id)
        subject_room = SubjectRoom.objects.get(pk=subject_room_id)

        gap_data = detect_gaps_for_student(student, subject_room)

        upserted = 0
        resolved = 0

        for data in gap_data:
            if data["is_resolved"]:
                # Only update if there's an existing gap row to resolve
                updated = LearningGap.objects.filter(
                    student=student,
                    chapter_id=data["chapter_id"],
                    subject_room=subject_room,
                    is_resolved=False,
                ).update(
                    avg_score=data["avg_score"],
                    tick_count=data["tick_count"],
                    is_resolved=True,
                )
                resolved += updated
            else:
                LearningGap.objects.update_or_create(
                    student=student,
                    chapter_id=data["chapter_id"],
                    subject_room=subject_room,
                    defaults={
                        "avg_score": data["avg_score"],
                        "severity": data["severity"],
                        "tick_count": data["tick_count"],
                        "is_resolved": False,
                    },
                )
                upserted += 1

        logger.info(
            "detect_learning_gaps: student=%d room=%d upserted=%d resolved=%d",
            student_id,
            subject_room_id,
            upserted,
            resolved,
        )
        return {"upserted": upserted, "resolved": resolved}

    except Exception as exc:
        logger.exception("detect_learning_gaps failed: student=%d room=%d", student_id, subject_room_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_performance_prediction_for_student(self, student_id: int, subject_room_id: int) -> dict:
    """
    Compute and persist a performance prediction for a student in a SubjectRoom.

    Returns {"updated": bool} — False when not enough data yet.
    """
    try:
        from openshiksha.apps.ai.analytics import predict_performance_for_student
        from openshiksha.apps.ai.models import PerformancePrediction
        from openshiksha.apps.core.models import SubjectRoom, User

        student = User.objects.get(pk=student_id)
        subject_room = SubjectRoom.objects.get(pk=subject_room_id)

        result = predict_performance_for_student(student, subject_room)

        if result is None:
            logger.info(
                "predict_performance: not enough data for student=%d room=%d",
                student_id,
                subject_room_id,
            )
            return {"updated": False}

        PerformancePrediction.objects.update_or_create(
            student=student,
            subject_room=subject_room,
            defaults={
                "predicted_score": result["predicted_score"],
                "confidence": result["confidence"],
                "readiness_level": result["readiness_level"],
                "tick_count": result["tick_count"],
                "factors": result["factors"],
            },
        )

        logger.info(
            "predict_performance: student=%d room=%d score=%.2f readiness=%s",
            student_id,
            subject_room_id,
            result["predicted_score"],
            result["readiness_level"],
        )
        return {"updated": True}

    except Exception as exc:
        logger.exception("predict_performance failed: student=%d room=%d", student_id, subject_room_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_class_insights_for_subject_room(self, subject_room_id: int) -> dict:
    """
    Generate and persist class-level insights for all chapters in a SubjectRoom.

    Returns {"upserted": int}
    """
    try:
        from openshiksha.apps.ai.analytics import generate_insights_for_subject_room
        from openshiksha.apps.ai.models import ClassInsight
        from openshiksha.apps.core.models import SubjectRoom

        subject_room = SubjectRoom.objects.get(pk=subject_room_id)

        insight_data = generate_insights_for_subject_room(subject_room)

        upserted = 0
        for data in insight_data:
            ClassInsight.objects.update_or_create(
                subject_room=subject_room,
                chapter_id=data["chapter_id"],
                defaults={
                    "insight_type": data["insight_type"],
                    "class_avg_score": data["class_avg_score"],
                    "students_assessed": data["students_assessed"],
                    "students_struggling": data["students_struggling"],
                    "pct_struggling": data["pct_struggling"],
                },
            )
            upserted += 1

        logger.info("generate_class_insights: room=%d upserted=%d", subject_room_id, upserted)
        return {"upserted": upserted}

    except Exception as exc:
        logger.exception("generate_class_insights failed: room=%d", subject_room_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_recommendations_for_student(self, student_id: int, subject_room_id: int) -> dict:
    """
    Generate and persist ContentRecommendations for a student in a SubjectRoom.

    Algorithm (see analytics.generate_recommendations_for_student):
    1. Active severe gaps → URGENT
    2. Recently resolved gaps → HIGH (spaced review)
    3. Active moderate gaps → HIGH
    4. Active mild gaps → MEDIUM
    5. Next unvisited chapters in curriculum → LOW

    Existing active recommendations are deactivated before writing new ones
    (clean-slate per run) so stale entries don't accumulate.

    Returns {"created": int, "deactivated": int}
    """
    try:

        from openshiksha.apps.ai.analytics import generate_recommendations_for_student
        from openshiksha.apps.ai.models import ContentRecommendation
        from openshiksha.apps.core.models import SubjectRoom, User

        student = User.objects.get(pk=student_id)
        subject_room = SubjectRoom.objects.get(pk=subject_room_id)

        rec_data = generate_recommendations_for_student(student, subject_room)

        # Deactivate previous active recommendations for this student × room
        deactivated = ContentRecommendation.objects.filter(
            student=student,
            subject_room=subject_room,
            is_active=True,
        ).update(is_active=False)

        created = 0
        for data in rec_data:
            ContentRecommendation.objects.update_or_create(
                student=student,
                chapter_id=data["chapter_id"],
                subject_room=subject_room,
                defaults={
                    "reason": data["reason"],
                    "priority": data["priority"],
                    "score_snapshot": data["score_snapshot"],
                    "problem_set_id": data["problem_set_id"],
                    "is_active": True,
                    "is_actioned": False,
                },
            )
            created += 1

        logger.info(
            "refresh_recommendations: student=%d room=%d created=%d deactivated=%d",
            student_id,
            subject_room_id,
            created,
            deactivated,
        )
        return {"created": created, "deactivated": deactivated}

    except Exception as exc:
        logger.exception("refresh_recommendations failed: student=%d room=%d", student_id, subject_room_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_daily_practice_plan(self, student_id: int, subject_room_id: int) -> dict:
    """
    Build (or refresh) today's PracticePlan for a student.

    Pulls the current active ContentRecommendations sorted by priority,
    takes the top MAX_PLAN_RECOMMENDATIONS, and stores them as a PracticePlan
    for today's date.

    Idempotent: calling multiple times on the same day updates the plan in-place.

    Returns {"plan_id": int, "recommendation_count": int, "estimated_minutes": int}
    """
    try:

        from django.utils import timezone

        from openshiksha.apps.ai.analytics import DEFAULT_MINUTES_PER_REC, MAX_PLAN_RECOMMENDATIONS
        from openshiksha.apps.ai.models import ContentRecommendation, PracticePlan
        from openshiksha.apps.core.models import ProblemSet, SubjectRoom, User

        student = User.objects.get(pk=student_id)
        subject_room = SubjectRoom.objects.get(pk=subject_room_id)
        today = timezone.localdate()

        active_recs = list(
            ContentRecommendation.objects.filter(student=student, subject_room=subject_room, is_active=True).order_by(
                "priority", "score_snapshot"
            )[:MAX_PLAN_RECOMMENDATIONS]
        )

        # Compute estimated minutes
        total_minutes = 0
        for rec in active_recs:
            if rec.problem_set_id:
                try:
                    ps = ProblemSet.objects.only("estimated_minutes").get(pk=rec.problem_set_id)
                    total_minutes += ps.estimated_minutes or DEFAULT_MINUTES_PER_REC
                except ProblemSet.DoesNotExist:
                    total_minutes += DEFAULT_MINUTES_PER_REC
            else:
                total_minutes += DEFAULT_MINUTES_PER_REC

        plan, _ = PracticePlan.objects.update_or_create(
            student=student,
            subject_room=subject_room,
            plan_date=today,
            defaults={
                "estimated_minutes": total_minutes,
                "is_completed": False,
            },
        )
        plan.recommendations.set(active_recs)

        logger.info(
            "generate_daily_practice_plan: student=%d room=%d plan=%d recs=%d mins=%d",
            student_id,
            subject_room_id,
            plan.pk,
            len(active_recs),
            total_minutes,
        )
        return {
            "plan_id": plan.pk,
            "recommendation_count": len(active_recs),
            "estimated_minutes": total_minutes,
        }

    except Exception as exc:
        logger.exception("generate_daily_practice_plan failed: student=%d room=%d", student_id, subject_room_id)
        raise self.retry(exc=exc)


@shared_task
def analyze_student_subject_room(student_id: int, subject_room_id: int) -> None:
    """
    Convenience task: runs gap detection, performance prediction,
    recommendation refresh, and mastery/path updates for a student.
    Called after grading completes for a submission.
    """
    detect_learning_gaps_for_student.delay(student_id, subject_room_id)
    update_performance_prediction_for_student.delay(student_id, subject_room_id)
    refresh_recommendations_for_student.delay(student_id, subject_room_id)
    update_student_mastery.delay(student_id, subject_room_id)
    rebuild_learning_path.delay(student_id, subject_room_id)


# ─────────────────────────────────────────────────────────────────────────────
# Adaptive Learning Engine Tasks
# ─────────────────────────────────────────────────────────────────────────────


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_student_mastery(self, student_id: int, subject_room_id: int) -> dict:
    """
    Recompute and persist StudentMastery records for a student in a SubjectRoom.

    Uses EWMA over all graded submissions (see adaptive_analytics.compute_mastery_for_student).
    Safe to call multiple times — uses update_or_create.

    Returns {"upserted": int}
    """
    try:
        from django.utils import timezone

        from openshiksha.apps.ai.adaptive_analytics import compute_mastery_for_student
        from openshiksha.apps.ai.models import StudentMastery
        from openshiksha.apps.core.models import SubjectRoom, User

        student = User.objects.get(pk=student_id)
        subject_room = SubjectRoom.objects.get(pk=subject_room_id)

        mastery_data = compute_mastery_for_student(student, subject_room)

        upserted = 0
        now = timezone.now()
        for data in mastery_data:
            obj, created = StudentMastery.objects.update_or_create(
                student=student,
                knowledge_node_id=data["knowledge_node_id"],
                defaults={
                    "mastery_score": data["new_mastery_score"],
                    "mastery_level": data["mastery_level"],
                    "attempt_count": data["attempt_count"],
                    "last_attempted_at": data["last_attempted_at"],
                },
            )
            if created:
                obj.first_attempted_at = now
                obj.save(update_fields=["first_attempted_at"])
            upserted += 1

        logger.info(
            "update_student_mastery: student=%d room=%d upserted=%d",
            student_id,
            subject_room_id,
            upserted,
        )
        return {"upserted": upserted}

    except Exception as exc:
        logger.exception("update_student_mastery failed: student=%d room=%d", student_id, subject_room_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_spaced_repetition_for_student(
    self,
    student_id: int,
    knowledge_node_id: int,
    score: float,
) -> dict:
    """
    Update (or create) the SpacedRepetitionEntry for a student × KnowledgeNode
    after a practice session using the SM-2 algorithm.

    Call this after a student completes a LearningPathStep or any graded session
    for this chapter.

    Returns {"knowledge_node_id": int, "next_review_date": str, "interval_days": int}
    """
    try:
        from django.utils import timezone

        from openshiksha.apps.ai.adaptive_analytics import SRS_INITIAL_EF, compute_srs_update
        from openshiksha.apps.ai.models import SpacedRepetitionEntry
        from openshiksha.apps.core.models import User

        student = User.objects.get(pk=student_id)
        now = timezone.now()

        try:
            entry = SpacedRepetitionEntry.objects.get(student=student, knowledge_node_id=knowledge_node_id)
            current_interval = entry.interval_days
            current_ef = entry.easiness_factor
            current_reps = entry.repetitions
        except SpacedRepetitionEntry.DoesNotExist:
            current_interval = 1
            current_ef = SRS_INITIAL_EF
            current_reps = 0

        updated = compute_srs_update(score, current_interval, current_ef, current_reps)
        next_review = timezone.localdate() + __import__("datetime").timedelta(days=updated["interval_days"])

        SpacedRepetitionEntry.objects.update_or_create(
            student=student,
            knowledge_node_id=knowledge_node_id,
            defaults={
                "interval_days": updated["interval_days"],
                "easiness_factor": updated["easiness_factor"],
                "repetitions": updated["repetitions"],
                "next_review_date": next_review,
                "last_reviewed_at": now,
            },
        )

        logger.info(
            "update_srs: student=%d node=%d score=%.2f interval=%dd next=%s",
            student_id,
            knowledge_node_id,
            score,
            updated["interval_days"],
            next_review,
        )
        return {
            "knowledge_node_id": knowledge_node_id,
            "next_review_date": next_review.isoformat(),
            "interval_days": updated["interval_days"],
        }

    except Exception as exc:
        logger.exception("update_srs failed: student=%d node=%d", student_id, knowledge_node_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def rebuild_learning_path(self, student_id: int, subject_room_id: int) -> dict:
    """
    Regenerate the student's LearningPath for a SubjectRoom.

    Marks any existing ACTIVE path as STALE, then creates a fresh LearningPath
    with LearningPathSteps ordered by the adaptive engine.

    Idempotent — safe to call after every grading event.

    Returns {"path_id": int, "total_steps": int}
    """
    try:
        from openshiksha.apps.ai.adaptive_analytics import generate_learning_path_steps
        from openshiksha.apps.ai.models import LearningPath, LearningPathStatus, LearningPathStep
        from openshiksha.apps.core.models import SubjectRoom, User

        student = User.objects.get(pk=student_id)
        subject_room = SubjectRoom.objects.get(pk=subject_room_id)

        step_data = generate_learning_path_steps(student, subject_room)

        # Mark existing active paths as stale
        LearningPath.objects.filter(
            student=student,
            subject_room=subject_room,
            status=LearningPathStatus.ACTIVE,
        ).update(status=LearningPathStatus.STALE)

        # Create new path
        path = LearningPath.objects.create(
            student=student,
            subject_room=subject_room,
            status=LearningPathStatus.ACTIVE,
            total_steps=len(step_data),
            completed_steps=0,
        )

        # Bulk-create steps
        steps = [
            LearningPathStep(
                learning_path=path,
                knowledge_node_id=s["knowledge_node_id"],
                problem_set_id=s["problem_set_id"],
                position=s["position"],
                is_review=s["is_review"],
            )
            for s in step_data
        ]
        LearningPathStep.objects.bulk_create(steps)

        logger.info(
            "rebuild_learning_path: student=%d room=%d path=%d steps=%d",
            student_id,
            subject_room_id,
            path.pk,
            len(steps),
        )
        return {"path_id": path.pk, "total_steps": len(steps)}

    except Exception as exc:
        logger.exception("rebuild_learning_path failed: student=%d room=%d", student_id, subject_room_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def complete_learning_path_step(
    self,
    step_id: int,
    score: float,
) -> dict:
    """
    Mark a LearningPathStep as COMPLETED and trigger downstream updates.

    After completion:
    - Step status → COMPLETED, score_when_completed saved
    - LearningPath.completed_steps incremented
    - SpacedRepetitionEntry updated for the chapter
    - StudentMastery refreshed
    - LearningPath rebuilt if all steps are done

    Returns {"step_id": int, "path_completed": bool}
    """
    try:
        from django.utils import timezone

        from openshiksha.apps.ai.models import LearningPath, LearningPathStep, StepStatus

        step = LearningPathStep.objects.select_related("learning_path").get(pk=step_id)
        path = step.learning_path

        step.status = StepStatus.COMPLETED
        step.score_when_completed = score
        step.completed_at = timezone.now()
        step.save(update_fields=["status", "score_when_completed", "completed_at"])

        LearningPath.objects.filter(pk=path.pk).update(
            completed_steps=LearningPath.objects.filter(pk=path.pk).values_list("completed_steps", flat=True).first()
            + 1
        )

        # Refresh SRS for the chapter
        update_spaced_repetition_for_student.delay(
            path.student_id,
            step.knowledge_node_id,
            score,
        )

        # Refresh mastery
        update_student_mastery.delay(path.student_id, path.subject_room_id)

        # Check if path is fully complete
        path.refresh_from_db()
        path_completed = path.completed_steps >= path.total_steps

        if path_completed:
            from openshiksha.apps.ai.models import LearningPathStatus

            path.status = LearningPathStatus.COMPLETED
            path.save(update_fields=["status"])
        else:
            rebuild_learning_path.delay(path.student_id, path.subject_room_id)

        logger.info(
            "complete_step: step=%d score=%.2f path_completed=%s",
            step_id,
            score,
            path_completed,
        )
        return {"step_id": step_id, "path_completed": path_completed}

    except Exception as exc:
        logger.exception("complete_step failed: step=%d", step_id)
        raise self.retry(exc=exc)
