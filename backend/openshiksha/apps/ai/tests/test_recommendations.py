"""
Tests for AI-Powered Content Recommendations.

Covers:
- generate_recommendations_for_student() algorithm
- ContentRecommendation model helpers
- PracticePlan model
- build_practice_plan() helper
"""

import pytest

from openshiksha.apps.ai.analytics import (
    MAX_PLAN_RECOMMENDATIONS,
    SPACED_REVIEW_DAYS,
    build_practice_plan,
    generate_recommendations_for_student,
)
from openshiksha.apps.ai.models import (
    ContentRecommendation,
    GapSeverity,
    LearningGap,
    PracticePlan,
    RecommendationPriority,
    RecommendationReason,
)

# ─────────────────────────────────────────────────────────────
# Fixtures / helpers (shared with test_analytics.py pattern)
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def db_setup(db):
    """Create a minimal educational structure: board→school→standard→subject→chapter→classroom→teacher→student→subject_room."""
    from openshiksha.apps.core.models import Board, Chapter, ClassRoom, School, Standard, Subject, SubjectRoom, User

    board = Board.objects.create(name="CBSE_R")
    school = School.objects.create(name="Reco School", board=board)
    standard = Standard.objects.get_or_create(number=7)[0]
    subject = Subject.objects.get_or_create(name="Science")[0]
    teacher = User.objects.create_user(username="teacher_r", password="pass", role="teacher")
    student = User.objects.create_user(username="student_r", password="pass", role="student")
    classroom = ClassRoom.objects.create(school=school, standard=standard, division="B", academic_year="2025-26")
    classroom.students.add(student)

    # Three chapters in order
    ch1 = Chapter.objects.create(name="Nutrition", subject=subject, standard=standard, order=1)
    ch2 = Chapter.objects.create(name="Respiration", subject=subject, standard=standard, order=2)
    ch3 = Chapter.objects.create(name="Transport", subject=subject, standard=standard, order=3)

    subject_room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    subject_room.students.add(student)

    return {
        "student": student,
        "teacher": teacher,
        "subject_room": subject_room,
        "chapters": [ch1, ch2, ch3],
        "subject": subject,
        "standard": standard,
    }


def _make_active_gap(db_setup, chapter, severity, avg_score):
    """Create an active LearningGap for the student in db_setup."""
    LearningGap.objects.create(
        student=db_setup["student"],
        chapter=chapter,
        subject_room=db_setup["subject_room"],
        avg_score=avg_score,
        severity=severity,
        tick_count=5,
        is_resolved=False,
    )


def _make_resolved_gap(db_setup, chapter, avg_score, days_ago=2):
    """Create a recently-resolved LearningGap."""
    from datetime import timedelta

    from django.utils import timezone

    gap = LearningGap.objects.create(
        student=db_setup["student"],
        chapter=chapter,
        subject_room=db_setup["subject_room"],
        avg_score=avg_score,
        severity=GapSeverity.MILD,
        tick_count=5,
        is_resolved=True,
    )
    # Backdate refreshed_at to simulate it was resolved 'days_ago' days ago
    LearningGap.objects.filter(pk=gap.pk).update(refreshed_at=timezone.now() - timedelta(days=days_ago))
    return gap


# ─────────────────────────────────────────────────────────────
# ContentRecommendation model helpers
# ─────────────────────────────────────────────────────────────


class TestContentRecommendationHelpers:
    def test_priority_for_severe_gap(self):
        assert (
            ContentRecommendation.priority_for_reason(RecommendationReason.SEVERE_GAP) == RecommendationPriority.URGENT
        )

    def test_priority_for_moderate_gap(self):
        assert (
            ContentRecommendation.priority_for_reason(RecommendationReason.MODERATE_GAP) == RecommendationPriority.HIGH
        )

    def test_priority_for_spaced_review(self):
        assert (
            ContentRecommendation.priority_for_reason(RecommendationReason.SPACED_REVIEW) == RecommendationPriority.HIGH
        )

    def test_priority_for_mild_gap(self):
        assert ContentRecommendation.priority_for_reason(RecommendationReason.MILD_GAP) == RecommendationPriority.MEDIUM

    def test_priority_for_next_topic(self):
        assert ContentRecommendation.priority_for_reason(RecommendationReason.NEXT_TOPIC) == RecommendationPriority.LOW


