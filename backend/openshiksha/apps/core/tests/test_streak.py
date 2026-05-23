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
        # Gap: skip 5/22, submit on 5/23
        streak.record_activity(date(2026, 5, 23))

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
