"""
Tests for the AI analytics algorithms.

Uses pytest-django with in-memory SQLite (no running Postgres needed).
Tests cover the pure computation layer (analytics.py) and the model
helper methods, not the Celery tasks (those would need integration tests).
"""

import pytest

from django.utils import timezone

from openshiksha.apps.ai.analytics import (
    MIN_TICKS_FOR_GAP,
    MIN_TICKS_FOR_PREDICTION,
    STRUGGLE_THRESHOLD,
    _sigmoid,
    detect_gaps_for_student,
    generate_insights_for_subject_room,
    predict_performance_for_student,
)
from openshiksha.apps.ai.models import ClassInsight, GapSeverity, LearningGap, PerformancePrediction

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def make_user(db, role="student", username=None):
    from openshiksha.apps.core.models import User

    username = username or f"user_{id(role)}"
    return User.objects.create_user(username=username, password="pass", role=role)


def make_board(db):
    from openshiksha.apps.core.models import Board

    return Board.objects.create(name="CBSE")


def make_school(db, board):
    from openshiksha.apps.core.models import School

    return School.objects.create(name="Test School", board=board)


def make_standard(db):
    from openshiksha.apps.core.models import Standard

    return Standard.objects.get_or_create(number=6)[0]


def make_subject(db):
    from openshiksha.apps.core.models import Subject

    return Subject.objects.get_or_create(name="Math")[0]


def make_chapter(db, subject, standard, name="Fractions"):
    from openshiksha.apps.core.models import Chapter

    return Chapter.objects.create(name=name, subject=subject, standard=standard)


def make_classroom(db, school, standard):
    from openshiksha.apps.core.models import ClassRoom

    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


def make_subject_room(db, classroom, subject, teacher, is_active=True):
    from openshiksha.apps.core.models import SubjectRoom

    return SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher, is_active=is_active)


def make_question(db, chapter, subject, standard):
    from openshiksha.apps.core.models import Question, QuestionType

    return Question.objects.create(chapter=chapter, subject=subject, standard=standard, question_type=QuestionType.MCQ)


def make_subpart(db, question, index=0):
    from openshiksha.apps.core.models import QuestionSubpart

    return QuestionSubpart.objects.create(question=question, index=index)


def make_submission(db, student, assignment):
    from openshiksha.apps.core.models import Submission

    return Submission.objects.create(student=student, assignment=assignment)


def make_assignment(db, subject_room, problem_set, teacher, due_at=None):
    from django.utils import timezone

    from openshiksha.apps.core.models import Assignment

    due_at = due_at or timezone.now() + timezone.timedelta(days=7)
    return Assignment.objects.create(
        subject_room=subject_room,
        problem_set=problem_set,
        assigned_by=teacher,
        due_at=due_at,
    )


def make_problem_set(db, school, standard, subject, chapter, teacher):
    from openshiksha.apps.core.models import ProblemSet

    return ProblemSet.objects.create(
        school=school, standard=standard, subject=subject, chapter=chapter, title="Test Set", created_by=teacher
    )


def make_tick(db, student, subpart, submission, subject_room, mark, created_at=None):
    from openshiksha.apps.edge.models import Tick

    tick = Tick.objects.create(
        student=student,
        question_subpart=subpart,
        submission=submission,
        subject_room=subject_room,
        mark=mark,
    )
    if created_at is not None:
        Tick.objects.filter(pk=tick.pk).update(created_at=created_at)
        tick.refresh_from_db()
    return tick


# ─────────────────────────────────────────────────────────────
# Unit tests — model helper methods
# ─────────────────────────────────────────────────────────────


class TestLearningGapModel:
    def test_severity_severe(self):
        assert LearningGap.severity_for_score(0.10) == GapSeverity.SEVERE

    def test_severity_moderate(self):
        assert LearningGap.severity_for_score(0.30) == GapSeverity.MODERATE

    def test_severity_mild(self):
        assert LearningGap.severity_for_score(0.45) == GapSeverity.MILD

    def test_severity_boundary_25(self):
        # 0.25 is the boundary between severe and moderate — should be moderate
        assert LearningGap.severity_for_score(0.25) == GapSeverity.MODERATE

    def test_severity_boundary_40(self):
        # 0.40 is the boundary between moderate and mild — should be mild
        assert LearningGap.severity_for_score(0.40) == GapSeverity.MILD


