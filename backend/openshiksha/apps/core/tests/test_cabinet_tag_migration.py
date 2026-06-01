"""Tests for the M7-05 cabinet tag-path data migration.

The migration module name starts with a digit (`0013_cabinet_tag_path`) which
Python's import system rejects. We test the data-rewrite logic via Django's
`migration_executor` running the migration against a real test DB instead of
importing the functions directly.
"""

import pytest

from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from openshiksha.apps.core.models import Chapter, Question, QuestionTag, QuestionType, Standard, Subject


def _make_chapter(name, std_num=9, subject_name="Mathematics"):
    standard, _ = Standard.objects.get_or_create(number=std_num)
    subject, _ = Subject.objects.get_or_create(name=subject_name)
    return Chapter.objects.create(name=name, subject=subject, standard=standard)


def _make_question(chapter):
    return Question.objects.create(
        standard=chapter.standard,
        subject=chapter.subject,
        chapter=chapter,
        question_type=QuestionType.NUMERIC,
    )


@pytest.mark.django_db(transaction=True)
class TestCabinetTagPathMigration:
    """Forward-migrate, then backward-migrate, asserting the rename round-trips."""

    PREVIOUS = ("core", "0012_user_email_reminders_opt_out_assignmentreminder")
    TARGET = ("core", "0013_cabinet_tag_path")

    def _migrate_to(self, migration):
        executor = MigrationExecutor(connection)
        executor.migrate([migration])
        # The migration framework caches the project state; reset it for clean
        # subsequent operations.
        executor.loader.build_graph()

    def test_forward_rewrites_legacy_tag_with_chapter_scope(self):
        # Set up: state at PREVIOUS migration with a legacy-named tag.
        self._migrate_to(self.PREVIOUS)
        chapter = _make_chapter("Polynomials")
        question = _make_question(chapter)
        tag = QuestionTag.objects.create(name="cabinet:1001", tag_type="special")
        question.tags.add(tag)

        # Apply target migration.
        self._migrate_to(self.TARGET)
        tag.refresh_from_db()
        assert tag.name == f"cabinet:c{chapter.id}:q1001"

    def test_reverse_round_trip(self):
        self._migrate_to(self.PREVIOUS)
        chapter = _make_chapter("Polynomials")
        question = _make_question(chapter)
        tag = QuestionTag.objects.create(name="cabinet:1001", tag_type="special")
        question.tags.add(tag)

        self._migrate_to(self.TARGET)
        self._migrate_to(self.PREVIOUS)
        tag.refresh_from_db()
        assert tag.name == "cabinet:1001"

    def test_orphan_legacy_tag_left_alone(self):
        self._migrate_to(self.PREVIOUS)
        tag = QuestionTag.objects.create(name="cabinet:9999", tag_type="special")

        self._migrate_to(self.TARGET)
        tag.refresh_from_db()
        assert tag.name == "cabinet:9999"
