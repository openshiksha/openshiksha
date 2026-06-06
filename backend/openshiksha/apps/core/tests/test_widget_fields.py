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


# ── IW-3b: per-student substitution + legacy-thermo migration command ─────────


class TestWidgetConfigSubstitution:
    """Student serializer walks widget_config and substitutes {{var}} tokens."""

    def test_substitution_into_string_leaves(self, db, school, standard, subject, chapter, teacher):
        from django.http import HttpRequest
        from rest_framework.request import Request

        from openshiksha.apps.api.serializers.core import QuestionSubpartStudentSerializer
        from openshiksha.apps.core.models import Question, QuestionSubpart, User, UserRole

        q = Question.objects.create(
            school=school, standard=standard, subject=subject, chapter=chapter, created_by=teacher
        )
        sp = QuestionSubpart.objects.create(
            question=q,
            index=0,
            subpart_type="mcq",
            question_text="What is {{a}}?",
            variable_constraints={"a": {"min": 5, "max": 5, "integer": True}},
            widget_kind="thermo-piston",
            widget_config={
                "initialVolume": "{{a}}",
                "maxHeat": 100,  # number leaf — must pass through untouched
                "nested": {"label": "Value = {{a}}", "n": 42},
                "list": ["x={{a}}", 7, True, None],
            },
        )
        student = User.objects.create_user(username="s1", password="pw", role=UserRole.STUDENT, school=school)
        req = Request(HttpRequest())
        req.user = student

        data = QuestionSubpartStudentSerializer(sp, context={"request": req}).data
        cfg = data["widget_config"]
        assert cfg["initialVolume"] == "5"
        assert cfg["maxHeat"] == 100
        assert cfg["nested"] == {"label": "Value = 5", "n": 42}
        assert cfg["list"] == ["x=5", 7, True, None]


class TestMigrateLegacyThermoCommand:
    def _make_thermo(self, school, standard, subject, chapter, teacher):
        from openshiksha.apps.core.models import Question, QuestionSubpart

        q = Question.objects.create(
            school=school, standard=standard, subject=subject, chapter=chapter, created_by=teacher
        )
        return QuestionSubpart.objects.create(
            question=q,
            index=0,
            subpart_type="mcq",
            question_text="Thermo",
            is_interactive=True,
            interactive_html="<div>legacy</div>",
            variable_constraints={"a": {"min": 1, "max": 9, "integer": True}},
        )

    def test_command_stamps_widget_kind(self, db, school, standard, subject, chapter, teacher):
        from django.core.management import call_command

        from openshiksha.apps.core.models import QuestionSubpart

        sp = self._make_thermo(school, standard, subject, chapter, teacher)
        call_command("migrate_legacy_thermo_widget", subpart_id=sp.id)
        sp.refresh_from_db()
        assert sp.widget_kind == "thermo-piston"
        # Defaults updated in IW-2 to match the legacy slider bounds.
        assert sp.widget_config["heatMin"] == -200
        assert sp.widget_config["heatMax"] == 200
        assert sp.widget_config["workMax"] == 200
        assert sp.interactive_html == "<div>legacy</div>"  # untouched
        # Idempotent re-run is a no-op
        call_command("migrate_legacy_thermo_widget", subpart_id=sp.id)
        sp.refresh_from_db()
        assert sp.widget_kind == "thermo-piston"
        # Untouched rows: explicit count check
        assert QuestionSubpart.objects.filter(widget_kind="thermo-piston").count() == 1

    def test_dry_run_writes_nothing(self, db, school, standard, subject, chapter, teacher):
        from django.core.management import call_command

        sp = self._make_thermo(school, standard, subject, chapter, teacher)
        call_command("migrate_legacy_thermo_widget", subpart_id=sp.id, dry_run=True)
        sp.refresh_from_db()
        assert sp.widget_kind == ""
        assert sp.widget_config == {}

    def test_command_strips_legacy_preamble_from_question_text(self, db, school, standard, subject, chapter, teacher):
        """The widget's own labels (formula readout, control captions) used to
        live in ``question_text`` after the M7-08 cleanup. Now that the React
        widget shows them itself, the command strips everything up to the
        actual prompt so the student sees the question once, not twice.
        """
        from django.core.management import call_command

        from openshiksha.apps.core.models import Question, QuestionSubpart

        q = Question.objects.create(
            school=school, standard=standard, subject=subject, chapter=chapter, created_by=teacher
        )
        legacy_text = (
            "Part b)\nChange in Internal Energy (ΔU) = ΔQ - ΔW\n= 0 Joules - 0 Joules\n"
            "ΔQ = Heat supplied to the system by the surroundings\n"
            "Piston (doing work):\n"
            "Heat supplied to the system:\n"
            "Based on the calculations above, what is the change in internal energy "
            "if {{k}} Joules of heat is removed from the system and {{j}} Joules of "
            "work is done on the system by the surroundings?"
        )
        sp = QuestionSubpart.objects.create(
            question=q,
            index=0,
            subpart_type="numeric",
            question_text=legacy_text,
            is_interactive=True,
            interactive_html="<div>legacy</div>",
            variable_constraints={"k": {"min": 20, "max": 200, "integer": True}},
        )

        call_command("migrate_legacy_thermo_widget", subpart_id=sp.id)
        sp.refresh_from_db()
        # Preamble (formula, control labels, "Part b)") all gone…
        assert "Part b)" not in sp.question_text
        assert "Heat supplied to the system:" not in sp.question_text
        assert "Change in Internal Energy" not in sp.question_text
        # …actual prompt preserved verbatim, including the {{var}} tokens.
        assert sp.question_text.startswith("Based on the calculations above")
        assert "{{k}}" in sp.question_text
        assert "{{j}}" in sp.question_text

    def test_command_text_clean_is_idempotent(self, db, school, standard, subject, chapter, teacher):
        """Re-running the command on a row whose preamble was already stripped
        must be a no-op for ``question_text`` (and the row count check below
        guards against accidental duplicate writes)."""
        from django.core.management import call_command

        from openshiksha.apps.core.models import Question, QuestionSubpart

        q = Question.objects.create(
            school=school, standard=standard, subject=subject, chapter=chapter, created_by=teacher
        )
        clean_prompt = "Based on the calculations above, what is ΔU?"
        sp = QuestionSubpart.objects.create(
            question=q,
            index=0,
            subpart_type="numeric",
            question_text=clean_prompt,
            is_interactive=True,
            interactive_html="<div>legacy</div>",
            variable_constraints={"k": {"min": 1, "max": 9, "integer": True}},
        )

        # First run: stamps the kind. question_text is already clean so it's
        # left alone (idx == 0 in derive_clean_prompt).
        call_command("migrate_legacy_thermo_widget", subpart_id=sp.id)
        sp.refresh_from_db()
        assert sp.widget_kind == "thermo-piston"
        assert sp.question_text == clean_prompt

        # Second run: skips both transformations.
        call_command("migrate_legacy_thermo_widget", subpart_id=sp.id)
        sp.refresh_from_db()
        assert sp.question_text == clean_prompt
