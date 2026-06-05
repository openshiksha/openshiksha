"""
Regression test for M7-03: the /questions/browse/ endpoint filters.

The BrowsePage Subject/Grade dropdowns send `subject=<subject_id>` and
`standard=<standard_number>` (e.g. `?standard=7` for Grade 7). Before the fix,
the backend matched `standard_id=<standard_number>` which only worked by
accident when PK == number. After the fix it matches `standard__number=...`.
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
def browse_filter_setup(db):
    board = Board.objects.create(name="CBSE Filter Test")
    school = School.objects.create(name="Filter Test School", board=board)

    std7 = Standard.objects.create(number=7, description="Class 7")
    std8 = Standard.objects.create(number=8, description="Class 8")

    maths = Subject.objects.create(name="Filter Maths")
    science = Subject.objects.create(name="Filter Science")

    chapters = {
        ("maths", 7): Chapter.objects.create(name="M7", subject=maths, standard=std7, order=1),
        ("maths", 8): Chapter.objects.create(name="M8", subject=maths, standard=std8, order=1),
        ("science", 7): Chapter.objects.create(name="S7", subject=science, standard=std7, order=1),
        ("science", 8): Chapter.objects.create(name="S8", subject=science, standard=std8, order=1),
    }

    # Each chapter needs at least one shared question, or browse omits it.
    for chapter in chapters.values():
        q = Question.objects.create(
            standard=chapter.standard,
            subject=chapter.subject,
            chapter=chapter,
            question_type=QuestionType.MCQ,
            difficulty=2,
            is_active=True,
        )
        QuestionSubpart.objects.create(
            question=q,
            index=0,
            subpart_type=QuestionType.MCQ,
            question_text="dummy",
            options=[{"key": "A", "text": "a"}, {"key": "B", "text": "b"}],
            correct_answer={"type": "mcq", "answer": "A"},
        )

    student = User.objects.create_user(
        username="open_browser",
        password="pass",
        role=UserRole.OPEN_STUDENT,
        school=school,
    )
    return {
        "student": student,
        "std7": std7,
        "std8": std8,
        "maths": maths,
        "science": science,
        "chapters": chapters,
    }


def _names(resp):
    return sorted(c["name"] for c in resp.json())


@pytest.mark.django_db
def test_browse_filters_by_standard_number(browse_filter_setup):
    """`?standard=7` returns only Grade-7 chapters, regardless of standard PK."""
    client = APIClient()
    client.force_authenticate(browse_filter_setup["student"])
    resp = client.get("/api/v1/questions/browse/?standard=7")
    assert resp.status_code == 200
    assert _names(resp) == ["M7", "S7"]


@pytest.mark.django_db
def test_browse_filters_by_subject(browse_filter_setup):
    """`?subject=<maths.id>` returns only Maths chapters."""
    client = APIClient()
    client.force_authenticate(browse_filter_setup["student"])
    maths_id = browse_filter_setup["maths"].id
    resp = client.get(f"/api/v1/questions/browse/?subject={maths_id}")
    assert resp.status_code == 200
    assert _names(resp) == ["M7", "M8"]


@pytest.mark.django_db
def test_browse_filters_combine(browse_filter_setup):
    """Subject + standard combine."""
    client = APIClient()
    client.force_authenticate(browse_filter_setup["student"])
    maths_id = browse_filter_setup["maths"].id
    resp = client.get(f"/api/v1/questions/browse/?subject={maths_id}&standard=8")
    assert resp.status_code == 200
    assert _names(resp) == ["M8"]


@pytest.mark.django_db
def test_browse_unfiltered_returns_all(browse_filter_setup):
    """No params returns every chapter with shared questions."""
    client = APIClient()
    client.force_authenticate(browse_filter_setup["student"])
    resp = client.get("/api/v1/questions/browse/")
    assert resp.status_code == 200
    assert _names(resp) == ["M7", "M8", "S7", "S8"]
