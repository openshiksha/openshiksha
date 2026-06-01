"""Tests for the infer_taxonomy_names management command."""

from io import StringIO

import pytest

from django.core.management import call_command

from openshiksha.apps.core.management.commands.infer_taxonomy_names import _candidate_tokens, _tokenize
from openshiksha.apps.core.models import (
    Chapter,
    Question,
    QuestionSubpart,
    QuestionTag,
    QuestionType,
    Standard,
    Subject,
)


class TestTokenize:
    def test_strips_latex_inline(self):
        tokens = _tokenize(r"Solve $2x + 3 = 11$ for the value of \(x\).")
        # 'value' is a stopword, math is stripped.
        assert "solve" in tokens
        assert "value" not in tokens  # stopword
        assert all("\\" not in t and "$" not in t for t in tokens)

    def test_strips_html_tags(self):
        tokens = _tokenize("<p>polynomial equation</p>")
        assert "polynomial" in tokens
        assert "equation" in tokens
        assert "p" not in tokens

    def test_drops_stopwords_and_short_words(self):
        assert _tokenize("the of is a x") == []

    def test_keeps_hyphenated_words(self):
        tokens = _tokenize("non-metals and metals")
        assert any("metal" in t for t in tokens)


class TestCandidateTokens:
    def test_singularises_trailing_s(self):
        tokens = _candidate_tokens("Polynomials")
        assert "polynomials" in tokens
        assert "polynomial" in tokens

    def test_multiword(self):
        tokens = _candidate_tokens("Linear Equations in One Variable")
        # 'variable' has trailing-s singularisation only if it ends in s; 'variable' is kept as-is
        assert "linear" in tokens
        assert "equations" in tokens
        assert "equation" in tokens  # singular form
        assert "variable" in tokens


@pytest.mark.django_db
class TestInferCommand:
    def _make_placeholder_chapter(self, *, standard_number, subject_name, chapter_name, tag_names):
        standard, _ = Standard.objects.get_or_create(number=standard_number)
        subject, _ = Subject.objects.get_or_create(name=subject_name)
        chapter = Chapter.objects.create(name=chapter_name, subject=subject, standard=standard)
        question = Question.objects.create(
            standard=standard,
            subject=subject,
            chapter=chapter,
            question_type=QuestionType.NUMERIC,
        )
        for name in tag_names:
            tag, _ = QuestionTag.objects.get_or_create(name=name, defaults={"tag_type": "concept"})
            question.tags.add(tag)
        # A subpart with question text that reinforces the concept.
        QuestionSubpart.objects.create(
            question=question,
            index=0,
            question_text=" ".join(tag_names).replace("-", " "),
            options={},
            correct_answer={"type": "numeric", "answer": "1"},
        )
        return chapter

    def test_dry_run_does_not_persist(self):
        chapter = self._make_placeholder_chapter(
            standard_number=9,
            subject_name="Mathematics",
            chapter_name="Imported Chapter 42",
            tag_names=["polynomials", "polynomial", "degree"],
        )
        out = StringIO()
        call_command("infer_taxonomy_names", "--dry-run", stdout=out)
        chapter.refresh_from_db()
        assert chapter.name == "Imported Chapter 42"

    def test_apply_renames_chapter_with_strong_match(self):
        chapter = self._make_placeholder_chapter(
            standard_number=9,
            subject_name="Mathematics",
            chapter_name="Imported Chapter 42",
            tag_names=["polynomials", "polynomial", "degree"],
        )
        out = StringIO()
        call_command("infer_taxonomy_names", "--apply", stdout=out)
        chapter.refresh_from_db()
        assert chapter.name == "Polynomials"

    def test_skips_unmatched_chapter(self):
        chapter = self._make_placeholder_chapter(
            standard_number=9,
            subject_name="Mathematics",
            chapter_name="Imported Chapter 999",
            tag_names=["unknown-concept", "frobnicate"],
        )
        call_command("infer_taxonomy_names", "--apply", stdout=StringIO())
        chapter.refresh_from_db()
        assert chapter.name == "Imported Chapter 999"

    def test_idempotent_skips_non_placeholders(self):
        # A non-placeholder chapter should never be touched.
        standard, _ = Standard.objects.get_or_create(number=9)
        subject, _ = Subject.objects.get_or_create(name="Mathematics")
        chapter = Chapter.objects.create(name="Polynomials", subject=subject, standard=standard)
        call_command("infer_taxonomy_names", "--apply", stdout=StringIO())
        chapter.refresh_from_db()
        assert chapter.name == "Polynomials"

    def test_subject_placeholder_renamed_from_toc(self):
        subject = Subject.objects.create(name="Imported Subject 1")
        Standard.objects.get_or_create(number=9)
        call_command("infer_taxonomy_names", "--apply", stdout=StringIO())
        subject.refresh_from_db()
        assert subject.name == "Mathematics"

    def test_apply_or_dry_run_required(self):
        out = StringIO()
        call_command("infer_taxonomy_names", stdout=out)
        assert "Pass --dry-run or --apply" in out.getvalue()