# ─────────────────────────────────────────────────────────────
# generate_recommendations_for_student
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGenerateRecommendations:
    def test_no_gaps_no_ticks_returns_next_topic_suggestions(self, db_setup):
        """With no gaps and no ticks, all chapters are unvisited → next_topic recommendations."""
        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        assert len(recs) == 3  # 3 chapters, all unvisited
        for rec in recs:
            assert rec["reason"] == RecommendationReason.NEXT_TOPIC
            assert rec["priority"] == RecommendationPriority.LOW
            assert rec["score_snapshot"] is None

    def test_next_topic_chapters_are_ordered_by_chapter_order(self, db_setup):
        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        chapter_ids = [r["chapter_id"] for r in recs]
        expected_order = [c.id for c in db_setup["chapters"]]
        assert chapter_ids == expected_order

    def test_severe_gap_gets_urgent_priority(self, db_setup):
        ch1 = db_setup["chapters"][0]
        _make_active_gap(db_setup, ch1, GapSeverity.SEVERE, 0.15)

        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        ch1_rec = next(r for r in recs if r["chapter_id"] == ch1.id)
        assert ch1_rec["reason"] == RecommendationReason.SEVERE_GAP
        assert ch1_rec["priority"] == RecommendationPriority.URGENT

    def test_moderate_gap_gets_high_priority(self, db_setup):
        ch1 = db_setup["chapters"][0]
        _make_active_gap(db_setup, ch1, GapSeverity.MODERATE, 0.32)

        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        ch1_rec = next(r for r in recs if r["chapter_id"] == ch1.id)
        assert ch1_rec["reason"] == RecommendationReason.MODERATE_GAP
        assert ch1_rec["priority"] == RecommendationPriority.HIGH

    def test_mild_gap_gets_medium_priority(self, db_setup):
        ch1 = db_setup["chapters"][0]
        _make_active_gap(db_setup, ch1, GapSeverity.MILD, 0.45)

        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        ch1_rec = next(r for r in recs if r["chapter_id"] == ch1.id)
        assert ch1_rec["reason"] == RecommendationReason.MILD_GAP
        assert ch1_rec["priority"] == RecommendationPriority.MEDIUM

    def test_recently_resolved_gap_triggers_spaced_review(self, db_setup):
        ch1 = db_setup["chapters"][0]
        _make_resolved_gap(db_setup, ch1, avg_score=0.72, days_ago=2)

        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        ch1_rec = next(r for r in recs if r["chapter_id"] == ch1.id)
        assert ch1_rec["reason"] == RecommendationReason.SPACED_REVIEW
        assert ch1_rec["priority"] == RecommendationPriority.HIGH

    def test_old_resolved_gap_not_recommended_for_spaced_review(self, db_setup):
        ch1 = db_setup["chapters"][0]
        _make_resolved_gap(db_setup, ch1, avg_score=0.72, days_ago=SPACED_REVIEW_DAYS + 5)

        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        # ch1 should still appear as next_topic (no ticks means unvisited),
        # but NOT as spaced_review
        ch1_recs = [r for r in recs if r["chapter_id"] == ch1.id]
        # There may be a next_topic rec but never a spaced_review
        for r in ch1_recs:
            assert r["reason"] != RecommendationReason.SPACED_REVIEW

    def test_gap_chapters_excluded_from_next_topic(self, db_setup):
        """Chapters with active gaps should not also appear as next_topic."""
        ch1, ch2, ch3 = db_setup["chapters"]
        _make_active_gap(db_setup, ch1, GapSeverity.SEVERE, 0.10)

        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        # ch1 should appear exactly once
        ch1_recs = [r for r in recs if r["chapter_id"] == ch1.id]
        assert len(ch1_recs) == 1
        assert ch1_recs[0]["reason"] == RecommendationReason.SEVERE_GAP

    def test_results_sorted_priority_ascending(self, db_setup):
        ch1, ch2, ch3 = db_setup["chapters"]
        _make_active_gap(db_setup, ch1, GapSeverity.SEVERE, 0.10)
        _make_active_gap(db_setup, ch2, GapSeverity.MILD, 0.44)

        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        priorities = [r["priority"] for r in recs]
        assert priorities == sorted(priorities)

    def test_score_snapshot_stored_for_gap_recommendations(self, db_setup):
        ch1 = db_setup["chapters"][0]
        _make_active_gap(db_setup, ch1, GapSeverity.MODERATE, 0.30)

        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        ch1_rec = next(r for r in recs if r["chapter_id"] == ch1.id)
        assert ch1_rec["score_snapshot"] == pytest.approx(0.30, abs=1e-4)

    def test_empty_subject_room_returns_no_active_gaps(self, db_setup):
        """Student with no ticks and no gaps only gets next_topic."""
        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        assert all(r["reason"] == RecommendationReason.NEXT_TOPIC for r in recs)


