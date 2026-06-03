"""
Tests for the Teacher AI Assistant — Open-Ended Response Grading feature.

Covers:
- OpenResponseRubric / OpenResponseGrade models: creation, effective_score /
  is_reviewed properties, __str__
- llm_client.grade_open_response: stub keyword-overlap heuristic, score clamping,
  and the anthropic / google / ollama provider cascade + prompt builder
- tasks.grade_open_response: success path (→ ai_graded), failure path (→ failed),
  already-reviewed no-op
- API: rubric CRUD, open-grade list/filter/retrieve scoping, submit, regrade,
  review with teacher-only permissions and override clamping
"""

from unittest.mock import patch

import pytest

_user_counter = 0


def make_user(db, role="student", username=None):
    global _user_counter
    from openshiksha.apps.core.models import User

    _user_counter += 1
    username = username or f"og_user_{role}_{_user_counter}"
    return User.objects.create_user(username=username, password="pass", role=role)


@pytest.fixture
def setup(db):
    from openshiksha.apps.core.models import (
        Board,
        ClassRoom,
        Question,
        QuestionSubpart,
        QuestionType,
        School,
        Standard,
        Subject,
        SubjectRoom,
    )

    board = Board.objects.get_or_create(name="CBSE")[0]
    school = School.objects.get_or_create(name="OG Test School", board=board)[0]
    standard = Standard.objects.get_or_create(number=8)[0]
    subject = Subject.objects.get_or_create(name="Science")[0]
    teacher = make_user(db, role="teacher", username="og_teacher")
    other_teacher = make_user(db, role="teacher", username="og_other_teacher")
    s1 = make_user(db, role="student", username="og_s1")
    classroom = ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")
    classroom.students.add(s1)
    subject_room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    subject_room.students.add(s1)
    other_room = SubjectRoom.objects.create(
        classroom=classroom,
        subject=Subject.objects.get_or_create(name="History")[0],
        teacher=other_teacher,
    )

    from openshiksha.apps.core.models import Chapter

    chapter = Chapter.objects.get_or_create(name="Photosynthesis", subject=subject, standard=standard)[0]
    question = Question.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.SHORT_ANSWER,
        difficulty=2,
    )
    subpart = QuestionSubpart.objects.create(
        question=question,
        index=0,
        question_text="Explain how plants make their own food.",
        correct_answer={},
    )

    return {
        "school": school,
        "standard": standard,
        "subject": subject,
        "teacher": teacher,
        "other_teacher": other_teacher,
        "student": s1,
        "subject_room": subject_room,
        "other_room": other_room,
        "question": question,
        "subpart": subpart,
    }


def make_rubric(setup, max_marks=5):
    from openshiksha.apps.ai.models import OpenResponseRubric

    return OpenResponseRubric.objects.create(
        subpart=setup["subpart"],
        max_marks=max_marks,
        model_answer="Plants make food by photosynthesis using sunlight, water and carbon dioxide to produce glucose.",
        criteria=[
            {"label": "Names photosynthesis", "description": "Mentions the process", "marks": 2},
            {"label": "Lists inputs", "description": "sunlight/water/CO2", "marks": 3},
        ],
        created_by=setup["teacher"],
    )


def make_grade(setup, response_text="Plants use sunlight and water.", status="pending", **kwargs):
    from openshiksha.apps.ai.models import OpenResponseGrade

    return OpenResponseGrade.objects.create(
        subpart=setup["subpart"],
        student=setup["student"],
        subject_room=setup["subject_room"],
        response_text=response_text,
        status=status,
        max_marks=kwargs.pop("max_marks", 5),
        **kwargs,
    )


# ─────────────────────────────────────────────────────────────
# Model tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_rubric_create_and_str(setup):
    rubric = make_rubric(setup)
    assert rubric.max_marks == 5
    assert rubric.subpart == setup["subpart"]
    assert "Rubric" in str(rubric)
    # OneToOne reverse accessor used by the grader.
    assert setup["subpart"].open_response_rubric == rubric


