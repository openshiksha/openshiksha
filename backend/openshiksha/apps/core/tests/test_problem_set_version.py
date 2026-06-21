"""
AIV-7: ``ProblemSetVersion`` immutability + dedup + reader fallback through
``resolve_assignment_content``.
"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from django.utils import timezone
from rest_framework.test import APIRequestFactory

from openshiksha.apps.api.serializers.core import AssignmentSerializer
from openshiksha.apps.core.models import (
    Assignment,
    Board,
    Chapter,
    ClassRoom,
    ProblemSet,
    ProblemSetVersion,
    Question,
    QuestionSubpart,
    School,
    Standard,
    Subject,
    SubjectRoom,
    Submission,
    User,
    UserRole,
)
from openshiksha.apps.core.snapshots import (
    build_assignment_snapshot,
    get_or_create_version_for,
    resolve_assignment_content,
)


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
    return User.objects.create_user(username="t", password="pw", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="s", password="pw", role=UserRole.STUDENT, school=school)


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


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


class TestGetOrCreateVersionFor:
    def test_first_call_mints_v1(self, problem_set, teacher):
        version, created = get_or_create_version_for(problem_set, created_by=teacher)
        assert created is True
        assert version.version_number == 1
        assert version.problem_set_id == problem_set.pk

    def test_second_call_dedups_when_content_unchanged(self, problem_set, teacher):
        v1, _ = get_or_create_version_for(problem_set, created_by=teacher)
        v2, created = get_or_create_version_for(problem_set, created_by=teacher)
        assert created is False
        assert v2.pk == v1.pk
        assert ProblemSetVersion.objects.filter(problem_set=problem_set).count() == 1

    def test_edit_live_then_create_mints_v2(self, problem_set, teacher):
        v1, _ = get_or_create_version_for(problem_set, created_by=teacher)
        # Live edit drifts the snapshot — next call mints a new version.
        sp = problem_set.questions.first().subparts.first()
        sp.correct_answer = {"type": "fill_blank", "answer": "999"}
        sp.save(update_fields=["correct_answer"])
        v2, created = get_or_create_version_for(problem_set, created_by=teacher)
        assert created is True
        assert v2.pk != v1.pk
        assert v2.version_number == 2

    def test_two_problem_sets_with_same_content_do_not_collide(self, db, school, standard, subject, chapter, teacher):
        # unique_together is per-(problem_set, content_hash), so identical content
        # under different sets still produces separate rows. The dedup is per-set.
        ps_a = ProblemSet.objects.create(
            school=school,
            standard=standard,
            subject=subject,
            chapter=chapter,
            title="A",
            number=10,
            created_by=teacher,
        )
        ps_b = ProblemSet.objects.create(
            school=school,
            standard=standard,
            subject=subject,
            chapter=chapter,
            title="B",
            number=11,
            created_by=teacher,
        )
        v_a, _ = get_or_create_version_for(ps_a, created_by=teacher)
        v_b, _ = get_or_create_version_for(ps_b, created_by=teacher)
        assert v_a.pk != v_b.pk
        # Both v1 because version_number is scoped per problem_set.
        assert v_a.version_number == 1
        assert v_b.version_number == 1


class TestAssignmentCapturePinsVersion:
    def test_serializer_create_pins_version_fk(self, problem_set, subject_room, teacher):
        factory = APIRequestFactory()
        request = factory.post("/api/v1/assignments/")
        request.user = teacher

        serializer = AssignmentSerializer(
            data={
                "subject_room": subject_room.pk,
                "problem_set_id": problem_set.pk,
                "due_at": (timezone.now() + timedelta(days=3)).isoformat(),
            },
            context={"request": request},
        )
        assert serializer.is_valid(), serializer.errors
        assignment = serializer.save()
        assert assignment.problem_set_version is not None
        assert assignment.assigned_content is not None  # legacy fallback still populated

    def test_two_assignments_same_content_share_one_version(self, problem_set, subject_room, teacher):
        factory = APIRequestFactory()
        for n in (1, 2):
            request = factory.post("/api/v1/assignments/")
            request.user = teacher
            serializer = AssignmentSerializer(
                data={
                    "subject_room": subject_room.pk,
                    "problem_set_id": problem_set.pk,
                    "due_at": (timezone.now() + timedelta(days=n)).isoformat(),
                    "number": n,
                },
                context={"request": request},
            )
            assert serializer.is_valid(), serializer.errors
            serializer.save()
        version_ids = list(Assignment.objects.values_list("problem_set_version_id", flat=True))
        assert len(version_ids) == 2
        assert version_ids[0] == version_ids[1]  # dedup
        assert ProblemSetVersion.objects.filter(problem_set=problem_set).count() == 1


class TestResolveAssignmentContent:
    def test_prefers_version_fk_over_assigned_content_when_both_set(self, problem_set, subject_room, teacher):
        # Build two distinct snapshots so we can prove which one the resolver chose.
        v1, _ = get_or_create_version_for(problem_set, created_by=teacher)
        legacy = build_assignment_snapshot(problem_set)
        # Mutate the legacy JSONField to a sentinel so a fallback would be visible.
        legacy["questions"][0]["subparts"][0]["question_text"] = "STALE"

        assignment = Assignment.objects.create(
            problem_set=problem_set,
            subject_room=subject_room,
            assigned_by=teacher,
            due_at=timezone.now() + timedelta(days=3),
            assigned_content=legacy,
            problem_set_version=v1,
        )
        resolved = resolve_assignment_content(assignment)
        # Version FK wins.
        assert resolved["questions"][0]["subparts"][0]["question_text"] == "6*7?"

    def test_falls_back_to_assigned_content_when_version_is_null(self, problem_set, subject_room, teacher):
        snapshot = build_assignment_snapshot(problem_set)
        assignment = Assignment.objects.create(
            problem_set=problem_set,
            subject_room=subject_room,
            assigned_by=teacher,
            due_at=timezone.now() + timedelta(days=3),
            assigned_content=snapshot,
            problem_set_version=None,
        )
        assert resolve_assignment_content(assignment) == snapshot


class TestGraderReadsVersion:
    @patch("openshiksha.apps.core.tasks._update_assignment_aggregates")
    @patch("openshiksha.apps.core.tasks.update_proficiency")
    def test_grades_against_version_content_after_live_edit(
        self, mock_prof, mock_agg, db, problem_set, subject_room, teacher, student
    ):
        from openshiksha.apps.core.tasks import grade_submission

        mock_agg.delay = MagicMock()
        mock_prof.delay = MagicMock()

        v1, _ = get_or_create_version_for(problem_set, created_by=teacher)
        assignment = Assignment.objects.create(
            problem_set=problem_set,
            subject_room=subject_room,
            assigned_by=teacher,
            due_at=timezone.now() + timedelta(days=3),
            assigned_content=None,  # FK only — proves grader reads via the version
            problem_set_version=v1,
        )

        # Edit the live answer; the version FK still holds "42".
        sp = problem_set.questions.first().subparts.first()
        sp.correct_answer = {"type": "fill_blank", "answer": "999"}
        sp.save(update_fields=["correct_answer"])

        submission = Submission.objects.create(
            assignment=assignment,
            student=student,
            answers={str(sp.id): "42"},
            submitted_at=timezone.now(),
        )
        result = grade_submission(submission.pk)
        assert result["score"] == pytest.approx(1.0)
