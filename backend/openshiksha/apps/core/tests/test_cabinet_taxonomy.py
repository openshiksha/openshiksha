"""Tests for the bundled cabinet taxonomy mapping (proper subject/chapter names).

The importer uses ``data/cabinet_taxonomy.json`` as its DEFAULT mapping when no
``--mapping`` is supplied, so a plain import names subjects/chapters properly
instead of leaving ``Imported Subject/Chapter N`` placeholders. Chapter ids are
reused across standards/subjects, so the mapping is keyed by the composite
``"<standard>:<subject_id>:<chapter_id>"``.
"""

from io import StringIO
from pathlib import Path

import pytest

from django.core.management import call_command

from openshiksha.apps.core.management.commands.import_cabinet_questions import _DEFAULT_TAXONOMY_PATH, Command
from openshiksha.apps.core.models import Chapter, Question, Subject

TAXONOMY_SOURCE = str(Path(__file__).parent / "fixtures" / "cabinet_taxonomy_sample")


class TestBundledTaxonomyMapping:
    def test_bundled_file_exists(self):
        assert _DEFAULT_TAXONOMY_PATH.is_file()

    def test_default_mapping_loaded_when_no_arg(self):
        mapping = Command()._load_mapping(None)
        assert mapping["subjects"]["3"] == "Physics"
        # Composite key: chapter 44 under standard 11 / subject 3 = Thermodynamics.
        assert mapping["chapters"]["11:3:44"] == "Thermodynamics"
        # Same chapter id, different subject → different (here same-named) chapter.
        assert mapping["chapters"]["11:4:44"] == "Thermodynamics"

    def test_explicit_mapping_overrides_default(self, tmp_path):
        custom = tmp_path / "m.json"
        custom.write_text('{"subjects": {"3": "MySubject"}, "chapters": {}}')
        mapping = Command()._load_mapping(str(custom))
        assert mapping["subjects"]["3"] == "MySubject"
        assert "11:3:44" not in mapping["chapters"]


@pytest.mark.django_db
class TestImportUsesProperNames:
    def test_plain_import_resolves_proper_taxonomy(self):
        """A no-mapping import of a real-id fixture (std 11 / subj 3 / chap 44)
        names the subject Physics and the chapter Thermodynamics — no placeholders."""
        call_command("import_cabinet_questions", source=TAXONOMY_SOURCE, stdout=StringIO(), stderr=StringIO())
        assert Subject.objects.filter(name="Physics").exists()
        assert Chapter.objects.filter(name="Thermodynamics", subject__name="Physics", standard__number=11).exists()
        assert not Subject.objects.filter(name__startswith="Imported Subject").exists()
        assert not Chapter.objects.filter(name__startswith="Imported Chapter").exists()

    def test_imported_question_points_at_named_taxonomy(self):
        call_command("import_cabinet_questions", source=TAXONOMY_SOURCE, stdout=StringIO(), stderr=StringIO())
        q = Question.objects.get(tags__name__startswith="cabinet:")
        assert q.subject.name == "Physics"
        assert q.chapter.name == "Thermodynamics"
