"""Standing DoD regression guard for Cabinet Data Fidelity (audit_cabinet_fidelity).

Seeds the small cabinet fixture via the importer (with the name mapping so
taxonomy resolves), asserts the audit is all-green, then mutates one row and
asserts the audit flags it — including the non-zero exit under ``--strict``.
"""

from io import StringIO
from pathlib import Path

import pytest

from django.core.management import call_command

from openshiksha.apps.core.models import QuestionSubpart

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "cabinet_sample"
SOURCE = str(FIXTURE_DIR)
MAPPING = str(FIXTURE_DIR / "mapping.json")


def _import():
    call_command("import_cabinet_questions", source=SOURCE, mapping=MAPPING, stdout=StringIO(), stderr=StringIO())


def _audit(**kwargs):
    out = StringIO()
    call_command("audit_cabinet_fidelity", stdout=out, stderr=StringIO(), **kwargs)
    return out.getvalue()


@pytest.mark.django_db
class TestCabinetFidelityAudit:
    def test_freshly_imported_corpus_is_all_green(self):
        _import()
        output = _audit()
        assert "all green" in output

    def test_blank_subpart_type_flags_wrong_widget(self):
        _import()
        sp = QuestionSubpart.objects.filter(question__tags__name__startswith="cabinet:").first()
        sp.subpart_type = ""
        sp.save(update_fields=["subpart_type"])
        output = _audit()
        assert "defects found" in output

    def test_strict_exits_nonzero_on_defect(self):
        _import()
        sp = QuestionSubpart.objects.filter(question__tags__name__startswith="cabinet:").first()
        sp.subpart_type = ""
        sp.save(update_fields=["subpart_type"])
        with pytest.raises(SystemExit):
            _audit(strict=True)

    def test_legacy_token_leak_flags(self):
        _import()
        sp = QuestionSubpart.objects.filter(question__tags__name__startswith="cabinet:").first()
        sp.question_text = "leftover #{8.gif}# token"
        sp.save(update_fields=["question_text"])
        output = _audit()
        assert "defects found" in output

    def test_strict_passes_clean_corpus(self):
        _import()
        # Should not raise on a clean corpus.
        _audit(strict=True)
