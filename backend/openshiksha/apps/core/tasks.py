"""
Celery tasks for grading submissions and updating analytics.

These tasks run asynchronously after a student submits answers.
Flow: grade_submission → _update_assignment_aggregates + update_proficiency
"""

import logging

from celery import shared_task

from django.db.models import Avg

logger = logging.getLogger(__name__)

REMEDIAL_THRESHOLD = 0.30


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
    assignment = submission.assignment
    problem_set = assignment.problem_set
    subject_room = assignment.subject_room
    # AIV-7: route through resolve_assignment_content so the grader reads the
    # ProblemSetVersion FK when set and falls back to assigned_content when not.
    from openshiksha.apps.core.snapshots import resolve_assignment_content

    snapshot = resolve_assignment_content(assignment)

    # AIV-2a: prefer the per-assignment snapshot — it pins the exact
    # correct_answer/subpart_type/variable_constraints the student was given,
    # so editing the live ProblemSet/Question afterwards cannot retroactively
    # re-grade past work. Fall back to the live set only for legacy rows the
    # 0023 backfill couldn't reach (defensive; should be unreachable in prod).
    if snapshot and snapshot.get("questions"):
        # Snapshot path. Tick still FKs the live QuestionSubpart row (we need a
        # row to point at and the subpart_id is preserved in the snapshot), but
        # the *grading inputs* come from the frozen copy.
        snap_subparts: list[dict] = []
        for q in snapshot["questions"]:
            for sp in q.get("subparts") or []:
                snap_subparts.append({"question_id": q["question_id"], **sp})

        live_subpart_ids = [s["subpart_id"] for s in snap_subparts]
        live_by_id = {
            sp.id: sp for sp in QuestionSubpart.objects.filter(id__in=live_subpart_ids).select_related("question")
        }

        subpart_count_by_question: dict[int, int] = {}
        for s in snap_subparts:
            qid = s["question_id"]
            subpart_count_by_question[qid] = subpart_count_by_question.get(qid, 0) + 1

        total_subparts = len(snap_subparts)
        attempted = 0
        total_mark = 0.0
        ticks_to_create = []
        student_id = submission.student_id

        for s in snap_subparts:
            sp_id = s["subpart_id"]
            answer_key = str(sp_id)
            if answer_key not in answers:
                continue
            live_sp = live_by_id.get(sp_id)
            if live_sp is None:
                # Subpart was deleted post-assign. We still graded it as
                # 0 (attempted but no FK target) to keep totals consistent.
                attempted += 1
                continue

            attempted += 1
            student_answer = answers[answer_key]
            # M7-03: snapshot subpart_type falls back to the live question
            # type for hand-authored rows that predate subpart_type.
            grading_type = s.get("subpart_type") or live_sp.question.question_type
            mark = _grade_subpart(
                grading_type,
                student_answer,
                s.get("correct_answer") or {},
                student_id=student_id,
                subpart_id=sp_id,
                original_options=s.get("options"),
                variable_constraints=s.get("variable_constraints"),
            )
            total_mark += mark

            ticks_to_create.append(
                Tick(
                    student=submission.student,
                    question_subpart=live_sp,
                    submission=submission,
                    subject_room=subject_room,
                    mark=mark,
                )
            )
    else:
        # Legacy / no-snapshot fallback — graded against the live set.
        question_ids = list(problem_set.questions.values_list("id", flat=True))
        subparts = list(
            QuestionSubpart.objects.filter(question__in=question_ids)
            .select_related("question")
            .order_by("question_id", "index")
        )

        subpart_count_by_question = {}
        for sp in subparts:
            subpart_count_by_question[sp.question_id] = subpart_count_by_question.get(sp.question_id, 0) + 1

        total_subparts = len(subparts)
        attempted = 0
        total_mark = 0.0
        ticks_to_create = []
        student_id = submission.student_id

        for subpart in subparts:
            answer_key = str(subpart.id)
            if answer_key not in answers:
                continue

            attempted += 1
            student_answer = answers[answer_key]
            grading_type = subpart.subpart_type or subpart.question.question_type
            mark = _grade_subpart(
                grading_type,
                student_answer,
                subpart.correct_answer,
                student_id=student_id,
                subpart_id=subpart.id,
                original_options=subpart.options,
                variable_constraints=subpart.variable_constraints,
            )
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

    # Email student with grading result
    from openshiksha.apps.core.emails import notify_grading_complete

    score_pct = int(submission.score * 100) if submission.score is not None else 0
    notify_grading_complete(
        submission.student,
        submission.assignment.problem_set.title,
        score_pct,
    )

    # Queue downstream tasks
    _update_assignment_aggregates.delay(submission.assignment_id)
    update_proficiency.delay(submission.student_id, subject_room.id)

    # Trigger AI analytics pipeline (learning gaps, recommendations, mastery, learning path)
    from openshiksha.apps.ai.tasks import (
        analyze_student_subject_room,
        generate_class_insights_for_subject_room,
        generate_explanations_for_submission,
    )

    analyze_student_subject_room.delay(submission.student_id, subject_room.id)
    generate_class_insights_for_subject_room.delay(subject_room.id)

    # Generate per-subpart AI explanations for the student
    generate_explanations_for_submission.delay(submission_id)

    # Create remedial assignment if student scored below threshold
    if submission.score is not None and submission.score < REMEDIAL_THRESHOLD:
        _create_remedial_assignment(submission.pk)

    return {
        "submission_id": submission_id,
        "total_subparts": total_subparts,
        "attempted": attempted,
        "score": submission.score,
        "completion": submission.completion,
        "ticks_created": len(ticks_to_create),
    }