@pytest.mark.django_db
def test_grade_effective_score_prefers_final(setup):
    grade = make_grade(setup, suggested_score=3.0)
    assert grade.effective_score == 3.0
    assert grade.is_reviewed is False

    grade.final_score = 4.5
    grade.status = "reviewed"
    grade.save()
    assert grade.effective_score == 4.5
    assert grade.is_reviewed is True


@pytest.mark.django_db
def test_grade_effective_score_none_when_ungraded(setup):
    grade = make_grade(setup)
    assert grade.effective_score is None
    assert "OpenResponseGrade" in str(grade)


# ─────────────────────────────────────────────────────────────
# llm_client.grade_open_response tests
# ─────────────────────────────────────────────────────────────


def _no_providers():
    """Patch context: no API keys, ollama unreachable → forces the stub path."""
    return patch.dict("os.environ", {"ANTHROPIC_API_KEY": "", "GOOGLE_AI_API_KEY": ""}, clear=False)


@pytest.mark.django_db
def test_grade_open_response_stub_high_overlap():
    from openshiksha.apps.ai import llm_client

    model_answer = "Photosynthesis uses sunlight water and carbon dioxide to make glucose."
    response = "Photosynthesis uses sunlight, water and carbon dioxide to make glucose."
    with _no_providers(), patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        result = llm_client.grade_open_response(
            "Explain photosynthesis.", model_answer, [], response, max_marks=5, grade_level=8
        )
    assert result["model"] == "stub"
    assert result["score"] >= 4.0  # near-identical answer scores high
    assert result["confidence"] == 0.3  # heuristic flags for review
    assert result["feedback"]


@pytest.mark.django_db
def test_grade_open_response_stub_low_overlap():
    from openshiksha.apps.ai import llm_client

    with _no_providers(), patch("openshiksha.apps.ai.llm_client._ollama_reachable", return_value=False):
        result = llm_client.grade_open_response(
            "Explain photosynthesis.",
            "Photosynthesis converts sunlight into glucose.",
            [],
            "I do not know the answer.",
            max_marks=5,
        )
    assert result["score"] < 2.0


@pytest.mark.django_db
def test_grade_open_response_anthropic_tool_and_clamp():
    from openshiksha.apps.ai import llm_client

    # Model over-awards (8 on a 5-mark question) and over-confident — both clamp.
    mock_result = {
        "data": {"score": 8, "feedback": "Great work!", "confidence": 1.4, "criterion_scores": [{"label": "x"}]},
        "model": "claude-sonnet-4-6",
        "input_tokens": 50,
        "output_tokens": 20,
    }
    with (
        patch.dict("os.environ", {"ANTHROPIC_API_KEY": "key"}, clear=False),
        patch("openshiksha.apps.ai.llm_client._call_anthropic_tool", return_value=mock_result) as mock_call,
    ):
        result = llm_client.grade_open_response("Q?", "model", [], "answer", max_marks=5)
    mock_call.assert_called_once()
    assert result["score"] == 5.0  # clamped to max
    assert result["confidence"] == 1.0  # clamped to 1
    assert result["model"] == "claude-sonnet-4-6"


@pytest.mark.django_db
def test_grade_open_response_google_cascade():
    from openshiksha.apps.ai import llm_client

    mock_result = {
        "text": '{"score": 3, "feedback": "Good", "confidence": 0.8, "criterion_scores": []}',
        "model": "gemma-4-it",
        "input_tokens": 10,
        "output_tokens": 5,
    }
    with (
        patch.dict("os.environ", {"ANTHROPIC_API_KEY": "", "GOOGLE_AI_API_KEY": "gkey"}, clear=False),
        patch("openshiksha.apps.ai.llm_client._call_google_gemma", return_value=mock_result) as mock_call,
    ):
        result = llm_client.grade_open_response("Q?", "model", [], "answer", max_marks=5)
    mock_call.assert_called_once()
    assert result["score"] == 3.0
    assert result["model"] == "gemma-4-it"


