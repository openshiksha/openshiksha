"""
Tests for GET /api/v1/proficiency/history/ — trend snapshot endpoint.

Covers:
- Missing required params → 400
- Student gets their own proficiency history
- Parent gets child's proficiency history (ownership enforced)
- Parent cannot get history for non-child student
- Snapshots written by _recalculate_percentile appear in history
"""

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Board,
    Chapter,
    ClassRoom,
    QuestionTag,
    School,
    Standard,
    Subject,
    SubjectRoom,
    User,
    UserRole,
)
from openshiksha.apps.edge.models import StudentProficiency, StudentProficiencySnapshot


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Test School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=7)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Science")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Light", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="B")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="teacher_hist", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="student_hist", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def other_student(db, school):
    return User.objects.create_user(username="other_hist", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def parent(db, student):
    p = User.objects.create_user(username="parent_hist", password="pass", role=UserRole.PARENT)
    p.children.add(student)
    return p


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def tag(db):
    return QuestionTag.objects.create(name="Reflection", tag_type="concept")


@pytest.fixture
def proficiency(db, student, subject_room, tag):
    return StudentProficiency.objects.create(
        student=student,
        subject_room=subject_room,
        question_tag=tag,
        score=0.6,
        rate=0.65,
        percentile=0.5,
        tick_count=5,
    )


@pytest.fixture
def snapshots(db, student, subject_room, tag):
    """Two snapshots for trend display."""
    snap1 = StudentProficiencySnapshot.objects.create(
        student=student, question_tag=tag, subject_room=subject_room, score=0.4
    )
    snap2 = StudentProficiencySnapshot.objects.create(
        student=student, question_tag=tag, subject_room=subject_room, score=0.6
    )
    return [snap1, snap2]


# ---------------------------------------------------------------------------
# Parameter validation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_history_requires_tag_param(api_client, student, subject_room):
    api_client.force_authenticate(user=student)
    response = api_client.get(f"/api/v1/proficiency/history/?subject_room={subject_room.id}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_history_requires_subject_room_param(api_client, student, tag):
    api_client.force_authenticate(user=student)
    response = api_client.get(f"/api/v1/proficiency/history/?tag={tag.id}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Student: own history
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_student_gets_own_history(api_client, student, subject_room, tag, snapshots):
    api_client.force_authenticate(user=student)
    response = api_client.get(f"/api/v1/proficiency/history/?tag={tag.id}&subject_room={subject_room.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    scores = [s["score"] for s in data]
    assert 0.4 in scores
    assert 0.6 in scores


@pytest.mark.django_db
def test_student_gets_empty_list_when_no_snapshots(api_client, student, subject_room, tag):
    api_client.force_authenticate(user=student)
    response = api_client.get(f"/api/v1/proficiency/history/?tag={tag.id}&subject_room={subject_room.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


# ---------------------------------------------------------------------------
# Parent: child history with ownership
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_parent_gets_child_history(api_client, parent, student, subject_room, tag, snapshots):
    api_client.force_authenticate(user=parent)
    url = f"/api/v1/proficiency/history/?tag={tag.id}&subject_room={subject_room.id}&student={student.id}"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


@pytest.mark.django_db
def test_parent_cannot_get_non_child_history(api_client, parent, other_student, subject_room, tag, db):
    # Create snapshots for other_student
    StudentProficiencySnapshot.objects.create(
        student=other_student, question_tag=tag, subject_room=subject_room, score=0.8
    )
    api_client.force_authenticate(user=parent)
    url = f"/api/v1/proficiency/history/?tag={tag.id}&subject_room={subject_room.id}&student={other_student.id}"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.django_db
def test_parent_without_student_param_gets_empty(api_client, parent, subject_room, tag, snapshots):
    api_client.force_authenticate(user=parent)
    response = api_client.get(f"/api/v1/proficiency/history/?tag={tag.id}&subject_room={subject_room.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


# ---------------------------------------------------------------------------
# Snapshot auto-creation via _recalculate_percentile
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_recalculate_percentile_creates_snapshots(student, subject_room, tag, proficiency):
    """_recalculate_percentile writes a StudentProficiencySnapshot for each student."""
    from openshiksha.apps.core.tasks import _recalculate_percentile

    initial_count = StudentProficiencySnapshot.objects.filter(
        student=student, question_tag=tag, subject_room=subject_room
    ).count()

    _recalculate_percentile(subject_room.id, tag.id)

    final_count = StudentProficiencySnapshot.objects.filter(
        student=student, question_tag=tag, subject_room=subject_room
    ).count()
    assert final_count == initial_count + 1

    snap = StudentProficiencySnapshot.objects.filter(
        student=student, question_tag=tag, subject_room=subject_room
    ).latest("recorded_at")
    # Score after recalculation: (0.7 * rate) + (0.3 * percentile) — single student gets percentile=0
    assert snap.score == pytest.approx(0.7 * proficiency.rate, abs=0.01)
