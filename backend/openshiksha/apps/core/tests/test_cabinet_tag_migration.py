"""Tests for the M7-05 cabinet tag-path data migration.

The migration module name starts with a digit (`0013_cabinet_tag_path`) which
Python's import system rejects. We test the data-rewrite logic via Django's
`migration_executor` running the migration against a real test DB.

We must use **historical models** (via the executor's project_state) for any
ORM work at the PREVIOUS migration state — the live ORM may include columns
(e.g. `Question.stem_text` from migration 0014) that don't exist at the
PREVIOUS state's schema, which would make `objects.create()` fail.
"""

import pytest

from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db(transaction=True)
class TestCabinetTagPathMigration:
    """Forward-migrate, then backward-migrate, asserting the rename round-trips."""

    PREVIOUS = ("core", "0012_user_email_reminders_opt_out_assignmentreminder")
    TARGET = ("core", "0013_cabinet_tag_path")

    def _migrate_to(self, migration):
        executor = MigrationExecutor(connection)
        executor.migrate([migration])
        executor.loader.build_graph()
        return executor

    def _historical_models(self, executor, migration):
        """Return apps registry frozen at the given migration's post-apply state."""
        state = executor.loader.project_state(nodes=[migration])
        return state.apps

    def _seed_legacy_tag(self, executor, tag_name="cabinet:1001"):
        """Create chapter + question + legacy-named tag at PREVIOUS state.

        Returns (chapter_id, tag_id) so the caller can re-query via the live
        QuestionTag ORM after migrating forward (the column set on QuestionTag
        is stable across this migration).
        """
        apps = self._historical_models(executor, self.PREVIOUS)
        Standard = apps.get_model("core", "Standard")
        Subject = apps.get_model("core", "Subject")
        Chapter = apps.get_model("core", "Chapter")
        Question = apps.get_model("core", "Question")
        QuestionTag = apps.get_model("core", "QuestionTag")

        standard, _ = Standard.objects.get_or_create(number=9)
        subject, _ = Subject.objects.get_or_create(name="Mathematics")
        chapter = Chapter.objects.create(name="Polynomials", subject=subject, standard=standard)
        question = Question.objects.create(
            standard=standard,
            subject=subject,
            chapter=chapter,
            question_type="numeric",
        )
        tag = QuestionTag.objects.create(name=tag_name, tag_type="special")
        question.tags.add(tag)
        return chapter.id, tag.id

    def _tag_name(self, tag_id):
        """Look up the tag name via raw SQL — works at any migration state."""
        with connection.cursor() as cur:
            cur.execute("SELECT name FROM question_tags WHERE id = %s", [tag_id])
            row = cur.fetchone()
        return row[0] if row else None

    def test_forward_rewrites_legacy_tag_with_chapter_scope(self):
        executor = self._migrate_to(self.PREVIOUS)
        chapter_id, tag_id = self._seed_legacy_tag(executor)

        self._migrate_to(self.TARGET)
        assert self._tag_name(tag_id) == f"cabinet:c{chapter_id}:q1001"

    def test_reverse_round_trip(self):
        executor = self._migrate_to(self.PREVIOUS)
        _chapter_id, tag_id = self._seed_legacy_tag(executor)

        self._migrate_to(self.TARGET)
        self._migrate_to(self.PREVIOUS)
        assert self._tag_name(tag_id) == "cabinet:1001"

    def test_orphan_legacy_tag_left_alone(self):
        executor = self._migrate_to(self.PREVIOUS)
        apps = self._historical_models(executor, self.PREVIOUS)
        QuestionTag = apps.get_model("core", "QuestionTag")
        tag = QuestionTag.objects.create(name="cabinet:9999", tag_type="special")

        self._migrate_to(self.TARGET)
        assert self._tag_name(tag.id) == "cabinet:9999"
