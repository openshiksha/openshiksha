"""Tests for the import_cabinet_questions management command and its converters."""

from io import StringIO
from pathlib import Path

import pytest

from django.core.management import call_command

from openshiksha.apps.core.management.commands.import_cabinet_questions import (
    DEFAULT_CONSTRAINT,
    convert_all_constraints,
    convert_constraints,
    convert_options,
    convert_pow,
    convert_subpart,
    convert_tokens,
    rewrite_inline_images,
)
from openshiksha.apps.core.models import Chapter, Question, QuestionSubpart, Subject

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "cabinet_sample"
SOURCE = str(FIXTURE_DIR)
MAPPING = str(FIXTURE_DIR / "mapping.json")


# ── Pure conversion helpers ──────────────────────────────────────────────────


class TestTokenConversion:
    def test_simple_variable_token(self):
        assert convert_tokens("_{a}_ + _{b}_") == "{{a}} + {{b}}"

    def test_expression_token_becomes_modern_double_brace(self):
        # 2026-05-30 fix: previous behaviour emitted "{a + b}" (single braces),
        # which modern croupier didn't recognise; now emits modern "{{a + b}}".
        assert convert_tokens("_{{a + b}}_") == "{{a + b}}"

    def test_expression_token_with_multiplication(self):
        # The witness case from Q652: "_{{2*k}}_" -> "{{2*k}}".
        assert convert_tokens("_{{2*k}}_") == "{{2*k}}"

    def test_expression_token_with_function(self):
        assert convert_tokens("_{{trunc(pi_val*r*r, 2)}}_") == "{{trunc(pi_val*r*r, 2)}}"

    def test_non_identifier_left_untouched(self):
        # A literal "_{1}_" is not a valid identifier and must not be rewritten.
        assert convert_tokens("_{1}_") == "_{1}_"

    def test_empty(self):
        assert convert_tokens("") == ""


class TestPowConversion:
    def test_simple(self):
        assert convert_pow("pow(2, i)") == "(2)**(i)"

    def test_with_other_ops(self):
        assert convert_pow("3 * pow(2, i)") == "3 * (2)**(i)"

    def test_nested_pow_converts_inner_without_corruption(self):
        # The inner atomic-arg call converts; the outer (whose args now contain
        # parens) is left as-is rather than being corrupted by a greedy rewrite.
        assert convert_pow("pow(pow(x, 2), 3)") == "pow((x)**(2), 3)"

    def test_no_pow(self):
        assert convert_pow("a + b") == "a + b"


class TestConstraintConversion:
    def test_single_range(self):
        assert convert_constraints({"range": {"include": [[1, 6]]}}) == {"min": 1, "max": 6, "integer": True}

    def test_empty_uses_default(self):
        assert convert_constraints({}) == DEFAULT_CONSTRAINT
        assert convert_constraints(None) == DEFAULT_CONSTRAINT

    def test_multi_range_union(self):
        result = convert_constraints({"range": {"include": [[1, 4], [6, 8]]}})
        assert result == {"min": 1, "max": 8, "integer": True}

    def test_all_constraints_map(self):
        out = convert_all_constraints({"a": {"range": {"include": [[1, 6]]}}, "b": {}})
        assert out == {"a": {"min": 1, "max": 6, "integer": True}, "b": DEFAULT_CONSTRAINT}

    def test_all_constraints_none(self):
        assert convert_all_constraints(None) is None


class TestOptionConversion:
    def test_mcq_correct_first(self):
        opts, correct = convert_options(
            {"correct": {"text": "right"}, "incorrect": [{"text": "wrong1"}, {"text": "wrong2"}]}, 1
        )
        assert opts == [
            {"key": "A", "text": "right"},
            {"key": "B", "text": "wrong1"},
            {"key": "C", "text": "wrong2"},
        ]
        assert correct == "A"

    def test_multi_select_returns_key_list(self):
        opts, correct = convert_options(
            {"correct": [{"text": "2"}, {"text": "3"}], "incorrect": [{"text": "4"}, {"text": "6"}]}, 2
        )
        assert correct == ["A", "B"]
        assert len(opts) == 4

    def test_non_four_option_count(self):
        opts, correct = convert_options({"correct": {"text": "a"}, "incorrect": [{"text": "b"}]}, 1)
        assert len(opts) == 2
        assert correct == "A"


