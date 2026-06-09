"""
AIV-8: list-versions + version-diff endpoints on ``ProblemSetViewSet``.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from django.utils import timezone
from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Assignment,
    Board,
    Chapter,
    ClassRoom,
    ProblemSet,
    Question,
    QuestionSubpart,
    School,
    Standard,
    Subject,
    SubjectRoom,
    User,
    UserRole,
)
from openshiksha.apps.core.snapshots import build_assignment_snapshot, get_or_create_version_for


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="S", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=9)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Math")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Algebra", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(
        username="t", password="pw", role=UserRole.TEACHER, school=school, first_name="Tara"
    )


@pytest.fixture
def subject_room(db, classroom, subject, teacher):
    return SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, teacher):
    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Set",
        number=1,
        created_by=teacher,
    )
    q = Question.objects.create(school=school, standard=standard, subject=subject, chapter=chapter, created_by=teacher)
    QuestionSubpart.objects.create(
        question=q,
        index=0,
        subpart_type="fill_blank",
        question_text="6*7?",
        correct_answer={"type": "fill_blank", "answer": "42"},
    )
    ps.questions.add(q)
    return ps


@pytest.fixture
def two_versions(db, problem_set, teacher):
    """Mint v1, edit the live set, then mint v2 → two distinct version rows."""
    v1, _ = get_or_create_version_for(problem_set, created_by=teacher)
    sp = problem_set.questions.first().subparts.first()
    sp.correct_answer = {"type": "fill_blank", "answer": "999"}
    sp.save(update_fields=["correct_answer"])
    v2, _ = get_or_create_version_for(problem_set, created_by=teacher)
    return v1, v2


@pytest.fixture
def teacher_api(teacher):
    c = APIClient()
    c.force_authenticate(user=teacher)
    return c


class TestListVersions:
    def test_returns_versions_newest_first(self, teacher_api, problem_set, two_versions):
        v1, v2 = two_versions
        resp = teacher_api.get(f"/api/v1/problem-sets/{problem_set.pk}/versions/")
        assert resp.status_code == 200
        ids = [row["id"] for row in resp.data["versions"]]
        assert ids == [v2.pk, v1.pk]

    def test_each_row_has_summary_fields(self, teacher_api, problem_set, two_versions):
        resp = teacher_api.get(f"/api/v1/problem-sets/{problem_set.pk}/versions/")
        first = resp.data["versions"][0]
        for key in (
            "id",
            "version_number",
            "content_hash",
            "created_at",
            "created_by_name",
            "question_count",
            "assignment_count",
        ):
            assert key in first
        assert first["created_by_name"] == "Tara"

    def test_assignment_count_reflects_pinned_assignments(
        self, teacher_api, problem_set, two_versions, subject_room, teacher
    ):
        v1, _v2 = two_versions
        Assignment.objects.create(
            problem_set=problem_set,
            subject_room=subject_room,
            assigned_by=teacher,
            due_at=timezone.now() + timedelta(days=3),
            problem_set_version=v1,
            assigned_content=build_assignment_snapshot(problem_set),
        )
        resp = teacher_api.get(f"/api/v1/problem-sets/{problem_set.pk}/versions/")
        by_id = {row["id"]: row for row in resp.data["versions"]}
        assert by_id[v1.pk]["assignment_count"] == 1
        # v2 has no pinned assignment.
        v2 = next(row for row in resp.data["versions"] if row["version_number"] == 2)
        assert v2["assignment_count"] == 0


class TestVersionDiff:
    def test_default_against_is_previous_version(self, teacher_api, problem_set, two_versions):
        v1, v2 = two_versions
        resp = teacher_api.get(f"/api/v1/problem-sets/{problem_set.pk}/versions/{v2.pk}/diff/")
        assert resp.status_code == 200
        assert resp.data["target"]["id"] == v2.pk
        assert resp.data["against"]["id"] == v1.pk
        # The change between v1 and v2 was a correct_answer edit ⇒ answer_changes.
        assert len(resp.data["diff"]["answer_changes"]) == 1

    def test_explicit_against_param(self, teacher_api, problem_set, two_versions):
        v1, v2 = two_versions
        resp = teacher_api.get(f"/api/v1/problem-sets/{problem_set.pk}/versions/{v1.pk}/diff/?against={v2.pk}")
        # v1 against v2 — the "before"/"after" roles flip relative to the default call.
        assert resp.data["diff"]["answer_changes"][0]["before"] == {
            "type": "fill_blank",
            "answer": "999",
        }
        assert resp.data["diff"]["answer_changes"][0]["after"] == {
            "type": "fill_blank",
            "answer": "42",
        }

    def test_first_version_against_none_returns_no_diff(self, teacher_api, problem_set, two_versions):
        v1, _v2 = two_versions
        # v1 has no earlier version ⇒ against = None ⇒ diff still includes the
        # whole set as additions (every question is "new" relative to empty).
        resp = teacher_api.get(f"/api/v1/problem-sets/{problem_set.pk}/versions/{v1.pk}/diff/")
        assert resp.data["against"] is None
        # diff_snapshots returns the diff against an empty old ⇒ questions_added
        assert len(resp.data["diff"]["questions_added"]) >= 1

    def test_404_when_target_belongs_to_other_problem_set(
        self, teacher_api, problem_set, two_versions, school, standard, subject, chapter, teacher
    ):
        v1, _v2 = two_versions
        other = ProblemSet.objects.create(
            school=school,
            standard=standard,
            subject=subject,
            chapter=chapter,
            title="Other",
            number=99,
            created_by=teacher,
        )
        resp = teacher_api.get(f"/api/v1/problem-sets/{other.pk}/versions/{v1.pk}/diff/")
        assert resp.status_code == 404
