"""
Tests for the Empirical Question Difficulty Calibration feature.

Covers:
- analytics.facility_to_difficulty: band edges.
- analytics.calibrate_subparts_for_subject_room: empty room, facility/empirical
  difficulty, discrimination index, min-sample drop, and each quality flag
  (TOO_EASY, TOO_HARD, MISLABELED, LOW_DISCRIMINATION, OK).
- tasks.refresh_difficulty_calibrations: writes rows, snapshot replace (idempotent).
- API: list / summary / refresh with teacher-only permissions and room scoping.
"""

import pytest

from django.urls import reverse
from rest_framework.test import APIClient

# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

_user_counter = 0


def make_user(db, role="student", username=None, grade=8):
    global _user_counter
    from openshiksha.apps.core.models import User

    _user_counter += 1
    username = username or f"cal_user_{role}_{_user_counter}"
    u = User.objects.create_user(username=username, password="pass", role=role)
    u.grade = grade
    u.save()
    return u


def make_subpart(db, standard, subject, *, difficulty=2, chapter_name="Algebra", text="x + 2 = 5"):
    from openshiksha.apps.core.models import Chapter, Question, QuestionSubpart, QuestionType

    chapter = Chapter.objects.get_or_create(name=chapter_name, subject=subject, standard=standard)[0]
    question = Question.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.MCQ,
        difficulty=difficulty,
    )
    return QuestionSubpart.objects.create(
        question=question,
        index=0,
        question_text=text,
        options=[{"key": "A", "text": "1"}, {"key": "B", "text": "3"}],
        correct_answer={"type": "mcq", "answer": "B"},
    )


def make_tick(db, student, subpart, room, mark):
    from openshiksha.apps.edge.models import Tick

    return Tick.objects.create(
        student=student,
        question_subpart=subpart,
        subject_room=room,
        mark=mark,
    )


@pytest.fixture
def setup(db):
    from openshiksha.apps.core.models import Board, ClassRoom, School, Standard, Subject, SubjectRoom

    board = Board.objects.get_or_create(name="CBSE")[0]
    school = School.objects.get_or_create(name="Cal Test School", board=board)[0]
    standard = Standard.objects.get_or_create(number=8)[0]
    subject = Subject.objects.get_or_create(name="Mathematics")[0]
    teacher = make_user(db, role="teacher", username="cal_teacher")
    other_teacher = make_user(db, role="teacher", username="cal_other_teacher")

    students = [make_user(db, role="student", username=f"cal_s{i}") for i in range(8)]
    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")
    for s in students:
        classroom.students.add(s)
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    for s in students:
        room.students.add(s)

    other_classroom = ClassRoom.objects.create(school=school, standard=standard, division="B", academic_year="2025-26")
    other_room = SubjectRoom.objects.create(classroom=other_classroom, subject=subject, teacher=other_teacher)

    return {
        "standard": standard,
        "subject": subject,
        "teacher": teacher,
        "other_teacher": other_teacher,
        "students": students,
        "subject_room": room,
        "other_subject_room": other_room,
    }


# ─────────────────────────────────────────────────────────────
# facility_to_difficulty
# ─────────────────────────────────────────────────────────────


def test_facility_to_difficulty_bands():
    from openshiksha.apps.ai.analytics import facility_to_difficulty

    assert facility_to_difficulty(1.0) == 1
    assert facility_to_difficulty(0.85) == 1
    assert facility_to_difficulty(0.84) == 2
    assert facility_to_difficulty(0.70) == 2
    assert facility_to_difficulty(0.55) == 3
    assert facility_to_difficulty(0.40) == 4
    assert facility_to_difficulty(0.10) == 5
    assert facility_to_difficulty(0.0) == 5


# ─────────────────────────────────────────────────────────────
# calibrate_subparts_for_subject_room
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_calibration_empty_room(setup):
    from openshiksha.apps.ai.analytics import calibrate_subparts_for_subject_room

    assert calibrate_subparts_for_subject_room(setup["subject_room"]) == []