def _grade_subpart(
    question_type: str,
    student_answer,
    correct_answer: dict,
    student_id: int | None = None,
    subpart_id: int | None = None,
    original_options: list | None = None,
    variable_constraints: dict | None = None,
) -> float:
    """
    Grade a single subpart answer. Returns a fraction (0.0–1.0).
    Matching questions support partial credit.

    For MCQ/multi_select, if student_id + subpart_id + original_options are
    provided, the student's submitted key is reverse-mapped through the
    Croupier shuffle back to the original storage key before comparison.

    For numeric questions with variable_constraints, the correct_answer["answer"]
    may be an expression like "({{c}} - {{b}}) / {{a}}" that is evaluated with
    the same deterministic variable values shown to the student.
    """
    if not correct_answer or "answer" not in correct_answer:
        return 0.0

    expected = correct_answer["answer"]

    if question_type in ("mcq", "fill_blank", "multi_select"):
        answer_to_compare = str(student_answer)
        if question_type in ("mcq", "multi_select") and student_id and subpart_id and original_options:
            from openshiksha.apps.api.croupier import get_original_key

            answer_to_compare = get_original_key(student_id, subpart_id, str(student_answer), original_options)
        return 1.0 if answer_to_compare == str(expected) else 0.0

    if question_type == "numeric":
        # Re-derive variable values and evaluate expression answers
        if variable_constraints and student_id and subpart_id:
            from openshiksha.apps.api.croupier import safe_eval_expr, sample_variable_values

            variable_values = sample_variable_values(variable_constraints, student_id, subpart_id)
            expected_raw = str(expected)
            if "{{" in expected_raw:
                try:
                    expected_float = safe_eval_expr(expected_raw, variable_values)
                    try:
                        submitted_float = float(student_answer)
                        return 1.0 if abs(submitted_float - expected_float) < 0.01 else 0.0
                    except (TypeError, ValueError):
                        return 0.0
                except (ValueError, ZeroDivisionError):
                    return 0.0
        # Non-variable numeric: direct comparison
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

    from openshiksha.apps.edge.models import StudentProficiencySnapshot

    n = len(profs)
    snapshots_to_create = []
    for i, prof in enumerate(profs):
        percentile = i / n  # rank fraction: bottom student gets 0, top gets (n-1)/n
        prof.recalculate_score(percentile)
        snapshots_to_create.append(
            StudentProficiencySnapshot(
                student_id=prof.student_id,
                question_tag_id=prof.question_tag_id,
                subject_room_id=prof.subject_room_id,
                score=prof.score,
            )
        )
    StudentProficiencySnapshot.objects.bulk_create(snapshots_to_create)

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