class TestClassInsightModel:
    def test_struggling(self):
        assert ClassInsight.insight_type_for_pct(0.50) == "struggling"

    def test_at_risk(self):
        assert ClassInsight.insight_type_for_pct(0.30) == "at_risk"

    def test_proficient(self):
        assert ClassInsight.insight_type_for_pct(0.10) == "proficient"


class TestPerformancePredictionModel:
    def test_exam_ready(self):
        assert PerformancePrediction.readiness_for_score(0.85) == "exam_ready"

    def test_on_track(self):
        assert PerformancePrediction.readiness_for_score(0.70) == "on_track"

    def test_developing(self):
        assert PerformancePrediction.readiness_for_score(0.50) == "developing"

    def test_needs_attention(self):
        assert PerformancePrediction.readiness_for_score(0.20) == "needs_attention"


class TestSigmoid:
    def test_output_range(self):
        for x in [-10, -5, 0, 5, 10]:
            result = _sigmoid(x)
            assert 0.0 < result < 1.0

    def test_midpoint(self):
        assert abs(_sigmoid(0) - 0.5) < 1e-9


# ─────────────────────────────────────────────────────────────
# Integration tests — analytics functions with DB
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def base_objects(db):
    """Create the minimum set of objects needed for analytics tests."""
    board = make_board(db)
    school = make_school(db, board)
    standard = make_standard(db)
    subject = make_subject(db)
    chapter = make_chapter(db, subject, standard, "Fractions")
    chapter2 = make_chapter(db, subject, standard, "Decimals")
    classroom = make_classroom(db, school, standard)
    teacher = make_user(db, role="teacher", username="teacher1")
    student = make_user(db, role="student", username="student1")
    classroom.students.add(student)
    subject_room = make_subject_room(db, classroom, subject, teacher)
    question = make_question(db, chapter, subject, standard)
    question2 = make_question(db, chapter2, subject, standard)
    subpart = make_subpart(db, question)
    subpart2 = make_subpart(db, question2)
    problem_set = make_problem_set(db, school, standard, subject, chapter, teacher)
    assignment = make_assignment(db, subject_room, problem_set, teacher)
    submission = make_submission(db, student, assignment)
    return {
        "student": student,
        "teacher": teacher,
        "subject_room": subject_room,
        "chapter": chapter,
        "chapter2": chapter2,
        "subpart": subpart,
        "subpart2": subpart2,
        "submission": submission,
    }


class TestDetectGapsForStudent:
    def test_no_ticks_returns_empty(self, base_objects):
        result = detect_gaps_for_student(base_objects["student"], base_objects["subject_room"])
        assert result == []

    def test_fewer_than_min_ticks_ignored(self, db, base_objects):
        # Create MIN_TICKS_FOR_GAP - 1 ticks
        for _ in range(MIN_TICKS_FOR_GAP - 1):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.2,
            )
        result = detect_gaps_for_student(base_objects["student"], base_objects["subject_room"])
        assert result == []

    def test_poor_performance_creates_gap(self, db, base_objects):
        for _ in range(MIN_TICKS_FOR_GAP):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.2,
            )
        result = detect_gaps_for_student(base_objects["student"], base_objects["subject_room"])
        assert len(result) == 1
        gap = result[0]
        assert gap["chapter_id"] == base_objects["chapter"].pk
        assert gap["is_resolved"] is False
        assert gap["severity"] == GapSeverity.SEVERE
        assert abs(gap["avg_score"] - 0.2) < 1e-9

    def test_good_performance_marks_resolved(self, db, base_objects):
        for _ in range(MIN_TICKS_FOR_GAP):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.8,
            )
        result = detect_gaps_for_student(base_objects["student"], base_objects["subject_room"])
        assert len(result) == 1
        assert result[0]["is_resolved"] is True

    def test_borderline_score_not_flagged(self, db, base_objects):
        # Score exactly at STRUGGLE_THRESHOLD should not create a gap (not < threshold)
        for _ in range(MIN_TICKS_FOR_GAP):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=STRUGGLE_THRESHOLD,
            )
        result = detect_gaps_for_student(base_objects["student"], base_objects["subject_room"])
        # 0.50 is not < STRUGGLE_THRESHOLD (0.50) — not a gap, and not >= RESOLVED_THRESHOLD
        assert result == []


