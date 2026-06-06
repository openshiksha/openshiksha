"""
Tests for the Interactive Widgets Framework data model on QuestionSubpart
(IW-3a) — `widget_kind` + `widget_config` fields, the known-kind guard, and
their exposure on the teacher write/read serializers.
"""

import pytest

from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Board,
    Chapter,
    Question,
    QuestionSubpart,
    School,
    Standard,
    Subject,
    User,
    UserRole,
)
from openshiksha.apps.core.widgets import KNOWN_WIDGET_KINDS, validate_widget_config


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Test School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=11)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Physics")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Thermodynamics", subject=subject, standard=standard, order=1)


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="t1", password="pw", role=UserRole.TEACHER, school=school)


@pytest.fixture
def question(db, school, standard, subject, chapter, teacher):
    return Question.objects.create(
        school=school,
        standard=standard,
        subject=subject,
        chapter=chapter,
        created_by=teacher,
    )


class TestWidgetFieldsModel:
    def test_defaults_are_blank_and_empty_dict(self, db, question):
        sp = QuestionSubpart.objects.create(question=question, index=0)
        assert sp.widget_kind == ""
        assert sp.widget_config == {}

    def test_round_trip(self, db, question):
        sp = QuestionSubpart.objects.create(
            question=question,
            index=0,
            widget_kind="thermo-piston",
            widget_config={"initialVolume": 5, "maxHeat": 100},
        )
        sp.refresh_from_db()
        assert sp.widget_kind == "thermo-piston"
        assert sp.widget_config == {"initialVolume": 5, "maxHeat": 100}


class TestValidateWidgetConfig:
    def test_blank_kind_is_noop(self):
        validate_widget_config("", {"anything": "goes"})
        validate_widget_config("", None)

    def test_known_kind_with_dict_passes(self):
        for kind in KNOWN_WIDGET_KINDS:
            validate_widget_config(kind, {})

    def test_unknown_kind_raises(self):
        from rest_framework.serializers import ValidationError

        with pytest.raises(ValidationError):
            validate_widget_config("not-a-real-widget", {})

    def test_non_dict_config_raises(self):
        from rest_framework.serializers import ValidationError

        with pytest.raises(ValidationError):
            validate_widget_config("thermo-piston", "string-config")
        with pytest.raises(ValidationError):
            validate_widget_config("thermo-piston", [1, 2, 3])


class TestWidgetFieldsAPI:
    @pytest.fixture
    def client(self, teacher):
        c = APIClient()
        c.force_authenticate(user=teacher)
        return c

    def _question_payload(self, standard, subject, chapter, **subpart_overrides):
        subpart = {
            "index": 0,
            "subpart_type": "mcq",
            "question_text": "What is the volume?",
            "options": [{"key": "A", "text": "5"}, {"key": "B", "text": "6"}],
            "correct_answer": {"type": "mcq", "answer": "A"},
        }
        subpart.update(subpart_overrides)
        return {
            "standard": standard.id,
            "subject": subject.id,
            "chapter": chapter.id,
            "question_type": "mcq",
            "difficulty": 2,
            "subparts": [subpart],
        }

    def test_create_with_widget_fields(self, client, standard, subject, chapter):
        payload = self._question_payload(
            standard,
            subject,
            chapter,
            widget_kind="thermo-piston",
            widget_config={"initialVolume": "{{a}}"},
        )
        resp = client.post("/api/v1/questions/", payload, format="json")
        assert resp.status_code == 201, resp.content
        qid = resp.data["id"]
        sp = QuestionSubpart.objects.get(question_id=qid)
        assert sp.widget_kind == "thermo-piston"
        assert sp.widget_config == {"initialVolume": "{{a}}"}

    def test_reject_unknown_kind(self, client, standard, subject, chapter):
        payload = self._question_payload(
            standard,
            subject,
            chapter,
            widget_kind="totally-made-up",
            widget_config={},
        )
        resp = client.post("/api/v1/questions/", payload, format="json")
        assert resp.status_code == 400
        assert b"Unknown widget kind" in resp.content or b"widget_kind" in resp.content

    def test_reject_non_dict_config(self, client, standard, subject, chapter):
        payload = self._question_payload(
            standard,
            subject,
            chapter,
            widget_kind="thermo-piston",
            widget_config=["not", "a", "dict"],
        )
        resp = client.post("/api/v1/questions/", payload, format="json")
        # DRF may reject the JSONField shape before our validator fires; either
        # way the request must fail.
        assert resp.status_code == 400

    def test_blank_kind_allows_arbitrary_config(self, client, standard, subject, chapter):
        payload = self._question_payload(
            standard,
            subject,
            chapter,
            widget_kind="",
            widget_config={},
        )
        resp = client.post("/api/v1/questions/", payload, format="json")
        assert resp.status_code == 201, resp.content
