"""
Tests for the Class Misconception Insights feature.

Covers:
- analytics.cluster_misconceptions_for_subject_room: empty, grouping by normalised
  label, drops singleton students, ignores misconceptions outside the lookback window
  and outside the room's roster.
- analytics._normalise_misconception_label: case/whitespace/trailing-punctuation folding.
- tasks.refresh_class_misconception_clusters: writes rows, idempotent (delete+create),
  honours custom lookback_days.
- API: list / retrieve / refresh with teacher-only permissions, room-ownership scoping.
"""

from datetime import timedelta

import pytest

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

_user_counter = 0


def make_user(db, role="student", username=None, grade=8):
    global _user_counter
    from openshiksha.apps.core.models import User

    _user_counter += 1
    username = username or f"mc_user_{role}_{_user_counter}"
    u = User.objects.create_user(username=username, password="pass", role=role)
    u.grade = grade
    u.save()
    return u


def make_question_subpart(db, standard, subject, chapter_name="Algebra"):
    from openshiksha.apps.core.models import Chapter, Question, QuestionSubpart, QuestionType

    chapter = Chapter.objects.get_or_create(name=chapter_name, subject=subject, standard=standard)[0]
    question = Question.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.MCQ,
        difficulty=2,
    )
    return QuestionSubpart.objects.create(
        question=question,
        index=0,
        question_text="x + 2 = 5",
        options=[{"key": "A", "text": "1"}, {"key": "B", "text": "3"}],
        correct_answer={"type": "mcq", "answer": "B"},
    )


def make_misconception(db, student, subpart, label, *, detected_offset_days=0, diagnosis="diag.", tip="tip."):
    from openshiksha.apps.ai.models import StudentMisconception

    m = StudentMisconception.objects.create(
        student=student,
        question_subpart=subpart,
        student_answer={"answer": "A"},
        misconception_label=label,
        diagnosis_text=diagnosis,
        remediation_tip=tip,
        grade_level=8,
    )
    if detected_offset_days:
        StudentMisconception.objects.filter(pk=m.pk).update(
            detected_at=timezone.now() - timedelta(days=detected_offset_days)
        )
        m.refresh_from_db()
    return m


@pytest.fixture
def setup(db):
    from openshiksha.apps.core.models import Board, ClassRoom, School, Standard, Subject, SubjectRoom

    board = Board.objects.get_or_create(name="CBSE")[0]
    school = School.objects.get_or_create(name="MC Test School", board=board)[0]
    standard = Standard.objects.get_or_create(number=8)[0]
    subject = Subject.objects.get_or_create(name="Mathematics")[0]
    teacher = make_user(db, role="teacher", username="mc_teacher")
    other_teacher = make_user(db, role="teacher", username="mc_other_teacher")
    s1 = make_user(db, role="student", username="mc_s1")
    s2 = make_user(db, role="student", username="mc_s2")
    s3 = make_user(db, role="student", username="mc_s3")
    outsider = make_user(db, role="student", username="mc_outsider")
    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")
    for s in (s1, s2, s3):
        classroom.students.add(s)
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    for s in (s1, s2, s3):
        room.students.add(s)

    other_classroom = ClassRoom.objects.create(school=school, standard=standard, division="B", academic_year="2025-26")
    other_room = SubjectRoom.objects.create(classroom=other_classroom, subject=subject, teacher=other_teacher)

    subpart = make_question_subpart(db, standard, subject)

    return {
        "standard": standard,
        "subject": subject,
        "teacher": teacher,
        "other_teacher": other_teacher,
        "students": [s1, s2, s3],
        "outsider": outsider,
        "subject_room": room,
        "other_subject_room": other_room,
        "subpart": subpart,
    }


# ─────────────────────────────────────────────────────────────
# Label normalisation
# ─────────────────────────────────────────────────────────────


def test_normalise_misconception_label_lowercases_and_strips():
    from openshiksha.apps.ai.analytics import _normalise_misconception_label

    assert _normalise_misconception_label("Sign error on subtraction.") == "sign error on subtraction"
    assert _normalise_misconception_label("  Sign Error  on   Subtraction  ") == "sign error on subtraction"
    assert _normalise_misconception_label("") == ""


# ─────────────────────────────────────────────────────────────
# Clustering
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_cluster_empty_room_returns_no_clusters(setup):
    from openshiksha.apps.ai.analytics import cluster_misconceptions_for_subject_room

    clusters, window_start = cluster_misconceptions_for_subject_room(setup["subject_room"])
    assert clusters == []
    assert window_start <= timezone.now()