# ─────────────────────────────────────────────────────────────
# build_practice_plan
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestBuildPracticePlan:
    def test_plan_capped_at_max_recommendations(self, db_setup):
        """When more recommendations exist than MAX_PLAN_RECOMMENDATIONS, only top N included."""
        # Create 6 chapters to exceed the cap
        from openshiksha.apps.core.models import Chapter

        [
            Chapter.objects.create(
                name=f"Ch Extra {i}",
                subject=db_setup["subject"],
                standard=db_setup["standard"],
                order=10 + i,
            )
            for i in range(3)
        ]
        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        plan = build_practice_plan(db_setup["student"], db_setup["subject_room"], recs)
        assert len(plan["chapter_ids"]) <= MAX_PLAN_RECOMMENDATIONS

    def test_plan_estimated_minutes_defaults_when_no_problem_set(self, db_setup):
        from openshiksha.apps.ai.analytics import DEFAULT_MINUTES_PER_REC

        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        plan = build_practice_plan(db_setup["student"], db_setup["subject_room"], recs)
        n = len(plan["chapter_ids"])
        assert plan["estimated_minutes"] == n * DEFAULT_MINUTES_PER_REC

    def test_plan_estimated_minutes_uses_problem_set_estimate(self, db_setup):
        from openshiksha.apps.core.models import ProblemSet

        ch1 = db_setup["chapters"][0]
        ps = ProblemSet.objects.create(
            standard=db_setup["standard"],
            subject=db_setup["subject"],
            chapter=ch1,
            title="Test PS",
            number=1,
            estimated_minutes=20,
        )

        # Build a single-item rec list pointing at this problem set
        recs = [
            {
                "chapter_id": ch1.id,
                "reason": RecommendationReason.NEXT_TOPIC,
                "priority": RecommendationPriority.LOW,
                "score_snapshot": None,
                "problem_set_id": ps.id,
            }
        ]
        plan = build_practice_plan(db_setup["student"], db_setup["subject_room"], recs)
        assert plan["estimated_minutes"] == 20

    def test_plan_chapter_ids_in_priority_order(self, db_setup):
        ch1, ch2, ch3 = db_setup["chapters"]
        _make_active_gap(db_setup, ch1, GapSeverity.SEVERE, 0.10)
        _make_active_gap(db_setup, ch2, GapSeverity.MILD, 0.45)

        recs = generate_recommendations_for_student(db_setup["student"], db_setup["subject_room"])
        plan = build_practice_plan(db_setup["student"], db_setup["subject_room"], recs)
        # ch1 (severe=urgent) must come before ch2 (mild=medium)
        assert plan["chapter_ids"].index(ch1.id) < plan["chapter_ids"].index(ch2.id)


# ─────────────────────────────────────────────────────────────
# PracticePlan model
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestPracticePlanModel:
    def test_practice_plan_str(self, db_setup):
        from datetime import date

        plan = PracticePlan.objects.create(
            student=db_setup["student"],
            subject_room=db_setup["subject_room"],
            plan_date=date(2026, 3, 29),
            estimated_minutes=30,
        )
        assert "2026-03-29" in str(plan)
        assert "30min" in str(plan)

    def test_practice_plan_unique_per_student_room_date(self, db_setup):
        from datetime import date

        from django.db import IntegrityError

        today = date(2026, 3, 29)
        PracticePlan.objects.create(
            student=db_setup["student"],
            subject_room=db_setup["subject_room"],
            plan_date=today,
            estimated_minutes=20,
        )
        with pytest.raises(IntegrityError):
            PracticePlan.objects.create(
                student=db_setup["student"],
                subject_room=db_setup["subject_room"],
                plan_date=today,
                estimated_minutes=10,
            )

    def test_practice_plan_accepts_recommendations(self, db_setup):
        from datetime import date

        ch1 = db_setup["chapters"][0]

        rec = ContentRecommendation.objects.create(
            student=db_setup["student"],
            subject_room=db_setup["subject_room"],
            chapter=ch1,
            reason=RecommendationReason.NEXT_TOPIC,
            priority=RecommendationPriority.LOW,
        )
        plan = PracticePlan.objects.create(
            student=db_setup["student"],
            subject_room=db_setup["subject_room"],
            plan_date=date(2026, 3, 29),
            estimated_minutes=10,
        )
        plan.recommendations.add(rec)
        assert plan.recommendations.count() == 1


# ─────────────────────────────────────────────────────────────
# ContentRecommendation model
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestContentRecommendationModel:
    def test_str_includes_reason_and_priority(self, db_setup):
        ch1 = db_setup["chapters"][0]
        rec = ContentRecommendation.objects.create(
            student=db_setup["student"],
            subject_room=db_setup["subject_room"],
            chapter=ch1,
            reason=RecommendationReason.SEVERE_GAP,
            priority=RecommendationPriority.URGENT,
            score_snapshot=0.10,
        )
        s = str(rec)
        assert "Severe Gap" in s
        assert "p1" in s

    def test_unique_constraint_per_student_chapter_room(self, db_setup):
        from django.db import IntegrityError

        ch1 = db_setup["chapters"][0]
        ContentRecommendation.objects.create(
            student=db_setup["student"],
            subject_room=db_setup["subject_room"],
            chapter=ch1,
            reason=RecommendationReason.NEXT_TOPIC,
            priority=RecommendationPriority.LOW,
        )
        with pytest.raises(IntegrityError):
            ContentRecommendation.objects.create(
                student=db_setup["student"],
                subject_room=db_setup["subject_room"],
                chapter=ch1,
                reason=RecommendationReason.MILD_GAP,
                priority=RecommendationPriority.MEDIUM,
            )

    def test_default_is_active_true(self, db_setup):
        ch1 = db_setup["chapters"][0]
        rec = ContentRecommendation.objects.create(
            student=db_setup["student"],
            subject_room=db_setup["subject_room"],
            chapter=ch1,
            reason=RecommendationReason.NEXT_TOPIC,
            priority=RecommendationPriority.LOW,
        )
        assert rec.is_active is True
        assert rec.is_actioned is False
        assert rec.actioned_at is None