class TestSubpartConversion:
    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            convert_subpart({"type": 99}, 0)

    def test_numeric_expression_answer(self):
        out = convert_subpart({"type": 3, "content": {"text": "x"}, "answer": {"value": "pow(2, _{j}_)"}}, 0)
        assert out["correct_answer"] == {"type": "numeric", "answer": "(2)**({{j}})"}

    def test_fill_blank_plain_answer(self):
        out = convert_subpart({"type": 4, "content": {"text": "x"}, "answer": "mitochondria"}, 0)
        assert out["correct_answer"] == {"type": "fill_blank", "answer": "mitochondria"}


class TestInlineImageRewrite:
    """M7-06: `rewrite_inline_images` resolves Cabinet inline references against
    the chapter raw dir and rewrites them to absolute raw-GitHub `<img>` tags."""

    BASE = "https://cdn.example/raw/CBSE/openshiksha/8/13/47"

    def _raw_dir(self, tmp_path, *, sibling=None, nested=None):
        if sibling:
            (tmp_path / sibling).write_text("x")
        if nested:
            (tmp_path / "img").mkdir(exist_ok=True)
            (tmp_path / "img" / nested).write_text("x")
        return tmp_path

    def test_token_resolves_to_img_subdir(self, tmp_path):
        raw = self._raw_dir(tmp_path, nested="d.png")
        out = rewrite_inline_images("see #{d.png}# here", raw, self.BASE)
        assert out == f'see <img src="{self.BASE}/img/d.png" alt="d.png"> here'

    def test_token_resolves_to_sibling(self, tmp_path):
        raw = self._raw_dir(tmp_path, sibling="d.png")
        out = rewrite_inline_images("#{d.png}#", raw, self.BASE)
        assert out == f'<img src="{self.BASE}/d.png" alt="d.png">'

    def test_unresolvable_token_left_untouched(self, tmp_path):
        out = rewrite_inline_images("#{missing.png}#", tmp_path, self.BASE)
        assert out == "#{missing.png}#"

    def test_relative_img_src_rewritten(self, tmp_path):
        raw = self._raw_dir(tmp_path, nested="d.png")
        out = rewrite_inline_images('<img src="d.png">', raw, self.BASE)
        assert out == f'<img src="{self.BASE}/img/d.png">'

    def test_absolute_img_src_untouched(self, tmp_path):
        out = rewrite_inline_images('<img src="https://x/y.png">', tmp_path, self.BASE)
        assert out == '<img src="https://x/y.png">'

    def test_empty_text(self, tmp_path):
        assert rewrite_inline_images("", tmp_path, self.BASE) == ""


# ── Management command (DB) ──────────────────────────────────────────────────


