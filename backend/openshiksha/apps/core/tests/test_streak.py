"""
Tests for StudentStreak model and the me_streak API endpoint.
"""

from datetime import date

import pytest

from rest_framework.test import APIClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def board(db):
    from openshiksha.apps.core.models import Board

    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    from openshiksha.apps.core.models import School

    return School.objects.create(name="Streak Test School", board=board)


@pytest.fixture
def student(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="streak_student", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def teacher(db, school):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="streak_teacher", password="pass", role=UserRole.TEACHER, school=school)


# ---------------------------------------------------------------------------
# StudentStreak.record_activity unit tests (no signal, pure model logic)
# ---------------------------------------------------------------------------


class TestStudentStreakModel:
    def test_first_activity_sets_streak_to_one(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak.objects.create(student=student)
        streak.record_activity(date(2026, 5, 22))

        streak.refresh_from_db()
        assert streak.current_streak == 1
        assert streak.longest_streak == 1
        assert streak.last_activity_date == date(2026, 5, 22)

    def test_consecutive_day_increments_streak(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak.objects.create(student=student)
        streak.record_activity(date(2026, 5, 21))
        streak.refresh_from_db()
        streak.record_activity(date(2026, 5, 22))

        streak.refresh_from_db()
        assert streak.current_streak == 2
        assert streak.longest_streak == 2

    def test_same_day_submission_no_double_count(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak.objects.create(student=student)
        streak.record_activity(date(2026, 5, 22))
        streak.refresh_from_db()
        streak.record_activity(date(2026, 5, 22))  # same day

        streak.refresh_from_db()
        assert streak.current_streak == 1

    def test_broken_streak_resets_to_one(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak.objects.create(student=student)
        streak.record_activity(date(2026, 5, 20))
        streak.refresh_from_db()
        streak.record_activity(date(2026, 5, 21))
        streak.refresh_from_db()
        # Gap: skip 5/22 AND 5/23 (2 missed days — beyond grace window)
        streak.record_activity(date(2026, 5, 24))

        streak.refresh_from_db()
        assert streak.current_streak == 1
        assert streak.longest_streak == 2  # preserved from the 2-day run


# ---------------------------------------------------------------------------
# me_streak API endpoint
# ---------------------------------------------------------------------------


class TestMeStreakEndpoint:
    def test_student_gets_streak_data(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        StudentStreak.objects.create(student=student, current_streak=5, longest_streak=10)

        client = APIClient()
        client.force_authenticate(user=student)
        response = client.get("/api/v1/users/me/streak/")

        assert response.status_code == 200
        assert response.data["current_streak"] == 5
        assert response.data["longest_streak"] == 10
        assert "last_activity_date" in response.data

    def test_teacher_gets_403(self, db, teacher):
        client = APIClient()
        client.force_authenticate(user=teacher)
        response = client.get("/api/v1/users/me/streak/")

        assert response.status_code == 403

    def test_new_student_streak_auto_created(self, db, student):
        """A student with no streak row gets one created automatically."""
        client = APIClient()
        client.force_authenticate(user=student)
        response = client.get("/api/v1/users/me/streak/")

        assert response.status_code == 200
        assert response.data["current_streak"] == 0

    def test_streak_response_includes_grace_and_tier(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        StudentStreak.objects.create(student=student, current_streak=7, longest_streak=7)
        client = APIClient()
        client.force_authenticate(user=student)
        response = client.get("/api/v1/users/me/streak/")

        assert response.status_code == 200
        assert "streak_grace_used" in response.data
        assert "milestone_tier" in response.data
        assert response.data["milestone_tier"] == "week"


# ---------------------------------------------------------------------------
# Grace day and milestone tier unit tests
# ---------------------------------------------------------------------------


class TestGraceDayMechanic:
    def test_grace_day_preserves_streak(self, db, student):
        """Day 1, skip day 2, day 3 → streak = 2 (grace consumed)."""
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak.objects.create(student=student)
        streak.record_activity(date(2026, 5, 1))
        streak.refresh_from_db()
        streak.record_activity(date(2026, 5, 3))  # skipped 5/2

        streak.refresh_from_db()
        assert streak.current_streak == 2
        assert streak.streak_grace_used is True

    def test_grace_day_only_once_per_run(self, db, student):
        """Grace used → next miss resets streak."""
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak.objects.create(student=student)
        streak.record_activity(date(2026, 5, 1))
        streak.refresh_from_db()
        streak.record_activity(date(2026, 5, 3))  # grace used: streak=2, grace=True
        streak.refresh_from_db()
        streak.record_activity(date(2026, 5, 5))  # another 1-day gap, grace exhausted → reset

        streak.refresh_from_db()
        assert streak.current_streak == 1
        assert streak.streak_grace_used is False

    def test_grace_day_resets_on_consecutive(self, db, student):
        """After grace, a consecutive day clears grace_used."""
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak.objects.create(student=student)
        streak.record_activity(date(2026, 5, 1))
        streak.refresh_from_db()
        streak.record_activity(date(2026, 5, 3))  # grace: streak=2, grace=True
        streak.refresh_from_db()
        streak.record_activity(date(2026, 5, 4))  # consecutive: streak=3, grace=False

        streak.refresh_from_db()
        assert streak.current_streak == 3
        assert streak.streak_grace_used is False

    def test_two_day_gap_resets_streak(self, db, student):
        """Gap of 3 days (2 missed) always resets, even without grace used."""
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak.objects.create(student=student)
        streak.record_activity(date(2026, 5, 1))
        streak.refresh_from_db()
        streak.record_activity(date(2026, 5, 4))  # skipped 5/2 and 5/3

        streak.refresh_from_db()
        assert streak.current_streak == 1

    def test_longest_streak_preserved_through_grace(self, db, student):
        """longest_streak should survive grace-day usage."""
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak.objects.create(student=student)
        for day in range(1, 11):  # 10 consecutive days
            streak.record_activity(date(2026, 5, day))
            streak.refresh_from_db()

        assert streak.longest_streak == 10

        streak.record_activity(date(2026, 5, 12))  # grace (skip 5/11)
        streak.refresh_from_db()
        assert streak.current_streak == 11
        assert streak.longest_streak == 11


class TestMilestoneTier:
    def test_tier_none(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak(student=student, current_streak=2)
        assert streak.milestone_tier == "none"

    def test_tier_starter(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak(student=student, current_streak=3)
        assert streak.milestone_tier == "starter"

    def test_tier_week(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak(student=student, current_streak=7)
        assert streak.milestone_tier == "week"

    def test_tier_month(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak(student=student, current_streak=30)
        assert streak.milestone_tier == "month"

    def test_tier_champion(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak(student=student, current_streak=60)
        assert streak.milestone_tier == "champion"

    def test_tier_boundary_6(self, db, student):
        from openshiksha.apps.core.models import StudentStreak

        streak = StudentStreak(student=student, current_streak=6)
        assert streak.milestone_tier == "starter"
