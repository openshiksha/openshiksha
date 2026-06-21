"""
Regression tests for the M7-03 remaining slice:

  * `/questions/?search=…` must return one row per question, not one row per
    matching subpart or tag (the legacy join used to multiply rows).
  * `/questions/?standard=<number>` filters by *standard number*, matching the
    Browse endpoint's contract (#194).
"""

import pytest

from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Board,
    Chapter,
    Question,
    QuestionSubpart,
    QuestionTag,
    QuestionType,
    School,
    Standard,
    Subject,
    User,
    UserRole,
)


@pytest.fixture
def teacher_with_questions(db):
    board = Board.objects.create(name="Q-filter board")
    school = School.objects.create(name="Q-filter school", board=board)
    std7 = Standard.objects.create(number=7, description="Class 7")
    std8 = Standard.objects.create(number=8, description="Class 8")
    subject = Subject.objects.create(name="Filter Maths")
    chapter7 = Chapter.objects.create(name="Algebra 7", subject=subject, standard=std7, order=1)
    chapter8 = Chapter.objects.create(name="Algebra 8", subject=subject, standard=std8, order=1)

    teacher = User.objects.create_user(username="qbank_teacher", password="pass", role=UserRole.TEACHER, school=school)

    # Question with three subparts all matching "polynomial" — pre-fix the join
    # would have returned this question three times.
    multi = Question.objects.create(
        standard=std7,
        subject=subject,
        chapter=chapter7,
        question_type=QuestionType.MCQ,
        difficulty=2,
        is_active=True,
    )
    for i in range(3):
        QuestionSubpart.objects.create(
            question=multi,
            index=i,
            subpart_type=QuestionType.MCQ,
            question_text=f"What is a polynomial? Part {i}",
            options=[{"key": "A", "text": "a"}, {"key": "B", "text": "b"}],
            correct_answer={"type": "mcq", "answer": "A"},
        )

    # Question with two matching tags — same dedup concern.
    tagged = Question.objects.create(
        standard=std8,
        subject=subject,
        chapter=chapter8,
        question_type=QuestionType.MCQ,
        difficulty=3,
        is_active=True,
    )
    tag_a = QuestionTag.objects.create(name="polynomial")
    tag_b = QuestionTag.objects.create(name="polynomial-special")
    tagged.tags.add(tag_a, tag_b)
    QuestionSubpart.objects.create(
        question=tagged,
        index=0,
        subpart_type=QuestionType.MCQ,
        question_text="Factor x^2 + 4x + 4.",
        options=[{"key": "A", "text": "a"}, {"key": "B", "text": "b"}],
        correct_answer={"type": "mcq", "answer": "A"},
    )

    # A throwaway non-matching question on the other standard, for the Grade filter.
    other = Question.objects.create(
        standard=std7,
        subject=subject,
        chapter=chapter7,
        question_type=QuestionType.MCQ,
        difficulty=1,
        is_active=True,
    )
    QuestionSubpart.objects.create(
        question=other,
        index=0,
        subpart_type=QuestionType.MCQ,
        question_text="Solve 1 + 1.",
        options=[{"key": "A", "text": "2"}, {"key": "B", "text": "3"}],
        correct_answer={"type": "mcq", "answer": "A"},
    )

    return {
        "teacher": teacher,
        "std7": std7,
        "std8": std8,
        "multi": multi,
        "tagged": tagged,
        "other": other,
    }


def _ids(resp):
    body = resp.json()
    results = body.get("results", body)
    return sorted(q["id"] for q in results)


@pytest.mark.django_db
def test_search_deduplicates_across_subparts(teacher_with_questions):
    """A question with several matching subparts must appear once."""
    client = APIClient()
    client.force_authenticate(teacher_with_questions["teacher"])
    resp = client.get("/api/v1/questions/?search=polynomial")
    assert resp.status_code == 200
    ids = _ids(resp)
    # Both the multi-subpart question and the tag-matched question should appear,
    # but each exactly once.
    assert ids.count(teacher_with_questions["multi"].id) == 1
    assert ids.count(teacher_with_questions["tagged"].id) == 1


@pytest.mark.django_db
def test_search_deduplicates_across_tags(teacher_with_questions):
    """A question with two matching tags must appear once."""
    client = APIClient()
    client.force_authenticate(teacher_with_questions["teacher"])
    resp = client.get("/api/v1/questions/?search=polynomial-special")
    assert resp.status_code == 200
    ids = _ids(resp)
    assert ids == [teacher_with_questions["tagged"].id]


@pytest.mark.django_db
def test_standard_filter_matches_standard_number(teacher_with_questions):
    """`?standard=8` must return Grade-8 questions regardless of standard PK."""
    client = APIClient()
    client.force_authenticate(teacher_with_questions["teacher"])
    resp = client.get("/api/v1/questions/?standard=8")
    assert resp.status_code == 200
    ids = _ids(resp)
    assert ids == [teacher_with_questions["tagged"].id]


@pytest.mark.django_db
def test_filters_combine_with_search(teacher_with_questions):
    """Search + standard combine; result is still deduplicated."""
    client = APIClient()
    client.force_authenticate(teacher_with_questions["teacher"])
    resp = client.get("/api/v1/questions/?search=polynomial&standard=7")
    assert resp.status_code == 200
    ids = _ids(resp)
    assert ids == [teacher_with_questions["multi"].id]