@pytest.mark.django_db
class TestImportCommand:
    def test_dry_run_writes_nothing(self):
        out = StringIO()
        call_command("import_cabinet_questions", source=SOURCE, dry_run=True, stdout=out, stderr=StringIO())
        assert Question.objects.count() == 0
        assert "DRY RUN" in out.getvalue()

    def test_missing_mapping_creates_placeholder(self):
        call_command("import_cabinet_questions", source=SOURCE, stdout=StringIO(), stderr=StringIO())
        assert Subject.objects.filter(name__startswith="Imported Subject").exists()
        assert Chapter.objects.filter(name__startswith="Imported Chapter").exists()

    def test_mapping_resolves_names(self):
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())
        assert Subject.objects.filter(name="Mathematics").exists()
        assert Chapter.objects.filter(name="Addition").exists()

    def test_malformed_question_skipped(self):
        out, err = StringIO(), StringIO()
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=out, stderr=err)
        # 6 valid questions import; the type-99 one is skipped.
        assert Question.objects.count() == 6
        assert "skip" in err.getvalue()

    def test_idempotent_reimport(self):
        for _ in range(2):
            call_command(
                "import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO()
            )
        assert Question.objects.count() == 6

    def test_solution_and_hint_imported(self):
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())
        sp = QuestionSubpart.objects.get(question__tags__name__endswith=":q1004")
        assert sp.solution_text
        assert sp.hint_text

    def test_tokens_converted_in_content(self):
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())
        sp = QuestionSubpart.objects.get(question__tags__name__endswith=":q1001")
        assert "{{a}}" in sp.question_text
        assert "_{a}_" not in sp.question_text

    def test_limit(self):
        call_command(
            "import_cabinet_questions", source=SOURCE, mapping=MAPPING, limit=2, stdout=StringIO(), stderr=StringIO()
        )
        assert Question.objects.count() == 2

    def test_image_url_set_when_sibling_file_present(self):
        """A sibling <subpart>.png file under raw/.../<chapter>/ is attached as a raw.githubusercontent.com URL."""
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())
        sp = QuestionSubpart.objects.get(question__tags__name__endswith=":q1001")
        assert sp.image_url.startswith(
            "https://raw.githubusercontent.com/openshiksha/openshiksha-cabinet/HEAD/questions/raw/"
        )
        assert sp.image_url.endswith("/2001.png")

    def test_image_url_empty_when_no_sibling_file(self):
        """A subpart with no sibling image file keeps image_url empty (the default)."""
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())
        sp = QuestionSubpart.objects.get(question__tags__name__endswith=":q1003")
        assert sp.image_url == ""

    def test_inline_image_token_rewritten_to_absolute_img(self):
        """M7-06: a `#{name}#` inline-image token in the HTML body becomes an
        absolute raw.githubusercontent.com `<img>` tag."""
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())
        sp = QuestionSubpart.objects.get(question__tags__name__endswith=":q1006")
        assert "#{organ.png}#" not in sp.question_text
        assert '<img src="https://raw.githubusercontent.com/openshiksha/openshiksha-cabinet/HEAD/' in sp.question_text
        assert sp.question_text.rstrip().endswith('alt="organ.png">')

    def test_subpart_type_set_per_subpart(self):
        """M7-03: every imported subpart carries its own type from the cabinet
        `type`, not the parent question's flat type."""
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())
        assert not QuestionSubpart.objects.filter(subpart_type="").exists()
        # Q1001 is cabinet type 1 → mcq.
        sp = QuestionSubpart.objects.get(question__tags__name__endswith=":q1001")
        assert sp.subpart_type == "mcq"

    def test_compound_question_flagged(self):
        """M7-03: a question with heterogeneous subpart types (mcq + numeric)
        gets question_type == 'compound', while each subpart keeps its own type."""
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())
        q = Question.objects.get(tags__name__endswith=":q1007")
        assert q.question_type == "compound"
        types = sorted(sp.subpart_type for sp in q.subparts.all())
        assert types == ["mcq", "numeric"]

    def test_homogeneous_question_not_compound(self):
        """A single-type question keeps that type as its summary."""
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())
        q = Question.objects.get(tags__name__endswith=":q1001")
        assert q.question_type == "mcq"

    def test_tags_are_chapter_scoped(self):
        """M7-05: tag must include the chapter PK so question_ids reused across
        chapters (e.g. `1.json` in many chapter folders) don't collapse."""
        call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())
        from openshiksha.apps.core.models import QuestionTag

        cabinet_tags = QuestionTag.objects.filter(name__startswith="cabinet:")
        for tag in cabinet_tags:
            # New form: cabinet:c<chapter_id>:q<question_id>
            assert ":c" in tag.name and ":q" in tag.name, tag.name
            # Each tag should be attached to exactly one Question.
            assert tag.questions.count() == 1