@shared_task
def send_due_date_reminders(window_hours: int = 24) -> dict:
    """
    Email students about assignments due within the next ``window_hours``.

    Runs on a Celery beat schedule (see CELERY_BEAT_SCHEDULE). For each upcoming
    assignment, reminds every enrolled student who:
      - has an email address and has not opted out of reminders,
      - has not already submitted the assignment, and
      - has not already been reminded for this assignment.

    Idempotency is guaranteed by an AssignmentReminder row per (assignment, student):
    the row is created before the email is sent, so repeat runs never double-email.
    """
    from datetime import timedelta

    from django.utils import timezone

    from openshiksha.apps.core.emails import build_due_reminder_push, notify_due_date_reminder
    from openshiksha.apps.core.models import (
        Assignment,
        AssignmentReminder,
        PushSubscription,
        Submission,
        UserRole,
    )
    from openshiksha.apps.core.push import send_web_push

    now = timezone.now()
    window_end = now + timedelta(hours=window_hours)

    assignments = (
        Assignment.objects.filter(
            due_at__gt=now,
            due_at__lte=window_end,
            subject_room__is_active=True,
        )
        .select_related("problem_set", "subject_room", "target_student")
        .prefetch_related("subject_room__students")
    )

    stats = {"assignments": 0, "reminded": 0, "skipped": 0}

    for assignment in assignments:
        stats["assignments"] += 1

        if assignment.target_student_id:
            students = [assignment.target_student] if assignment.target_student else []
        else:
            students = list(assignment.subject_room.students.all())

        if not students:
            continue

        # Students who already submitted this assignment are not reminded.
        submitted_ids = set(
            Submission.objects.filter(
                assignment=assignment,
                student__in=students,
                submitted_at__isnull=False,
            ).values_list("student_id", flat=True)
        )
        # Students already reminded for this assignment.
        reminded_ids = set(
            AssignmentReminder.objects.filter(assignment=assignment).values_list("student_id", flat=True)
        )
        # Students with at least one Web Push subscription (MPN-5). Push reaches
        # a home-screen PWA install even when the student has no email on file.
        push_user_ids = set(PushSubscription.objects.filter(user__in=students).values_list("user_id", flat=True))

        due_str = timezone.localtime(assignment.due_at).strftime("on %B %d at %I:%M %p")

        for student in students:
            if student.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
                continue
            if student.id in submitted_ids or student.id in reminded_ids:
                stats["skipped"] += 1
                continue
            # A single opt-out governs both channels (email + push) for v1.
            if student.email_reminders_opt_out:
                stats["skipped"] += 1
                continue

            has_email = bool(student.email)
            has_push = student.id in push_user_ids
            if not has_email and not has_push:
                # No deliverable channel — don't burn the idempotency row.
                stats["skipped"] += 1
                continue

            # Create the log first so a crash mid-send never produces a duplicate later.
            _, created = AssignmentReminder.objects.get_or_create(assignment=assignment, student=student)
            if not created:
                stats["skipped"] += 1
                continue

            if has_email:
                notify_due_date_reminder(student, assignment.problem_set.title, due_str)
            if has_push:
                # send_web_push never raises into the task; email is the source
                # of truth and must not fail because a push endpoint is dead.
                payload = build_due_reminder_push(student, assignment.problem_set.title, due_str)
                payload["url"] = f"/student/assignments/{assignment.id}"
                payload["tag"] = f"assignment-{assignment.id}"
                send_web_push(student, payload)
            stats["reminded"] += 1

    logger.info(
        "send_due_date_reminders: assignments=%d reminded=%d skipped=%d",
        stats["assignments"],
        stats["reminded"],
        stats["skipped"],
    )
    return stats