@pytest.mark.django_db
def test_calibration_drops_below_min_students(setup):
    """Fewer than CALIBRATION_MIN_STUDENTS distinct students → no calibration."""
    from openshiksha.apps.ai.analytics import calibrate_subparts_for_subject_room

    subpart = make_subpart(setup, setup["standard"], setup["subject"])
    # Only 4 students attempt — below the threshold of 5.
    for s in setup["students"][:4]:
        make_tick(setup, s, subpart, setup["subject_room"], 1.0)

    assert calibrate_subparts_for_subject_room(setup["subject_room"]) == []


@pytest.mark.django_db
def test_calibration_facility_and_empirical_difficulty(setup):
    from openshiksha.apps.ai.analytics import calibrate_subparts_for_subject_room

    subpart = make_subpart(setup, setup["standard"], setup["subject"], difficulty=3)
    # 8 students: 4 correct, 4 wrong → facility 0.5 → empirical difficulty 3.
    for i, s in enumerate(setup["students"]):
        make_tick(setup, s, subpart, setup["subject_room"], 1.0 if i < 4 else 0.0)

    results = calibrate_subparts_for_subject_room(setup["subject_room"])
    assert len(results) == 1
    r = results[0]
    assert r["facility_index"] == pytest.approx(0.5)
    assert r["empirical_difficulty"] == 3
    assert r["declared_difficulty"] == 3
    assert r["sample_size"] == 8
    assert r["attempt_count"] == 8
    assert r["flag"] == "ok"


@pytest.mark.django_db
def test_calibration_averages_multiple_attempts_per_student(setup):
    """A student answering twice contributes their mean, not two votes."""
    from openshiksha.apps.ai.analytics import calibrate_subparts_for_subject_room

    subpart = make_subpart(setup, setup["standard"], setup["subject"])
    # 5 students, all correct once. One of them also attempts again and fails.
    for s in setup["students"][:5]:
        make_tick(setup, s, subpart, setup["subject_room"], 1.0)
    make_tick(setup, setup["students"][0], subpart, setup["subject_room"], 0.0)

    results = calibrate_subparts_for_subject_room(setup["subject_room"])
    r = results[0]
    assert r["sample_size"] == 5
    assert r["attempt_count"] == 6
    # student0 mean = 0.5, others = 1.0 → facility = (0.5 + 4) / 5 = 0.9
    assert r["facility_index"] == pytest.approx(0.9)


@pytest.mark.django_db
def test_calibration_flag_too_easy(setup):
    from openshiksha.apps.ai.analytics import calibrate_subparts_for_subject_room

    subpart = make_subpart(setup, setup["standard"], setup["subject"], difficulty=1)
    for s in setup["students"]:
        make_tick(setup, s, subpart, setup["subject_room"], 1.0)

    r = calibrate_subparts_for_subject_room(setup["subject_room"])[0]
    assert r["facility_index"] == pytest.approx(1.0)
    assert r["flag"] == "too_easy"


@pytest.mark.django_db
def test_calibration_flag_too_hard(setup):
    from openshiksha.apps.ai.analytics import calibrate_subparts_for_subject_room

    subpart = make_subpart(setup, setup["standard"], setup["subject"], difficulty=5)
    for s in setup["students"]:
        make_tick(setup, s, subpart, setup["subject_room"], 0.0)

    r = calibrate_subparts_for_subject_room(setup["subject_room"])[0]
    assert r["facility_index"] == pytest.approx(0.0)
    assert r["flag"] == "too_hard"


