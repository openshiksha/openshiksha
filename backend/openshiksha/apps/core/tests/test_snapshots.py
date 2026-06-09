"""
AIV-1: tests for ``Assignment.assigned_content`` snapshot.

Covers: snapshot helper shape, capture in the regular AssignmentSerializer
creation path, capture in the remedial-creation path, and the byte-identical
invariant — editing the live ProblemSet / Question / Subpart after assign time
must NOT change the frozen snapshot.
"""

from __future__ import annotations

import copy
from datetime import timedelta

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
    Question,
    QuestionSubpart,
    School,
    Standard,
    Subject,
    SubjectRoom,
    User,
    UserRole,
)
from openshiksha.apps.core.snapshots import SNAPSHOT_SCHEMA_VERSION, build_assignment_snapshot


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Test School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=9)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Science")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Motion", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="t1", password="pw", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="s1", password="pw", role=UserRole.STUDENT, school=school)


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def question_with_subparts(db, school, standard, subject, chapter, teacher):
    question = Question.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        created_by=teacher,
        difficulty=3,
        stem_text="Shared stem",
    )
    QuestionSubpart.objects.create(
        question=question,
        index=0,
        subpart_type="mcq",
        question_text="What is 2+2?",
        options=[{"key": "A", "text": "3"}, {"key": "B", "text": "4"}],
        correct_answer={"type": "mcq", "answer": "B"},
    )
    QuestionSubpart.objects.create(
        question=question,
        index=1,
        subpart_type="numeric",
        question_text="Compute {{a}}*2",
        correct_answer={"type": "numeric", "answer": "{{a}}*2"},
        variable_constraints={"a": {"min": 1, "max": 9, "integer": True}},
    )
    return question


@pytest.fixture
def problem_set(db, school, standard, subject, chapter, question_with_subparts, teacher):
    ps = ProblemSet.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        title="Set 1",
        number=1,
        created_by=teacher,
    )
    ps.questions.add(question_with_subparts)
    return ps


class TestBuildSnapshot:
    def test_shape_and_fields(self, problem_set, question_with_subparts):
        snap = build_assignment_snapshot(problem_set)
        assert snap["schema_version"] == SNAPSHOT_SCHEMA_VERSION
        assert snap["problem_set_id"] == problem_set.pk
        assert snap["problem_set_title"] == "Set 1"
        assert "captured_at" in snap
        assert len(snap["questions"]) == 1

        q = snap["questions"][0]
        assert q["question_id"] == question_with_subparts.pk
        assert q["stem_text"] == "Shared stem"
        assert q["difficulty"] == 3
        assert len(q["subparts"]) == 2

        sp0 = q["subparts"][0]
        assert sp0["subpart_type"] == "mcq"
        assert sp0["correct_answer"] == {"type": "mcq", "answer": "B"}
        assert sp0["options"] == [{"key": "A", "text": "3"}, {"key": "B", "text": "4"}]

        sp1 = q["subparts"][1]
        assert sp1["subpart_type"] == "numeric"
        assert sp1["variable_constraints"] == {"a": {"min": 1, "max": 9, "integer": True}}

    def test_empty_problem_set(self, db, school, standard, subject, chapter):
        ps = ProblemSet.objects.create(
            school=school, standard=standard, subject=subject, chapter=chapter, title="Empty", number=7
        )
        snap = build_assignment_snapshot(ps)
        assert snap["questions"] == []


class TestAssignmentCapture:
    def test_serializer_create_captures_snapshot(self, problem_set, subject_room, teacher):
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

        assert assignment.assigned_content is not None
        assert assignment.assigned_content["problem_set_id"] == problem_set.pk
        assert len(assignment.assigned_content["questions"]) == 1
        assert assignment.assigned_content["questions"][0]["subparts"][0]["correct_answer"] == {
            "type": "mcq",
            "answer": "B",
        }

    def test_snapshot_byte_identical_after_live_edit(self, problem_set, subject_room, teacher, question_with_subparts):
        assignment = Assignment.objects.create(
            subject_room=subject_room,
            problem_set=problem_set,
            assigned_by=teacher,
            due_at=timezone.now() + timedelta(days=3),
            assigned_content=build_assignment_snapshot(problem_set),
        )
        original = copy.deepcopy(assignment.assigned_content)

        # Mutate everything we can on the live set/question/subpart.
        sp0 = question_with_subparts.subparts.get(index=0)
        sp0.question_text = "Edited prompt"
        sp0.correct_answer = {"type": "mcq", "answer": "A"}
        sp0.options = [{"key": "A", "text": "changed"}, {"key": "B", "text": "changed"}]
        sp0.save()

        question_with_subparts.stem_text = "Edited stem"
        question_with_subparts.save()

        problem_set.title = "Renamed set"
        problem_set.save()
        problem_set.questions.clear()  # remove the question from the live set

        assignment.refresh_from_db()
        assert assignment.assigned_content == original


class TestRemedialCapture:
    def test_remedial_assignment_has_snapshot(
        self, problem_set, subject_room, teacher, student, question_with_subparts
    ):
        # Set up a fully-graded submission below REMEDIAL_THRESHOLD to trigger
        # _create_remedial_assignment without going through the celery task.
        from openshiksha.apps.core.models import Submission
        from openshiksha.apps.core.tasks import _create_remedial_assignment
        from openshiksha.apps.edge.models import Tick

        assignment = Assignment.objects.create(
            subject_room=subject_room,
            problem_set=problem_set,
            assigned_by=teacher,
            due_at=timezone.now() + timedelta(days=3),
            assigned_content=build_assignment_snapshot(problem_set),
        )
        submission = Submission.objects.create(
            assignment=assignment,
            student=student,
            score=0.0,
            completion=1.0,
            submitted_at=timezone.now(),
        )
        # One wrong tick on the question so the remedial has something to copy.
        sp = question_with_subparts.subparts.first()
        Tick.objects.create(
            student=student,
            question_subpart=sp,
            submission=submission,
            subject_room=subject_room,
            mark=0.0,
        )

        _create_remedial_assignment(submission.pk)

        remedial = Assignment.objects.exclude(pk=assignment.pk).get()
        assert remedial.assigned_content is not None
        assert remedial.assigned_content["schema_version"] == SNAPSHOT_SCHEMA_VERSION
        assert len(remedial.assigned_content["questions"]) >= 1