def test_grade_open_response_prompt_includes_rubric():
    from openshiksha.apps.ai.llm_client import _build_open_grade_prompt

    prompt = _build_open_grade_prompt(
        "Explain X.",
        "Model answer here.",
        [{"label": "Point A", "description": "desc", "marks": 2}],
        "Student answer.",
        max_marks=4,
        grade_level=8,
    )
    assert "Model answer here." in prompt
    assert "Point A" in prompt
    assert "out of 4 marks" in prompt
    assert "save_grade" in prompt


# ─────────────────────────────────────────────────────────────
# tasks.grade_open_response tests
# ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_task_grades_pending(setup):
    from openshiksha.apps.ai.models import OpenResponseGradeStatus
    from openshiksha.apps.ai.tasks import grade_open_response

    make_rubric(setup, max_marks=6)
    grade = make_grade(setup, status="pending", max_marks=6)

    mock = {
        "score": 4.0,
        "feedback": "Nice attempt.",
        "confidence": 0.7,
        "criterion_scores": [{"label": "x", "awarded": 2, "max": 3}],
        "model": "stub",
        "input_tokens": 0,
        "output_tokens": 0,
    }
    with patch("openshiksha.apps.ai.llm_client.grade_open_response", return_value=mock):
        grade_open_response(grade.pk)

    grade.refresh_from_db()
    assert grade.status == OpenResponseGradeStatus.AI_GRADED
    assert grade.suggested_score == 4.0
    assert grade.feedback == "Nice attempt."
    assert grade.confidence == 0.7
    assert grade.max_marks == 6


@pytest.mark.django_db
def test_task_skips_reviewed(setup):
    from openshiksha.apps.ai.tasks import grade_open_response

    grade = make_grade(setup, status="reviewed", suggested_score=2.0, final_score=5.0)
    with patch("openshiksha.apps.ai.llm_client.grade_open_response") as mock_call:
        result = grade_open_response(grade.pk)
    mock_call.assert_not_called()
    assert result["status"] == "reviewed"


@pytest.mark.django_db
def test_task_marks_failed_on_error(setup):
    from openshiksha.apps.ai.models import OpenResponseGradeStatus
    from openshiksha.apps.ai.tasks import grade_open_response

    grade = make_grade(setup, status="pending")
    with patch("openshiksha.apps.ai.llm_client.grade_open_response", side_effect=RuntimeError("boom")):
        with pytest.raises(Exception):
            grade_open_response(grade.pk)
    grade.refresh_from_db()
    assert grade.status == OpenResponseGradeStatus.FAILED
    assert "boom" in grade.error_detail


# ─────────────────────────────────────────────────────────────
# API tests
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


