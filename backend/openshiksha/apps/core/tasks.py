"""
Celery tasks for grading submissions and updating analytics.

These tasks run asynchronously after a student submits answers.
Flow: grade_submission → _update_assignment_aggregates + update_proficiency
"""

import logging

from celery import shared_task

from django.db.models import Avg

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def grade_submission(self, submission_id: int) -> dict:
    """
    Grade a submission after a student submits answers.

    Steps:
    1. Load submission + assignment + problem_set + questions
    2. For each question subpart, compare student answer to correct_answer
    3. Bulk-create Tick records for each subpart
    4. Compute submission.score and submission.completion
    5. Save submission
    6. Queue assignment aggregate update and proficiency update

    Returns a summary dict with grading results.
    """
    from openshiksha.apps.core.models import QuestionSubpart, Submission
    from openshiksha.apps.edge.models import Tick

    try:
        submission = Submission.objects.select_related(
            "assignment__problem_set",
            "assignment__subject_room",
            "student",
        ).get(pk=submission_id)
    except Submission.DoesNotExist:
        logger.error(f"grade_submission: Submission {submission_id} not found")
        return {"error": "Submission not found"}

    answers = submission.answers  # {str(subpart_id): answer_value}
    problem_set = submission.assignment.problem_set
    subject_room = submission.assignment.subject_room

    # Load all subparts for this problem set's questions in one query
    question_ids = list(problem_set.questions.values_list("id", flat=True))
    subparts = list(
        QuestionSubpart.objects.filter(question__in=question_ids)
        .select_related("question")
        .order_by("question_id", "index")
    )

    # Group subpart counts per question for SubjectRoomQuestionMistake
    subpart_count_by_question: dict[int, int] = {}
    for sp in subparts:
        subpart_count_by_question[sp.question_id] = subpart_count_by_question.get(sp.question_id, 0) + 1

    total_subparts = len(subparts)
    attempted = 0
    total_mark = 0.0
    ticks_to_create = []

    for subpart in subparts:
        answer_key = str(subpart.id)
        if answer_key not in answers:
            continue

        attempted += 1
        student_answer = answers[answer_key]
        mark = _grade_subpart(subpart.question.question_type, student_answer, subpart.correct_answer)
        total_mark += mark

        ticks_to_create.append(
            Tick(
                student=submission.student,
                question_subpart=subpart,
                submission=submission,
                subject_room=subject_room,
                mark=mark,
            )
        )

    # Bulk-create all ticks in one DB round trip
    created_ticks = Tick.objects.bulk_create(ticks_to_create)

    # Update submission scores
    submission.score = total_mark / total_subparts if total_subparts > 0 else 0.0
    submission.completion = attempted / total_subparts if total_subparts > 0 else 0.0
    submission.save(update_fields=["score", "completion"])

    # Update question mistake aggregates
    _update_question_mistakes(created_ticks, subject_room.id, subpart_count_by_question)

    # Queue downstream tasks
    _update_assignment_aggregates.delay(submission.assignment_id)
    update_proficiency.delay(submission.student_id, subject_room.id)

    return {
        "submission_id": submission_id,
        "total_subparts": total_subparts,
        "attempted": attempted,
        "score": submission.score,
        "completion": submission.completion,
        "ticks_created": len(ticks_to_create),
    }


def _grade_subpart(question_type: str, student_answer, correct_answer: dict) -> float:
    """
    Grade a single subpart answer. Returns a fraction (0.0–1.0).
    Matching questions support partial credit.
    """
    if not correct_answer or "answer" not in correct_answer:
        return 0.0

    expected = correct_answer["answer"]

    if question_type in ("mcq", "fill_blank", "multi_select"):
        return 1.0 if str(student_answer) == str(expected) else 0.0

    if question_type == "numeric":
        try:
            return 1.0 if abs(float(student_answer) - float(expected)) < 0.001 else 0.0
        except (TypeError, ValueError):
            return 0.0

    if question_type == "matching":
        # Partial credit: each correctly matched pair = 1/n
        if not isinstance(expected, dict) or not isinstance(student_answer, dict):
            return 0.0
        if not expected:
            return 0.0
        correct_pairs = sum(1 for k, v in expected.items() if str(student_answer.get(k)) == str(v))
        return correct_pairs / len(expected)

    return 0.0


