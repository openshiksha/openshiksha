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


# A schema-valid + a schema-invalid config for every kind that ships a vendored
# JSON Schema. DTB-1 asks for exactly this: a valid and an invalid config per
# kind, proving the per-kind guard actually bites.
VALID_CONFIGS: dict[str, dict] = {
    "thermo-piston": {"heatMin": -150, "heatMax": 150, "workMax": 200, "workStep": 5},
    "number-line": {"min": 0, "max": 10, "step": 0.5, "label": "Mark 3/4"},
    "function-plotter": {"expr": "x**2", "xMin": -5, "xMax": 5},
    "fraction-bar": {"numerator": 3, "denominator": 4, "mode": "shaded"},
    "custom-html": {"html": "<b>hello</b>"},
}

INVALID_CONFIGS: dict[str, dict] = {
    # heatMin is type:number — a bare string (not a {{token}}) must fail.
    "thermo-piston": {"heatMin": "lots of heat"},
    # step has exclusiveMinimum:0 — zero must fail.
    "number-line": {"min": 0, "max": 10, "step": 0},
    # additionalProperties:false — an unknown key must fail.
    "function-plotter": {"expr": "x**2", "bogus": 1},
    # mode is an enum — "rainbow" is not a member.
    "fraction-bar": {"numerator": 1, "denominator": 4, "mode": "rainbow"},
    # html is required.
    "custom-html": {},
}


class TestValidateWidgetConfig:
    def test_blank_kind_is_noop(self):
        validate_widget_config("", {"anything": "goes"})
        validate_widget_config("", None)

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

    @pytest.mark.parametrize("kind", sorted(VALID_CONFIGS))
    def test_valid_config_per_kind_passes(self, kind):
        validate_widget_config(kind, VALID_CONFIGS[kind])

    @pytest.mark.parametrize("kind", sorted(INVALID_CONFIGS))
    def test_invalid_config_per_kind_raises(self, kind):
        from rest_framework.serializers import ValidationError

        with pytest.raises(ValidationError):
            validate_widget_config(kind, INVALID_CONFIGS[kind])

    def test_empty_config_ok_for_all_optional_kinds(self):
        # Every kind whose schema has no `required` accepts {} (defaults apply in
        # the runtime). custom-html requires `html`, so it is excluded.
        for kind in KNOWN_WIDGET_KINDS - {"custom-html"}:
            validate_widget_config(kind, {})

    def test_empty_config_rejected_for_custom_html(self):
        from rest_framework.serializers import ValidationError

        with pytest.raises(ValidationError):
            validate_widget_config("custom-html", {})

    def test_template_token_satisfies_numeric_fields(self):
        # DTB-5's variable-aware authoring: a pure {{var}} binding stands in for a
        # number/integer/boolean during validation; the croupier substitutes the
        # real value per-student before render.
        validate_widget_config("number-line", {"min": "{{lo}}", "max": "{{hi}}", "step": "{{s}}"})
        validate_widget_config("thermo-piston", {"heatMin": "{{a}}", "workStep": "{{b}}"})

    def test_partial_template_string_is_not_a_wildcard(self):
        from rest_framework.serializers import ValidationError

        # "x={{a}}" is not a *pure* token, so it stays a plain string and must
        # fail a numeric field.
        with pytest.raises(ValidationError):
            validate_widget_config("number-line", {"step": "x={{a}}"})

    def test_studio_scene_falls_back_to_floor(self):
        # No vendored schema → floor-only: any JSON object is accepted, a non-dict
        # is rejected.
        from rest_framework.serializers import ValidationError

        validate_widget_config("studio-scene", {"anything": [1, 2, {"deep": True}]})
        with pytest.raises(ValidationError):
            validate_widget_config("studio-scene", "not-a-dict")

    def test_missing_schema_file_degrades_to_floor(self, monkeypatch):
        # If a kind's schema file is unreadable, validation must degrade to
        # floor-only rather than 500 (DTB principle #4: deterministic fallback).
        from openshiksha.apps.core import widgets as widgets_mod

        # Patch the schema loader to report "no schema", then drop the cached
        # validator so it is rebuilt against the patched loader.
        monkeypatch.setattr(widgets_mod, "_load_schema", lambda kind: None)
        widgets_mod._validator_for.cache_clear()
        try:
            # number-line normally rejects step:0; with no schema it passes the floor.
            validate_widget_config("number-line", {"step": 0})
        finally:
            # Restore real validators for subsequent tests (monkeypatch restores
            # _load_schema itself at teardown).
            widgets_mod._validator_for.cache_clear()


class TestWidgetSchemaParity:
    """The vendored backend schemas must stay byte-for-identical (by content) to
    the frontend ``params.schema.json`` files — the single source of truth the
    runtime config form is generated from. Drift here is a silent guardrail bug.
    """

    def test_vendored_schemas_match_frontend(self):
        import json
        from pathlib import Path

        from openshiksha.apps.core import widgets as widgets_mod

        # backend/openshiksha/apps/core/widgets.py -> repo root is parents[4].
        repo_root = Path(widgets_mod.__file__).resolve().parents[4]
        frontend_dir = repo_root / "frontend_modern" / "src" / "widgets"
        if not frontend_dir.exists():  # pragma: no cover - deploy tree without frontend
            pytest.skip("frontend tree not present in this checkout")

        for schema_file in sorted(widgets_mod._SCHEMA_DIR.glob("*.schema.json")):
            kind = schema_file.name.removesuffix(".schema.json")
            frontend_file = frontend_dir / kind / "params.schema.json"
            assert frontend_file.exists(), f"no frontend schema for vendored kind {kind!r}"
            vendored = json.loads(schema_file.read_text(encoding="utf-8"))
            upstream = json.loads(frontend_file.read_text(encoding="utf-8"))
            assert vendored == upstream, f"vendored {kind} schema drifted from frontend source"

    def test_every_schema_is_a_valid_draft_2020_12_schema(self):
        from jsonschema import Draft202012Validator

        from openshiksha.apps.core import widgets as widgets_mod

        for kind in KNOWN_WIDGET_KINDS:
            schema = widgets_mod._load_schema(kind)
            if schema is None:
                continue
            Draft202012Validator.check_schema(schema)


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
        # DTB-5: a *pure* {{token}} leaf resolves to the variable's NATIVE type, so
        # a numeric widget field bound to a croupier var arrives as a number (not
        # the string "5", which a Number.isFinite-guarded runtime would ignore).
        assert cfg["initialVolume"] == 5 and isinstance(cfg["initialVolume"], int)
        assert cfg["maxHeat"] == 100
        # Mixed strings still render as strings.
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