@pytest.mark.django_db
def test_cluster_groups_by_normalised_label(setup):
    from openshiksha.apps.ai.analytics import cluster_misconceptions_for_subject_room

    s1, s2, s3 = setup["students"]
    # Same misconception, varied formatting — should fold to one cluster of 3.
    make_misconception(setup, s1, setup["subpart"], "Sign error on subtraction.")
    make_misconception(setup, s2, setup["subpart"], "sign error on subtraction")
    make_misconception(setup, s3, setup["subpart"], "Sign Error on Subtraction")

    clusters, _ = cluster_misconceptions_for_subject_room(setup["subject_room"])
    assert len(clusters) == 1
    c = clusters[0]
    assert c["misconception_label"] == "sign error on subtraction"
    assert c["student_count"] == 3
    assert c["occurrence_count"] == 3


@pytest.mark.django_db
def test_cluster_drops_singletons(setup):
    """A misconception held by only one student isn't a class-level signal."""
    from openshiksha.apps.ai.analytics import cluster_misconceptions_for_subject_room

    s1, s2, _ = setup["students"]
    make_misconception(setup, s1, setup["subpart"], "Lonely misconception")
    make_misconception(setup, s2, setup["subpart"], "Shared misconception")
    # Second student shares a misconception with no one — singleton, drop.
    # First student also has their own — singleton, drop.
    clusters, _ = cluster_misconceptions_for_subject_room(setup["subject_room"])
    assert clusters == []


@pytest.mark.django_db
def test_cluster_excludes_misconceptions_outside_lookback(setup):
    from openshiksha.apps.ai.analytics import cluster_misconceptions_for_subject_room

    s1, s2, _ = setup["students"]
    make_misconception(setup, s1, setup["subpart"], "Old issue", detected_offset_days=60)
    make_misconception(setup, s2, setup["subpart"], "Old issue", detected_offset_days=60)
    # Inside the default 30-day window — no rows match
    clusters, _ = cluster_misconceptions_for_subject_room(setup["subject_room"], lookback_days=30)
    assert clusters == []
    # Widen the window, the cluster reappears
    clusters, _ = cluster_misconceptions_for_subject_room(setup["subject_room"], lookback_days=90)
    assert len(clusters) == 1
    assert clusters[0]["student_count"] == 2


@pytest.mark.django_db
def test_cluster_ignores_students_outside_room(setup):
    from openshiksha.apps.ai.analytics import cluster_misconceptions_for_subject_room

    s1 = setup["students"][0]
    outsider = setup["outsider"]
    make_misconception(setup, s1, setup["subpart"], "Shared error")
    make_misconception(setup, outsider, setup["subpart"], "Shared error")

    # Only one in-room student — drop as singleton
    clusters, _ = cluster_misconceptions_for_subject_room(setup["subject_room"])
    assert clusters == []


@pytest.mark.django_db
def test_cluster_sorted_by_student_count_desc(setup):
    from openshiksha.apps.ai.analytics import cluster_misconceptions_for_subject_room

    s1, s2, s3 = setup["students"]
    # Cluster A: 3 students
    make_misconception(setup, s1, setup["subpart"], "Big shared error")
    make_misconception(setup, s2, setup["subpart"], "Big shared error")
    make_misconception(setup, s3, setup["subpart"], "Big shared error")
    # Cluster B: 2 students
    make_misconception(setup, s1, setup["subpart"], "Small shared error")
    make_misconception(setup, s2, setup["subpart"], "Small shared error")

    clusters, _ = cluster_misconceptions_for_subject_room(setup["subject_room"])
    assert [c["student_count"] for c in clusters] == [3, 2]
    assert clusters[0]["misconception_label"] == "big shared error"


# ─────────────────────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_refresh_task_writes_rows(setup):
    from openshiksha.apps.ai.models import ClassMisconceptionCluster
    from openshiksha.apps.ai.tasks import refresh_class_misconception_clusters

    s1, s2, _ = setup["students"]
    make_misconception(setup, s1, setup["subpart"], "Shared issue", diagnosis="They mis-applied X.", tip="Review X.")
    make_misconception(setup, s2, setup["subpart"], "Shared issue", diagnosis="ignored", tip="ignored")

    result = refresh_class_misconception_clusters(setup["subject_room"].pk)
    assert result["created"] == 1
    assert result["deleted"] == 0

    rows = list(ClassMisconceptionCluster.objects.filter(subject_room=setup["subject_room"]))
    assert len(rows) == 1
    assert rows[0].student_count == 2
    assert rows[0].misconception_label == "shared issue"
    assert rows[0].sample_diagnosis  # populated from the newest underlying record
    assert rows[0].sample_remediation_tip