def _update_question_mistakes(ticks, subject_room_id: int, subpart_count_by_question: dict) -> None:
    """
    Update SubjectRoomQuestionMistake records from a batch of newly created ticks.
    Uses get_or_create + apply_tick for each unique question in the batch.
    """
    from openshiksha.apps.edge.models import SubjectRoomQuestionMistake

    # Group ticks by question
    ticks_by_question: dict[int, list] = {}
    for tick in ticks:
        q_id = tick.question_subpart.question_id
        ticks_by_question.setdefault(q_id, []).append(tick)

    for question_id, q_ticks in ticks_by_question.items():
        mistake, _ = SubjectRoomQuestionMistake.objects.get_or_create(
            subject_room_id=subject_room_id,
            question_id=question_id,
        )
        num_subparts = subpart_count_by_question.get(question_id, 1)
        for tick in q_ticks:
            mistake.apply_tick(tick, num_subparts)


@shared_task
def _update_assignment_aggregates(assignment_id: int) -> None:
    """Recompute Assignment.average_score and completion_rate from all submitted submissions."""
    from openshiksha.apps.core.models import Assignment, Submission

    agg = Submission.objects.filter(
        assignment_id=assignment_id,
        submitted_at__isnull=False,
    ).aggregate(
        avg_score=Avg("score"),
        avg_completion=Avg("completion"),
    )
    Assignment.objects.filter(pk=assignment_id).update(
        average_score=agg["avg_score"] or 0.0,
        completion_rate=agg["avg_completion"] or 0.0,
    )


@shared_task
def update_proficiency(student_id: int, subject_room_id: int) -> None:
    """
    Recalculate StudentProficiency for all tags from unacknowledged ticks.

    Steps:
    1. Load unacknowledged ticks for this student + subjectroom
    2. For each tick, update StudentProficiency for all tags on the subpart + question
    3. Acknowledge all ticks
    4. Recalculate percentile ranking across all students for each affected tag
    5. Update SubjectRoomProficiency aggregates
    """
    from openshiksha.apps.edge.models import StudentProficiency, Tick

    ticks = list(
        Tick.objects.filter(
            student_id=student_id,
            subject_room_id=subject_room_id,
            is_acknowledged=False,
        )
        .select_related("question_subpart__question")
        .prefetch_related("question_subpart__tags", "question_subpart__question__tags")
    )

    if not ticks:
        return

    affected_tag_ids = set()

    for tick in ticks:
        # Tags from both the subpart and its parent question (union)
        all_tags = set(tick.question_subpart.tags.all()) | set(tick.question_subpart.question.tags.all())
        for tag in all_tags:
            prof, _ = StudentProficiency.objects.get_or_create(
                student_id=student_id,
                question_tag=tag,
                subject_room_id=subject_room_id,
            )
            prof.apply_tick(tick)
            affected_tag_ids.add(tag.id)

    # Acknowledge all processed ticks
    Tick.objects.filter(
        student_id=student_id,
        subject_room_id=subject_room_id,
        is_acknowledged=False,
    ).update(is_acknowledged=True)

    # Recalculate percentile rankings for all affected tags
    for tag_id in affected_tag_ids:
        _recalculate_percentile(subject_room_id, tag_id)


def _recalculate_percentile(subject_room_id: int, tag_id: int) -> None:
    """
    Recalculate percentile rank for all students in a SubjectRoom for a given tag.
    Uses rank-based percentile: student at rank i out of n gets percentile = i/n.
    """
    from openshiksha.apps.edge.models import StudentProficiency, SubjectRoomProficiency

    profs = list(
        StudentProficiency.objects.filter(
            subject_room_id=subject_room_id,
            question_tag_id=tag_id,
        ).order_by("rate")
    )

    if not profs:
        return

    n = len(profs)
    for i, prof in enumerate(profs):
        percentile = i / n  # rank fraction: bottom student gets 0, top gets (n-1)/n
        prof.recalculate_score(percentile)

    # Update SubjectRoom aggregate
    agg = StudentProficiency.objects.filter(
        subject_room_id=subject_room_id,
        question_tag_id=tag_id,
    ).aggregate(avg_rate=Avg("rate"), avg_score=Avg("score"))

    SubjectRoomProficiency.objects.update_or_create(
        subject_room_id=subject_room_id,
        question_tag_id=tag_id,
        defaults={
            "rate": agg["avg_rate"] or 0.0,
            "score": agg["avg_score"] or 0.0,
        },
    )
