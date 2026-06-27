"""
Tests for the on-scrape business / queue-depth gauges (MET-2).

Seeds a small graph via the ORM, scrapes the gated /metrics endpoint, and asserts
the ``openshiksha_*`` business families reflect the seeded data. The gated-off
(404, no DB hit) path is covered by ``test_metrics_endpoint.py``.
"""

from datetime import timedelta

import pytest

from django.urls import reverse
from django.utils import timezone

from openshiksha.apps.core.models import (
    Assignment,
    Board,
    Chapter,
    ClassRoom,
    ProblemSet,
    School,
    Standard,
    Subject,
    SubjectRoom,
    Submission,
    User,
    UserRole,
)


@pytest.fixture
def seeded(db, settings):
    settings.METRICS_ENABLED = True
    board = Board.objects.create(name="CBSE")
    school = School.objects.create(name="Test School", board=board)
    standard = Standard.objects.create(number=9)
    subject = Subject.objects.create(name="Science")
    chapter = Chapter.objects.create(name="Motion", subject=subject, standard=standard, order=1)
    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")
    teacher = User.objects.create_user(username="t1", password="pw", role=UserRole.TEACHER, school=school)
    s1 = User.objects.create_user(username="s1", password="pw", role=UserRole.STUDENT, school=school)
    s2 = User.objects.create_user(username="s2", password="pw", role=UserRole.STUDENT, school=school)
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    ps = ProblemSet.objects.create(
        school=school, standard=standard, subject=subject, chapter=chapter, title="Set 1", number=1, created_by=teacher
    )

    now = timezone.now()
    active = Assignment.objects.create(
        subject_room=room, problem_set=ps, assigned_by=teacher, due_at=now + timedelta(days=3)
    )
    # A closed assignment — must NOT count toward "active".
    Assignment.objects.create(
        subject_room=room,
        problem_set=ps,
        assigned_by=teacher,
        due_at=now + timedelta(days=3),
        number=2,
        closed_at=now,
    )
    # Create both in-progress (no submitted_at ⇒ the on-submit grade signal does
    # not fire), then force the exact terminal states via .update() — which
    # bypasses post_save — so the pending row stays ungraded deterministically.
    sub_pending = Submission.objects.create(assignment=active, student=s1)
    sub_graded = Submission.objects.create(assignment=active, student=s2)
    # Pending-grading: submitted, no score → grade-queue depth = 1.
    Submission.objects.filter(pk=sub_pending.pk).update(submitted_at=now, score=None)
    # Graded: excluded from the pending count.
    Submission.objects.filter(pk=sub_graded.pk).update(submitted_at=now, score=0.9)
    return {"active": active}


class TestBusinessGauges:
    def _scrape(self, client):
        response = client.get(reverse("metrics"))
        assert response.status_code == 200
        return response.content.decode()

    def test_active_assignments_excludes_closed(self, client, seeded):
        body = self._scrape(client)
        assert "openshiksha_assignments_active 1.0" in body

    def test_grade_queue_depth_excludes_graded(self, client, seeded):
        body = self._scrape(client)
        assert "openshiksha_submissions_pending_grading 1.0" in body

    def test_users_by_role(self, client, seeded):
        body = self._scrape(client)
        assert 'openshiksha_users{role="student"} 2.0' in body
        assert 'openshiksha_users{role="teacher"} 1.0' in body

    def test_classroom_and_subjectroom_totals(self, client, seeded):
        body = self._scrape(client)
        assert "openshiksha_classrooms 1.0" in body
        assert "openshiksha_subjectrooms 1.0" in body

    def test_build_info_still_present(self, client, seeded):
        # Business gauges ride alongside the MET-1 identity gauge.
        assert "openshiksha_build_info" in self._scrape(client)
