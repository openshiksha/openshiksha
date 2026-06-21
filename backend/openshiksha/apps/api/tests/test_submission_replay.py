"""
MSO-6 — replay-safe / idempotent submission writes.

An offline mutation queue replays writes onto the server at-least-once. These
tests pin the server contract that makes that safe:

- The first submit grades exactly once.
- A replayed (duplicate) submit is an idempotent 200 no-op — never a re-grade,
  never a 400, and never a mutation of the graded snapshot.
- A stale auto-save PATCH that lands after submission is a harmless no-op — the
  answers are immutable post-submit and no grading is triggered.
- The normal first-submit path is unchanged.

Both layers are exercised: the serializer's no-op-on-resubmit guard and the
``trigger_grading_on_submit`` signal's ``score is None`` gate.
"""

from datetime import timedelta
from unittest.mock import patch

import pytest

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Assignment,
    Board,
    Chapter,
    ClassRoom,
    ProblemSet,
    Question,
    School,
    Standard,
    Subject,
    SubjectRoom,
    Submission,
    User,
    UserRole,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Replay School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=10)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Physics")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Kinematics", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="R", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="teacher_replay", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="student_replay", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def question(db, school, standard, subject, chapter):
    return Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter)


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, question):
    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Replay Practice",
        number=1,
    )
    ps.questions.add(question)
    return ps


@pytest.fixture
def assignment(db, subject_room, problem_set, teacher):
    return Assignment.objects.create(
        subject_room=subject_room,
        problem_set=problem_set,
        assigned_by=teacher,
        due_at=timezone.now() + timedelta(days=7),
    )


@pytest.fixture
def submission(db, assignment, student):
    """An in-progress (not yet submitted) submission, created online on first open."""
    return Submission.objects.create(assignment=assignment, student=student, answers={"1": 1}, completion=0.5)


class TestSubmissionReplaySafety:
    def test_first_submit_grades_exactly_once(self, api_client, student, submission):
        """(a) PATCH submitted_at once → grade_submission queued exactly once."""
        api_client.force_authenticate(user=student)
        url = reverse("submission-detail", kwargs={"pk": submission.pk})
        with patch("openshiksha.apps.core.tasks.grade_submission.delay") as mock_grade:
            response = api_client.patch(url, {"submitted_at": timezone.now().isoformat()}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert mock_grade.call_count == 1
        mock_grade.assert_called_once_with(submission.pk)

    def test_replayed_submit_does_not_regrade(self, api_client, student, submission):
        """(b) A duplicate submit replayed after grading → 200, no second grade, same score."""
        # First submit, then simulate grading having run (score populated).
        submission.submitted_at = timezone.now()
        submission.score = 0.75
        submission.save(update_fields=["submitted_at", "score"])

        api_client.force_authenticate(user=student)
        url = reverse("submission-detail", kwargs={"pk": submission.pk})
        with patch("openshiksha.apps.core.tasks.grade_submission.delay") as mock_grade:
            response = api_client.patch(url, {"submitted_at": timezone.now().isoformat()}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert mock_grade.call_count == 0
        assert response.data["score"] == 0.75
        submission.refresh_from_db()
        assert submission.score == 0.75

    def test_replayed_submit_before_grading_completes_is_noop(self, api_client, student, submission):
        """A submit replayed while the first grade is still pending (score is None) is a no-op.

        Guards against the async double-grade race: the serializer short-circuits
        the save so the signal never re-fires even though score is not yet set.
        """
        submission.submitted_at = timezone.now()
        submission.save(update_fields=["submitted_at"])
        assert submission.score is None

        api_client.force_authenticate(user=student)
        url = reverse("submission-detail", kwargs={"pk": submission.pk})
        with patch("openshiksha.apps.core.tasks.grade_submission.delay") as mock_grade:
            response = api_client.patch(url, {"submitted_at": timezone.now().isoformat()}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert mock_grade.call_count == 0

    def test_stale_autosave_after_submit_is_noop(self, api_client, student, submission):
        """(c) An answers PATCH that lands after submission → 200, answers unchanged, no grade."""
        submission.submitted_at = timezone.now()
        submission.score = 0.6
        submission.answers = {"1": 2}
        submission.save(update_fields=["submitted_at", "score", "answers"])

        api_client.force_authenticate(user=student)
        url = reverse("submission-detail", kwargs={"pk": submission.pk})
        with patch("openshiksha.apps.core.tasks.grade_submission.delay") as mock_grade:
            response = api_client.patch(url, {"answers": {"1": 4}, "completion": 1.0}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert mock_grade.call_count == 0
        submission.refresh_from_db()
        assert submission.answers == {"1": 2}  # immutable post-submit
        assert submission.score == 0.6

    def test_normal_in_progress_autosave_still_works(self, api_client, student, submission):
        """(d) The normal pre-submit auto-save path is unchanged — answers update, no grade."""
        api_client.force_authenticate(user=student)
        url = reverse("submission-detail", kwargs={"pk": submission.pk})
        with patch("openshiksha.apps.core.tasks.grade_submission.delay") as mock_grade:
            response = api_client.patch(url, {"answers": {"1": 3}, "completion": 0.8}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert mock_grade.call_count == 0
        submission.refresh_from_db()
        assert submission.answers == {"1": 3}
        assert submission.completion == 0.8


class TestGradeSignalScoreGate:
    """Direct unit coverage of the signal's MSO-6 ``score is None`` gate."""

    def test_resave_of_graded_submission_does_not_regrade(self, submission):
        submission.submitted_at = timezone.now()
        submission.score = 0.9
        submission.save(update_fields=["submitted_at", "score"])

        with patch("openshiksha.apps.core.tasks.grade_submission.delay") as mock_grade:
            # A full save() (update_fields=None) carrying submitted_at on an
            # already-graded submission must not trigger grading.
            submission.save()
        assert mock_grade.call_count == 0

    def test_first_submit_save_triggers_grade(self, submission):
        with patch("openshiksha.apps.core.tasks.grade_submission.delay") as mock_grade:
            submission.submitted_at = timezone.now()
            submission.save(update_fields=["submitted_at"])
        mock_grade.assert_called_once_with(submission.pk)
