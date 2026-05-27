"""
Tests for POST /api/v1/ai/generate-questions/ endpoint.
"""

from unittest.mock import patch

import pytest

from rest_framework.test import APIClient

from openshiksha.apps.core.models import Board, Chapter, School, Standard, Subject, User, UserRole


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=9, description="Standard 9")


@pytest.fixture
def subject(db, board, standard):
    return Subject.objects.create(name="Mathematics", description="Math")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Polynomials", subject=subject, standard=standard, order=1)


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Test School", board=board)


@pytest.fixture
def teacher_user(db, school):
    return User.objects.create_user(
        username="teacher1",
        password="pass1234",
        role=UserRole.TEACHER,
        school=school,
    )


@pytest.fixture
def student_user(db, school):
    return User.objects.create_user(
        username="student1",
        password="pass1234",
        role=UserRole.STUDENT,
        school=school,
    )


@pytest.fixture
def teacher_client(teacher_user):
    client = APIClient()
    client.force_authenticate(user=teacher_user)
    return client


@pytest.fixture
def student_client(student_user):
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


MOCK_DRAFTS = [
    {
        "question_text": "What is the degree of the polynomial $3x^2 + 2x + 1$?",
        "options": [
            {"key": "A", "text": "1"},
            {"key": "B", "text": "2"},
            {"key": "C", "text": "3"},
            {"key": "D", "text": "0"},
        ],
        "correct_answer": "B",
        "variable_constraints": None,
        "suggested_tags": ["degree", "polynomials"],
    }
]


@pytest.mark.django_db
def test_generate_questions_success(teacher_client, chapter):
    with patch("openshiksha.apps.ai.views.generate_questions", return_value=MOCK_DRAFTS) as mock_gen:
        url = "/api/v1/ai/generate-questions/"
        response = teacher_client.post(
            url,
            {
                "topic": "Polynomial degree and leading term",
                "chapter_id": chapter.id,
                "question_type": "mcq",
                "difficulty": 2,
                "count": 1,
            },
            format="json",
        )

    assert response.status_code == 200, response.data
    assert "questions" in response.data
    assert len(response.data["questions"]) == 1
    q = response.data["questions"][0]
    assert q["question_text"] == MOCK_DRAFTS[0]["question_text"]
    assert q["correct_answer"] == "B"
    mock_gen.assert_called_once_with(
        topic="Polynomial degree and leading term",
        chapter_name="Polynomials",
        subject_name="Mathematics",
        standard_number=9,
        question_type="mcq",
        difficulty=2,
        count=1,
    )


@pytest.mark.django_db
def test_generate_questions_forbidden_for_students(student_client, chapter):
    response = student_client.post(
        "/api/v1/ai/generate-questions/",
        {
            "topic": "Polynomials",
            "chapter_id": chapter.id,
            "question_type": "mcq",
            "difficulty": 2,
            "count": 1,
        },
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_generate_questions_invalid_chapter(teacher_client):
    response = teacher_client.post(
        "/api/v1/ai/generate-questions/",
        {
            "topic": "Something",
            "chapter_id": 99999,
            "question_type": "mcq",
            "difficulty": 2,
            "count": 1,
        },
        format="json",
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_generate_questions_invalid_count(teacher_client, chapter):
    response = teacher_client.post(
        "/api/v1/ai/generate-questions/",
        {
            "topic": "Topic",
            "chapter_id": chapter.id,
            "question_type": "mcq",
            "difficulty": 2,
            "count": 10,  # out of range
        },
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_generate_questions_llm_failure_returns_503(teacher_client, chapter):
    with patch("openshiksha.apps.ai.views.generate_questions", side_effect=RuntimeError("LLM down")):
        response = teacher_client.post(
            "/api/v1/ai/generate-questions/",
            {
                "topic": "Topic",
                "chapter_id": chapter.id,
                "question_type": "mcq",
                "difficulty": 2,
                "count": 1,
            },
            format="json",
        )
    assert response.status_code == 503


@pytest.mark.django_db
def test_generate_questions_unauthenticated(chapter):
    client = APIClient()
    response = client.post(
        "/api/v1/ai/generate-questions/",
        {
            "topic": "Topic",
            "chapter_id": chapter.id,
            "question_type": "mcq",
            "difficulty": 2,
            "count": 1,
        },
        format="json",
    )
    assert response.status_code == 401