class TestGenerateInsightsForSubjectRoom:
    def test_no_ticks_returns_empty(self, base_objects):
        result = generate_insights_for_subject_room(base_objects["subject_room"])
        assert result == []

    def test_single_student_excluded(self, db, base_objects):
        # Needs at least 2 students assessed
        for _ in range(MIN_TICKS_FOR_GAP):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.2,
            )
        result = generate_insights_for_subject_room(base_objects["subject_room"])
        assert result == []

    def test_two_students_creates_insight(self, db, base_objects):
        student2 = make_user(db, role="student", username="student2")
        # Both students struggle in chapter
        for _ in range(MIN_TICKS_FOR_GAP):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.2,
            )
        # student2 needs their own submission — reuse existing assignment
        from openshiksha.apps.core.models import Submission

        submission2 = Submission.objects.create(
            assignment=base_objects["submission"].assignment,
            student=student2,
        )
        for _ in range(MIN_TICKS_FOR_GAP):
            make_tick(db, student2, base_objects["subpart"], submission2, base_objects["subject_room"], mark=0.3)

        result = generate_insights_for_subject_room(base_objects["subject_room"])
        assert len(result) == 1
        r = result[0]
        assert r["chapter_id"] == base_objects["chapter"].pk
        assert r["students_assessed"] == 2
        assert r["students_struggling"] == 2
        assert r["insight_type"] == "struggling"


class TestPredictPerformance:
    def test_insufficient_ticks_returns_none(self, base_objects):
        result = predict_performance_for_student(base_objects["student"], base_objects["subject_room"])
        assert result is None

    def test_prediction_returned_with_enough_ticks(self, db, base_objects):
        for _ in range(MIN_TICKS_FOR_PREDICTION + 2):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.7,
            )
        result = predict_performance_for_student(base_objects["student"], base_objects["subject_room"])
        assert result is not None
        assert 0.0 <= result["predicted_score"] <= 1.0
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["readiness_level"] in ["needs_attention", "developing", "on_track", "exam_ready"]
        assert "factors" in result
        assert "recent_trend" in result["factors"]

    def test_recent_ticks_weighted_more(self, db, base_objects):
        """Recent good performance should push score higher than all-old ticks."""
        old_time = timezone.now() - timezone.timedelta(days=60)
        # Older poor performance
        for _ in range(MIN_TICKS_FOR_PREDICTION):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.1,
                created_at=old_time,
            )
        # Recent good performance
        for _ in range(MIN_TICKS_FOR_PREDICTION):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.9,
            )
        result = predict_performance_for_student(base_objects["student"], base_objects["subject_room"])
        # With recency weighting: (2 * 0.9*5 + 0.1*5) / (2*5 + 5) = (9+0.5)/15 ≈ 0.633
        # Unweighted would be (0.9*5 + 0.1*5) / 10 = 0.5
        assert result["predicted_score"] > 0.5

    def test_trend_improving(self, db, base_objects):
        old_time = timezone.now() - timezone.timedelta(days=60)
        for _ in range(MIN_TICKS_FOR_PREDICTION):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.3,
                created_at=old_time,
            )
        for _ in range(MIN_TICKS_FOR_PREDICTION):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.8,
            )
        result = predict_performance_for_student(base_objects["student"], base_objects["subject_room"])
        assert result["factors"]["recent_trend"] == "improving"

    def test_trend_declining(self, db, base_objects):
        old_time = timezone.now() - timezone.timedelta(days=60)
        for _ in range(MIN_TICKS_FOR_PREDICTION):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.9,
                created_at=old_time,
            )
        for _ in range(MIN_TICKS_FOR_PREDICTION):
            make_tick(
                db,
                base_objects["student"],
                base_objects["subpart"],
                base_objects["submission"],
                base_objects["subject_room"],
                mark=0.2,
            )
        result = predict_performance_for_student(base_objects["student"], base_objects["subject_room"])
        assert result["factors"]["recent_trend"] == "declining"