@pytest.mark.django_db
def test_calibration_flag_mislabeled(setup):
    """Authored as easy (1) but behaves hard (4) → MISLABELED."""
    from openshiksha.apps.ai.analytics import calibrate_subparts_for_subject_room

    subpart = make_subpart(setup, setup["standard"], setup["subject"], difficulty=1)
    # facility ~0.375 → empirical 4; delta = 3 ≥ 2. Vary marks so discrimination is healthy.
    marks = [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    for s, m in zip(setup["students"], marks):
        make_tick(setup, s, subpart, setup["subject_room"], m)

    r = calibrate_subparts_for_subject_room(setup["subject_room"])[0]
    assert r["empirical_difficulty"] == 4
    assert r["declared_difficulty"] == 1
    assert r["empirical_difficulty"] - r["declared_difficulty"] == 3
    assert r["flag"] == "mislabeled"


@pytest.mark.django_db
def test_calibration_discrimination_and_low_discrimination_flag(setup):
    """Weak students outperform strong ones on this item → negative discrimination."""
    from openshiksha.apps.ai.analytics import calibrate_subparts_for_subject_room

    students = setup["students"]
    room = setup["subject_room"]
    # Two anchor items establish a clear ability ordering (first 4 strong, last 4
    # weak) that survives even after the target item inverts it.
    anchor_a = make_subpart(setup, setup["standard"], setup["subject"], chapter_name="AnchorA")
    anchor_b = make_subpart(setup, setup["standard"], setup["subject"], chapter_name="AnchorB")
    target = make_subpart(setup, setup["standard"], setup["subject"], difficulty=3, chapter_name="Target")

    for i, s in enumerate(students):
        strong = i < 4
        make_tick(setup, s, anchor_a, room, 1.0 if strong else 0.0)
        make_tick(setup, s, anchor_b, room, 1.0 if strong else 0.0)
        # On the target, invert: strong students fail, weak students pass (mis-keyed signal).
        make_tick(setup, s, target, room, 0.0 if strong else 1.0)

    results = {r["question_subpart_id"]: r for r in calibrate_subparts_for_subject_room(room)}
    tr = results[target.pk]
    assert tr["discrimination_index"] is not None
    assert tr["discrimination_index"] < 0
    assert tr["flag"] == "low_discrimination"


@pytest.mark.django_db
def test_calibration_discrimination_null_below_threshold(setup):
    """With < DISCRIMINATION_MIN_STUDENTS students, discrimination is left null."""
    from openshiksha.apps.ai.analytics import calibrate_subparts_for_subject_room

    subpart = make_subpart(setup, setup["standard"], setup["subject"], difficulty=3)
    # Exactly 5 students (meets calibration min, below discrimination min of 6).
    marks = [1.0, 1.0, 0.0, 1.0, 0.0]
    for s, m in zip(setup["students"][:5], marks):
        make_tick(setup, s, subpart, setup["subject_room"], m)

    r = calibrate_subparts_for_subject_room(setup["subject_room"])[0]
    assert r["discrimination_index"] is None
    # No low-discrimination flag possible without a discrimination value.
    assert r["flag"] in {"ok", "mislabeled", "too_easy", "too_hard"}


# ─────────────────────────────────────────────────────────────
# Task
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_refresh_task_writes_rows(setup):
    from openshiksha.apps.ai.models import QuestionDifficultyCalibration
    from openshiksha.apps.ai.tasks import refresh_difficulty_calibrations

    subpart = make_subpart(setup, setup["standard"], setup["subject"])
    for i, s in enumerate(setup["students"]):
        make_tick(setup, s, subpart, setup["subject_room"], 1.0 if i < 4 else 0.0)

    result = refresh_difficulty_calibrations(setup["subject_room"].pk)
    assert result["created"] == 1
    assert result["deleted"] == 0
    assert QuestionDifficultyCalibration.objects.filter(subject_room=setup["subject_room"]).count() == 1


@pytest.mark.django_db
def test_refresh_task_snapshot_replaces(setup):
    from openshiksha.apps.ai.models import QuestionDifficultyCalibration
    from openshiksha.apps.ai.tasks import refresh_difficulty_calibrations

    subpart = make_subpart(setup, setup["standard"], setup["subject"])
    for i, s in enumerate(setup["students"]):
        make_tick(setup, s, subpart, setup["subject_room"], 1.0 if i < 4 else 0.0)

    refresh_difficulty_calibrations(setup["subject_room"].pk)
    # Second run replaces the prior row, not appends.
    result = refresh_difficulty_calibrations(setup["subject_room"].pk)
    assert result["created"] == 1
    assert result["deleted"] == 1
    assert QuestionDifficultyCalibration.objects.filter(subject_room=setup["subject_room"]).count() == 1


# ─────────────────────────────────────────────────────────────
# API
# ─────────────────────────────────────────────────────────────


def _auth(client, user):
    client.force_authenticate(user=user)


def _calibration(setup, room, *, difficulty=2, flag="ok", facility=0.5):
    from openshiksha.apps.ai.models import QuestionDifficultyCalibration

    subpart = make_subpart(setup, setup["standard"], setup["subject"], difficulty=difficulty)
    return QuestionDifficultyCalibration.objects.create(
        subject_room=room,
        question_subpart=subpart,
        sample_size=8,
        attempt_count=8,
        facility_index=facility,
        discrimination_index=0.4,
        empirical_difficulty=3,
        declared_difficulty=difficulty,
        flag=flag,
    )


@pytest.mark.django_db
def test_api_list_students_get_empty(setup):
    client = APIClient()
    _auth(client, setup["students"][0])
    resp = client.get(reverse("difficulty-calibration-list"))
    assert resp.status_code == 200
    assert resp.json()["results"] == []


@pytest.mark.django_db
def test_api_list_scopes_to_teacher_rooms(setup):
    _calibration(setup, setup["subject_room"], flag="mislabeled")
    _calibration(setup, setup["other_subject_room"], flag="too_hard")

    client = APIClient()
    _auth(client, setup["teacher"])
    resp = client.get(reverse("difficulty-calibration-list"))
    assert resp.status_code == 200
    flags = [r["flag"] for r in resp.json()["results"]]
    assert flags == ["mislabeled"]


@pytest.mark.django_db
def test_api_list_filters_by_needs_review(setup):
    _calibration(setup, setup["subject_room"], flag="ok")
    _calibration(setup, setup["subject_room"], flag="too_easy")

    client = APIClient()
    _auth(client, setup["teacher"])
    resp = client.get(reverse("difficulty-calibration-list"), {"needs_review": "true"})
    assert resp.status_code == 200
    flags = [r["flag"] for r in resp.json()["results"]]
    assert flags == ["too_easy"]


@pytest.mark.django_db
def test_api_summary_counts_by_flag(setup):
    _calibration(setup, setup["subject_room"], flag="ok")
    _calibration(setup, setup["subject_room"], flag="ok")
    _calibration(setup, setup["subject_room"], flag="mislabeled")

    client = APIClient()
    _auth(client, setup["teacher"])
    resp = client.get(
        reverse("difficulty-calibration-summary"),
        {"subject_room": setup["subject_room"].pk},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_calibrated"] == 3
    assert body["flagged"] == 1
    assert body["by_flag"]["ok"] == 2
    assert body["by_flag"]["mislabeled"] == 1


@pytest.mark.django_db
def test_api_summary_requires_subject_room(setup):
    client = APIClient()
    _auth(client, setup["teacher"])
    resp = client.get(reverse("difficulty-calibration-summary"))
    assert resp.status_code == 400


@pytest.mark.django_db
def test_api_refresh_queues_task_for_owned_room(setup):
    from unittest.mock import patch

    client = APIClient()
    _auth(client, setup["teacher"])
    with patch("openshiksha.apps.ai.views.refresh_difficulty_calibrations.delay") as mock_delay:
        resp = client.post(
            reverse("difficulty-calibration-refresh"),
            {"subject_room_id": setup["subject_room"].pk},
            format="json",
        )
    assert resp.status_code == 202
    mock_delay.assert_called_once_with(setup["subject_room"].pk)


@pytest.mark.django_db
def test_api_refresh_rejects_unowned_room(setup):
    client = APIClient()
    _auth(client, setup["teacher"])
    resp = client.post(
        reverse("difficulty-calibration-refresh"),
        {"subject_room_id": setup["other_subject_room"].pk},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_refresh_forbidden_for_students(setup):
    client = APIClient()
    _auth(client, setup["students"][0])
    resp = client.post(
        reverse("difficulty-calibration-refresh"),
        {"subject_room_id": setup["subject_room"].pk},
        format="json",
    )
    assert resp.status_code == 403