@pytest.mark.django_db
def test_refresh_task_is_idempotent_and_replaces_rows(setup):
    from openshiksha.apps.ai.models import ClassMisconceptionCluster
    from openshiksha.apps.ai.tasks import refresh_class_misconception_clusters

    s1, s2, _ = setup["students"]
    m_a = make_misconception(setup, s1, setup["subpart"], "Stale issue")
    m_b = make_misconception(setup, s2, setup["subpart"], "Stale issue")

    refresh_class_misconception_clusters(setup["subject_room"].pk)
    assert ClassMisconceptionCluster.objects.filter(subject_room=setup["subject_room"]).count() == 1

    # Aging the underlying rows out of the window must cause the cluster to vanish.
    from openshiksha.apps.ai.models import StudentMisconception

    StudentMisconception.objects.filter(pk__in=[m_a.pk, m_b.pk]).update(
        detected_at=timezone.now() - timedelta(days=120)
    )
    result = refresh_class_misconception_clusters(setup["subject_room"].pk)
    assert result["created"] == 0
    assert result["deleted"] == 1
    assert ClassMisconceptionCluster.objects.filter(subject_room=setup["subject_room"]).count() == 0


@pytest.mark.django_db
def test_refresh_task_honours_custom_lookback(setup):
    from openshiksha.apps.ai.models import ClassMisconceptionCluster
    from openshiksha.apps.ai.tasks import refresh_class_misconception_clusters

    s1, s2, _ = setup["students"]
    make_misconception(setup, s1, setup["subpart"], "Old issue", detected_offset_days=60)
    make_misconception(setup, s2, setup["subpart"], "Old issue", detected_offset_days=60)

    refresh_class_misconception_clusters(setup["subject_room"].pk, lookback_days=30)
    assert ClassMisconceptionCluster.objects.filter(subject_room=setup["subject_room"]).count() == 0

    refresh_class_misconception_clusters(setup["subject_room"].pk, lookback_days=90)
    assert ClassMisconceptionCluster.objects.filter(subject_room=setup["subject_room"]).count() == 1


# ─────────────────────────────────────────────────────────────
# API
# ─────────────────────────────────────────────────────────────


def _auth(client, user):
    client.force_authenticate(user=user)


@pytest.mark.django_db
def test_api_list_requires_teacher_role(setup):
    client = APIClient()
    _auth(client, setup["students"][0])
    resp = client.get(reverse("misconception-cluster-list"))
    # Students get empty list, not 403, because viewset returns empty queryset
    assert resp.status_code == 200
    assert resp.json()["results"] == []


@pytest.mark.django_db
def test_api_list_scopes_to_teacher_rooms(setup):
    from openshiksha.apps.ai.models import ClassMisconceptionCluster

    # Teacher's room cluster
    ClassMisconceptionCluster.objects.create(
        subject_room=setup["subject_room"],
        misconception_label="mine",
        student_count=2,
        occurrence_count=2,
        window_start=timezone.now() - timedelta(days=30),
        last_seen=timezone.now(),
    )
    # Other teacher's room cluster
    ClassMisconceptionCluster.objects.create(
        subject_room=setup["other_subject_room"],
        misconception_label="theirs",
        student_count=2,
        occurrence_count=2,
        window_start=timezone.now() - timedelta(days=30),
        last_seen=timezone.now(),
    )

    client = APIClient()
    _auth(client, setup["teacher"])
    resp = client.get(reverse("misconception-cluster-list"))
    assert resp.status_code == 200
    labels = [r["misconception_label"] for r in resp.json()["results"]]
    assert labels == ["mine"]


@pytest.mark.django_db
def test_api_refresh_queues_task_for_owned_room(setup):
    from unittest.mock import patch

    client = APIClient()
    _auth(client, setup["teacher"])
    with patch("openshiksha.apps.ai.views.refresh_class_misconception_clusters.delay") as mock_delay:
        resp = client.post(
            reverse("misconception-cluster-refresh"),
            {"subject_room_id": setup["subject_room"].pk},
            format="json",
        )
    assert resp.status_code == 202
    mock_delay.assert_called_once_with(setup["subject_room"].pk, None)


@pytest.mark.django_db
def test_api_refresh_rejects_non_owned_room(setup):
    client = APIClient()
    _auth(client, setup["teacher"])
    resp = client.post(
        reverse("misconception-cluster-refresh"),
        {"subject_room_id": setup["other_subject_room"].pk},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_refresh_rejects_students(setup):
    client = APIClient()
    _auth(client, setup["students"][0])
    resp = client.post(
        reverse("misconception-cluster-refresh"),
        {"subject_room_id": setup["subject_room"].pk},
        format="json",
    )
    assert resp.status_code == 403
