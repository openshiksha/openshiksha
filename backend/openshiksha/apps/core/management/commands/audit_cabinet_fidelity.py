"""Management command: audit_cabinet_fidelity

Standing regression guard for the Cabinet Data Fidelity initiative's
Definition of Done. Reports, over the imported cabinet question corpus
(``tags__name__startswith="cabinet:"``), the cross-cutting invariants the
initiative promised — and with ``--strict`` exits non-zero if any regress, so
a future re-import can't silently undo the fidelity work.

Metrics (all should be 0 once the bank is re-imported with M7-03/06/09):
  - wrong_widget       — subparts with a blank/invalid ``subpart_type`` (M7-03).
  - legacy_tokens      — fields still holding un-converted ``_{x}_`` legacy
                         tokens or literal ``#{img}#`` inline-image tokens
                         (M7-06 + token conversion).
  - taxonomy_placeholders — cabinet questions still pointing at
                         "Imported Subject %"/"Imported Chapter %" placeholders
                         (M7-09 taxonomy inference / mapping).
  - tag_cardinality    — cabinet tags attached to != 1 Question (M7-05 identity).

Usage:
    python manage.py audit_cabinet_fidelity
    python manage.py audit_cabinet_fidelity --strict   # CI: non-zero on any defect
"""

from __future__ import annotations

import re

from django.core.management.base import BaseCommand
from django.db.models import Count

from openshiksha.apps.core.models import Question, QuestionSubpart, QuestionTag, QuestionType

_CABINET_TAG_PREFIX = "cabinet:"
_VALID_SUBPART_TYPES = {t.value for t in QuestionType if t != QuestionType.COMPOUND}

# Un-converted legacy substitution token (``_{x}_``) or a literal inline-image
# token (``#{8.gif}#``) that should have been rewritten by the importer.
_LEAK_RE = re.compile(r"_\{[a-zA-Z_]\w*\}_|#\{[^{}#]+\}#")


def _subpart_text_fields(sp: QuestionSubpart):
    yield sp.question_text or ""
    yield sp.solution_text or ""
    yield sp.hint_text or ""
    for opt in sp.options or []:
        if isinstance(opt, dict):
            yield opt.get("text", "") or ""


class Command(BaseCommand):
    help = "Audit the imported Cabinet corpus against the fidelity Definition of Done."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Exit non-zero if any metric is out of bounds (for CI).",
        )

    def handle(self, *args, **options):
        cabinet_questions = Question.objects.filter(tags__name__startswith=_CABINET_TAG_PREFIX).distinct()
        total_questions = cabinet_questions.count()

        cabinet_subparts = QuestionSubpart.objects.filter(
            question__tags__name__startswith=_CABINET_TAG_PREFIX
        ).distinct()

        # (a) wrong-widget subparts — blank or invalid subpart_type.
        wrong_widget = sum(1 for sp in cabinet_subparts if sp.subpart_type not in _VALID_SUBPART_TYPES)

        # (b) legacy/inline-image token leaks in any rendered field.
        legacy_tokens = sum(
            1
            for sp in cabinet_subparts.iterator(chunk_size=500)
            if any(_LEAK_RE.search(text) for text in _subpart_text_fields(sp))
        )

        # (c) taxonomy placeholders still referenced by cabinet questions.
        taxonomy_placeholders = (
            cabinet_questions.filter(subject__name__startswith="Imported Subject").count()
            + cabinet_questions.filter(chapter__name__startswith="Imported Chapter").count()
        )

        # (d) every cabinet tag maps to exactly one Question.
        tag_cardinality = (
            QuestionTag.objects.filter(name__startswith=_CABINET_TAG_PREFIX)
            .annotate(n=Count("questions"))
            .exclude(n=1)
            .count()
        )

        metrics = {
            "wrong_widget": wrong_widget,
            "legacy_tokens": legacy_tokens,
            "taxonomy_placeholders": taxonomy_placeholders,
            "tag_cardinality": tag_cardinality,
        }

        self.stdout.write(f"cabinet questions: {total_questions}  subparts: {cabinet_subparts.count()}")
        all_green = True
        for name, value in metrics.items():
            ok = value == 0
            all_green = all_green and ok
            style = self.style.SUCCESS if ok else self.style.ERROR
            self.stdout.write(style(f"  {name:<22} {value}"))

        if all_green:
            self.stdout.write(self.style.SUCCESS("DoD audit: all green."))
        else:
            self.stdout.write(self.style.ERROR("DoD audit: defects found."))
            if options.get("strict"):
                raise SystemExit(1)