def _create_remedial_assignment(submission_id: int) -> None:
    """
    Create a remedial ProblemSet + Assignment for a student who scored below REMEDIAL_THRESHOLD.

    Targets only the questions the student answered incorrectly.
    Idempotent: skips if a remedial already exists for this assignment + student.
    """
    from datetime import timedelta

    from django.db.models import Max
    from django.utils import timezone

    from openshiksha.apps.core.models import Assignment, ProblemSet, Submission
    from openshiksha.apps.edge.models import Tick

    try:
        submission = Submission.objects.select_related(
            "assignment__problem_set",
            "assignment__subject_room",
            "student",
            "assignment__assigned_by",
        ).get(pk=submission_id)
    except Submission.DoesNotExist:
        logger.error(f"_create_remedial_assignment: Submission {submission_id} not found")
        return

    orig = submission.assignment
    orig_ps = orig.problem_set

    # Idempotency: skip if a remedial already exists for this specific student + source assignment
    already_exists = Assignment.objects.filter(
        problem_set__is_remedial=True,
        problem_set__source_assignment=orig,
        target_student=submission.student,
    ).exists()
    if already_exists:
        return

    # Find questions the student got wrong (any subpart with mark < 1.0)
    wrong_question_ids = list(
        Tick.objects.filter(submission=submission, mark__lt=1.0)
        .values_list("question_subpart__question_id", flat=True)
        .distinct()
    )

    if not wrong_question_ids:
        logger.warning(
            f"_create_remedial_assignment: no wrong ticks for submission {submission_id} "
            f"despite score {submission.score:.2f} — skipping"
        )
        return

    # Pick a unique number to satisfy ProblemSet.unique_together
    max_num = (
        ProblemSet.objects.filter(
            school=orig_ps.school,
            standard=orig_ps.standard,
            subject=orig_ps.subject,
            chapter=orig_ps.chapter,
        ).aggregate(Max("number"))["number__max"]
        or 0
    )

    remedial_ps = ProblemSet.objects.create(
        title=f"Remedial: {orig_ps.title}",
        school=orig_ps.school,
        standard=orig_ps.standard,
        subject=orig_ps.subject,
        chapter=orig_ps.chapter,
        number=max_num + 1,
        is_remedial=True,
        source_assignment=orig,
        created_by=orig.assigned_by,
    )
    remedial_ps.questions.set(wrong_question_ids)

    due = timezone.now() + timedelta(days=3)
    # AIV-1: snapshot remedial content at creation time so the grader and
    # student renderer read from the frozen copy, not the live remedial set.
    # AIV-7: also pin a deduplicated ProblemSetVersion FK.
    from openshiksha.apps.core.snapshots import build_assignment_snapshot, get_or_create_version_for

    version, _ = get_or_create_version_for(remedial_ps, created_by=orig.assigned_by)
    Assignment.objects.create(
        problem_set=remedial_ps,
        subject_room=orig.subject_room,
        assigned_by=orig.assigned_by,
        due_at=due,
        target_student=submission.student,
        assigned_content=build_assignment_snapshot(remedial_ps),
        problem_set_version=version,
    )

    # Email student about the new remedial assignment
    from openshiksha.apps.core.emails import notify_remedial_assigned

    notify_remedial_assigned(
        submission.student,
        orig_ps.chapter.name,
        due.strftime("%B %d"),
    )

    logger.info(
        f"Created remedial assignment for student {submission.student_id} "
        f"(submission {submission_id}, {len(wrong_question_ids)} wrong questions)"
    )
