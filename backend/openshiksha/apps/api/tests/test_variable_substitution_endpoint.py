"""
Regression test for M7-02: variable substitution on the /questions/ browse endpoint.

Before the fix, GET /api/v1/questions/?chapter=<id> returned raw ``{{var}}`` tokens
for students because QuestionViewSet used QuestionSerializer (teacher-safe, no
substitution) instead of QuestionWithSubpartsStudentSerializer for student roles.

After the fix:
  - Students see substituted numeric values (no ``{{...}}`` in question_text).
  - Teachers still get QuestionSerializer (with correct_answer, no substitution needed).
  - MCQ options are also shuffled per-student.
"""

import pytest

from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Board,
    Chapter,
    Question,
    QuestionSubpart,
    QuestionType,
    School,
    Standard,
    Subject,
    User,
    UserRole,
)


@pytest.fixture
def browse_setup(db):
    board = Board.objects.create(name="CBSE Test Board")
    standard = Standard.objects.create(number=8, description="Class 8")
    subject = Subject.objects.create(name="Maths Browse Test")
    chapter = Chapter.objects.create(
        name="Algebra Browse",
        subject=subject,
        standard=standard,
        order=1,
    )
    school = School.objects.create(name="Browse Test School", board=board)

    student = User.objects.create_user(
        username="browse_student",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
        grade=8,
    )
    teacher = User.objects.create_user(
        username="browse_teacher",
        password="pass",
        role=UserRole.TEACHER,
        school=school,
    )

    # A question with variable constraints — should be substituted for students.
    question = Question.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.NUMERIC,
        difficulty=2,
        is_active=True,
    )
    QuestionSubpart.objects.create(
        question=question,
        index=0,
        subpart_type=QuestionType.NUMERIC,
        question_text="Solve: {{a}}x + {{b}} = {{c}}. Find x.",
        correct_answer={"type": "numeric", "answer": "({{c}} - {{b}}) / {{a}}"},
        variable_constraints={
            "a": {"min": 2, "max": 9, "integer": True},
            "b": {"min": 1, "max": 20, "integer": True},
            "c": {"min": 10, "max": 50, "integer": True},
        },
    )
    return {"chapter": chapter, "student": student, "teacher": teacher, "question": question}


def _get_first_subpart_text(client, chapter_id):
    url = f"/api/v1/questions/?chapter={chapter_id}"
    resp = client.get(url)
    assert resp.status_code == 200
    results = resp.json().get("results", resp.json())
    assert results, "No questions returned"
    subparts = results[0]["subparts"]
    assert subparts, "No subparts"
    return subparts[0]["question_text"]


@pytest.mark.django_db
def test_student_sees_substituted_variables(browse_setup):
    """Students must receive concrete numbers, not raw {{var}} tokens."""
    client = APIClient()
    client.force_authenticate(browse_setup["student"])
    text = _get_first_subpart_text(client, browse_setup["chapter"].id)
    assert "{{" not in text, f"Raw token still present for student: {text!r}"
    # Should be digits in place of variables
    assert any(c.isdigit() for c in text), f"Expected numeric values in substituted text: {text!r}"


@pytest.mark.django_db
def test_student_substitution_is_deterministic(browse_setup):
    """Two requests by the same student must return identical substituted values."""
    client = APIClient()
    client.force_authenticate(browse_setup["student"])
    t1 = _get_first_subpart_text(client, browse_setup["chapter"].id)
    t2 = _get_first_subpart_text(client, browse_setup["chapter"].id)
    assert t1 == t2, "Substitution is not deterministic across requests"


@pytest.mark.django_db
def test_different_students_may_see_different_values(browse_setup, db):
    """Two different students should (probabilistically) get different values."""
    student2 = User.objects.create_user(
        username="browse_student2",
        password="pass",
        role=UserRole.STUDENT,
        school=browse_setup["student"].school,
        grade=8,
    )
    c1 = APIClient()
    c1.force_authenticate(browse_setup["student"])
    c2 = APIClient()
    c2.force_authenticate(student2)

    t1 = _get_first_subpart_text(c1, browse_setup["chapter"].id)
    t2 = _get_first_subpart_text(c2, browse_setup["chapter"].id)
    # With a=2..9, b=1..20, c=10..50 there are thousands of combos; collision is
    # extremely unlikely but not impossible — assert only that raw tokens are gone.
    assert "{{" not in t1
    assert "{{" not in t2


@pytest.mark.django_db
def test_teacher_gets_question_serializer_with_subparts(browse_setup):
    """
    Teachers use QuestionSerializer which includes correct_answer on subparts
    and does NOT hide/substitute tokens (teachers author questions, need raw form).
    """
    client = APIClient()
    client.force_authenticate(browse_setup["teacher"])
    url = f"/api/v1/questions/?chapter={browse_setup['chapter'].id}"
    resp = client.get(url)
    assert resp.status_code == 200
    results = resp.json().get("results", resp.json())
    subpart = results[0]["subparts"][0]
    # Teacher serializer exposes correct_answer
    assert "correct_answer" in subpart, "Teacher should see correct_answer"
