"""
Tests for per-student {{var}} substitution in Question.stem_text.

The stem occasionally references the same variables a subpart samples — e.g.
"Consider a triangle with sides {{a}}, {{b}}, {{c}}" — and the student's view
of the stem must match the numbers they see in the body. We seed off the first
subpart so the stem and that subpart are guaranteed to use the same per-student
values.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APIRequestFactory

from openshiksha.apps.api.croupier import sample_variable_values
from openshiksha.apps.api.serializers.core import QuestionWithSubpartsStudentSerializer
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
def question_with_stem_vars(db):
    board = Board.objects.create(name="CBSE Stem Sub")
    standard = Standard.objects.create(number=8, description="Class 8")
    subject = Subject.objects.create(name="Maths Stem Sub")
    chapter = Chapter.objects.create(name="Linear Equations Stem", subject=subject, standard=standard, order=1)
    school = School.objects.create(name="Stem Test School", board=board)
    student = User.objects.create_user(
        username="stem_student",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
        grade=8,
    )
    question = Question.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.NUMERIC,
        difficulty=2,
        is_active=True,
        stem_text="A trader sells {{a}} apples and {{b}} bananas. Use this context to answer.",
    )
    sp = QuestionSubpart.objects.create(
        question=question,
        index=0,
        subpart_type=QuestionType.NUMERIC,
        question_text="How many fruits in total?",
        correct_answer={"type": "numeric", "answer": "{{a}} + {{b}}"},
        variable_constraints={
            "a": {"min": 5, "max": 50, "integer": True},
            "b": {"min": 5, "max": 50, "integer": True},
        },
    )
    return {"question": question, "first_subpart": sp, "student": student}


@pytest.mark.django_db
def test_authenticated_student_sees_substituted_stem(question_with_stem_vars):
    """{{a}} and {{b}} in the stem are replaced with concrete numbers."""
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = question_with_stem_vars["student"]
    serializer = QuestionWithSubpartsStudentSerializer(
        question_with_stem_vars["question"], context={"request": request}
    )
    data = serializer.data
    assert "{{" not in data["stem_text"], data["stem_text"]
    assert any(c.isdigit() for c in data["stem_text"])


@pytest.mark.django_db
def test_stem_uses_same_seed_as_first_subpart(question_with_stem_vars):
    """Stem numbers match whatever the first subpart's sample yields."""
    student = question_with_stem_vars["student"]
    first = question_with_stem_vars["first_subpart"]
    expected = sample_variable_values(first.variable_constraints, student.id, first.id)

    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = student
    serializer = QuestionWithSubpartsStudentSerializer(
        question_with_stem_vars["question"], context={"request": request}
    )
    rendered = serializer.data["stem_text"]
    assert f"sells {expected['a']} apples" in rendered
    assert f"and {expected['b']} bananas" in rendered


@pytest.mark.django_db
def test_stem_substitution_is_deterministic(question_with_stem_vars):
    """Two render passes for the same student yield identical stem text."""
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = question_with_stem_vars["student"]

    a = QuestionWithSubpartsStudentSerializer(question_with_stem_vars["question"], context={"request": request}).data[
        "stem_text"
    ]
    b = QuestionWithSubpartsStudentSerializer(question_with_stem_vars["question"], context={"request": request}).data[
        "stem_text"
    ]
    assert a == b


@pytest.mark.django_db
def test_stem_unchanged_when_no_variables(db):
    """Static stems (the common case — cabinet stems don't use vars today)
    pass through unchanged with no substitution work."""
    board = Board.objects.create(name="CBSE Stem Static")
    standard = Standard.objects.create(number=9, description="Class 9")
    subject = Subject.objects.create(name="Maths Stem Static")
    chapter = Chapter.objects.create(name="Polynomials Stem Static", subject=subject, standard=standard, order=1)
    school = School.objects.create(name="Stem Static School", board=board)
    student = User.objects.create_user(
        username="stem_static_student",
        password="pass",
        role=UserRole.STUDENT,
        school=school,
        grade=9,
    )
    static_stem = "For the given graphs find the number of zeros in each case"
    question = Question.objects.create(
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.NUMERIC,
        difficulty=2,
        is_active=True,
        stem_text=static_stem,
    )
    QuestionSubpart.objects.create(
        question=question,
        index=0,
        subpart_type=QuestionType.NUMERIC,
        question_text="<div>Graph 1</div>",
        correct_answer={"type": "numeric", "answer": 2},
        variable_constraints={},
    )

    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = student
    serializer = QuestionWithSubpartsStudentSerializer(question, context={"request": request})
    assert serializer.data["stem_text"] == static_stem


@pytest.mark.django_db
def test_anonymous_request_returns_stem_untouched(question_with_stem_vars):
    """Anonymous request → no substitution; the raw stored stem is returned.
    Anonymous browsing is rare but must not crash."""
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = AnonymousUser()
    serializer = QuestionWithSubpartsStudentSerializer(
        question_with_stem_vars["question"], context={"request": request}
    )
    assert "{{a}}" in serializer.data["stem_text"]