def auth(api_client, user):
    resp = api_client.post(
        "/api/v1/auth/login/",
        {"username": user.username, "password": "pass"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")


@pytest.mark.django_db
def test_api_rubric_create_teacher(api_client, setup):
    auth(api_client, setup["teacher"])
    resp = api_client.post(
        "/api/v1/ai/open-rubrics/",
        {
            "subpart": setup["subpart"].pk,
            "max_marks": 8,
            "model_answer": "Photosynthesis.",
            "criteria": [{"label": "names process", "marks": 8}],
        },
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["max_marks"] == 8
    assert resp.data["created_by"] == setup["teacher"].pk


@pytest.mark.django_db
def test_api_rubric_create_forbidden_for_student(api_client, setup):
    auth(api_client, setup["student"])
    resp = api_client.post(
        "/api/v1/ai/open-rubrics/",
        {"subpart": setup["subpart"].pk, "max_marks": 5},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_submit_creates_and_queues(api_client, setup):
    auth(api_client, setup["teacher"])
    make_rubric(setup, max_marks=6)
    with patch("openshiksha.apps.ai.views.grade_open_response.delay") as mock_delay:
        resp = api_client.post(
            "/api/v1/ai/open-grades/submit/",
            {
                "subpart_id": setup["subpart"].pk,
                "student_id": setup["student"].pk,
                "subject_room_id": setup["subject_room"].pk,
                "response_text": "Plants use sunlight to make food.",
            },
            format="json",
        )
    assert resp.status_code == 202
    assert resp.data["status"] == "pending"
    assert resp.data["max_marks"] == 6  # snapshotted from the rubric
    mock_delay.assert_called_once_with(resp.data["id"])


@pytest.mark.django_db
def test_api_submit_forbidden_other_room(api_client, setup):
    auth(api_client, setup["teacher"])
    with patch("openshiksha.apps.ai.views.grade_open_response.delay"):
        resp = api_client.post(
            "/api/v1/ai/open-grades/submit/",
            {
                "subpart_id": setup["subpart"].pk,
                "student_id": setup["student"].pk,
                "subject_room_id": setup["other_room"].pk,  # taught by other_teacher
                "response_text": "x",
            },
            format="json",
        )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_api_list_scoped_to_teacher_rooms(api_client, setup):
    make_grade(setup, status="ai_graded", suggested_score=3.0)
    # other teacher sees nothing
    auth(api_client, setup["other_teacher"])
    resp = api_client.get("/api/v1/ai/open-grades/")
    assert resp.status_code == 200
    assert resp.data["count"] == 0
    # owning teacher sees the grade
    auth(api_client, setup["teacher"])
    resp = api_client.get("/api/v1/ai/open-grades/?status=ai_graded")
    assert resp.data["count"] == 1


@pytest.mark.django_db
def test_api_review_sets_final_and_clamps(api_client, setup):
    grade = make_grade(setup, status="ai_graded", suggested_score=2.0, max_marks=5)
    auth(api_client, setup["teacher"])

    # over-max final_score is rejected
    resp = api_client.post(
        f"/api/v1/ai/open-grades/{grade.pk}/review/",
        {"final_score": 9},
        format="json",
    )
    assert resp.status_code == 400

    resp = api_client.post(
        f"/api/v1/ai/open-grades/{grade.pk}/review/",
        {"final_score": 4, "teacher_comment": "Good improvement."},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["status"] == "reviewed"
    assert resp.data["final_score"] == 4.0
    assert resp.data["effective_score"] == 4.0
    grade.refresh_from_db()
    assert grade.reviewed_by_id == setup["teacher"].pk
    assert grade.reviewed_at is not None


@pytest.mark.django_db
def test_api_regrade_requeues(api_client, setup):
    grade = make_grade(setup, status="ai_graded", suggested_score=2.0)
    auth(api_client, setup["teacher"])
    with patch("openshiksha.apps.ai.views.grade_open_response.delay") as mock_delay:
        resp = api_client.post(f"/api/v1/ai/open-grades/{grade.pk}/regrade/")
    assert resp.status_code == 202
    assert resp.data["status"] == "pending"
    mock_delay.assert_called_once_with(grade.pk)


@pytest.mark.django_db
def test_api_regrade_blocked_when_reviewed(api_client, setup):
    grade = make_grade(setup, status="reviewed", final_score=5.0)
    auth(api_client, setup["teacher"])
    with patch("openshiksha.apps.ai.views.grade_open_response.delay") as mock_delay:
        resp = api_client.post(f"/api/v1/ai/open-grades/{grade.pk}/regrade/")
    assert resp.status_code == 409
    mock_delay.assert_not_called()


@pytest.mark.django_db
def test_api_list_forbidden_for_student(api_client, setup):
    make_grade(setup, status="ai_graded")
    auth(api_client, setup["student"])
    resp = api_client.get("/api/v1/ai/open-grades/")
    assert resp.status_code == 200
    assert resp.data["count"] == 0
