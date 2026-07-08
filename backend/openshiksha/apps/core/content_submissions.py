"""
Materialization of an approved content pack into the shared question bank (CP-3).

The pipeline's one privileged write: turning a maintainer-**approved**
``ContentSubmission`` into live ``Question`` rows. Everything upstream (CP-1
validation, CP-2 staging) keeps external content inert; this module runs *only*
from the approve action behind the admin wall, and only for a row whose state
machine has moved ``pending → approved``.

Design notes:

* **Shared bank, attributed.** Materialized questions land with ``school=None``
  (the shared OpenShiksha bank) and ``created_by`` = the approving admin. Each is
  tagged with a pack marker ``content-pack:<pack_hash[:16]>`` (a ``special``
  ``QuestionTag``) that links every question back to the ``ContentSubmission`` row
  — which permanently retains the full provenance block (author/license/source).
  ``Question`` has no dedicated attribution column, so this tag + the retained
  submission are the durable attribution trail (a first-class attribution field
  is a deliberate future migration, out of scope here).

* **Idempotent on the pack hash.** The pack marker tag *is* the idempotency key:
  if any question already carries it, the pack was already materialized and
  :func:`materialize_submission` is a no-op. So re-approving an already-approved
  pack (same ``pack_hash``) never double-inserts.
"""

from __future__ import annotations

from django.db import transaction

from openshiksha.apps.core.models import (
    Chapter,
    ContentSubmission,
    Question,
    QuestionSubpart,
    QuestionTag,
    Standard,
    Subject,
)

#: Default answer type / difficulty when a question omits them (mirrors the CP-1
#: schema's documented import defaults).
_DEFAULT_QUESTION_TYPE = "mcq"
_DEFAULT_DIFFICULTY = 2


def pack_marker_name(pack_hash: str) -> str:
    """The name of the ``QuestionTag`` that marks questions from this pack."""

    return f"content-pack:{pack_hash[:16]}"


def is_materialized(submission: ContentSubmission) -> bool:
    """Whether this submission's pack has already produced live questions."""

    return Question.objects.filter(tags__name=pack_marker_name(submission.pack_hash)).exists()


@transaction.atomic
def materialize_submission(submission: ContentSubmission, reviewer=None) -> list[Question]:
    """Create shared-bank ``Question`` rows for an approved pack; return them.

    Idempotent on ``pack_hash`` via the pack-marker tag: if the pack is already
    materialized, returns the existing questions without inserting anything. The
    caller is responsible for having transitioned the submission to ``APPROVED``
    first (this module does not touch the state machine).
    """

    marker_name = pack_marker_name(submission.pack_hash)
    pack_tag, _ = QuestionTag.objects.get_or_create(name=marker_name, defaults={"tag_type": "special"})

    if is_materialized(submission):
        return list(Question.objects.filter(tags=pack_tag))

    pack = submission.payload or {}
    created: list[Question] = []
    for q in pack.get("questions", []):
        created.append(_materialize_question(q, pack_tag, reviewer))
    return created


def _materialize_question(q: dict, pack_tag: QuestionTag, reviewer) -> Question:
    standard, _ = Standard.objects.get_or_create(number=q["standard"])
    subject, _ = Subject.objects.get_or_create(name=q["subject"])
    chapter, _ = Chapter.objects.get_or_create(subject=subject, standard=standard, name=q["chapter"])

    question = Question.objects.create(
        school=None,  # shared OpenShiksha bank
        standard=standard,
        subject=subject,
        chapter=chapter,
        question_type=q.get("question_type") or _DEFAULT_QUESTION_TYPE,
        difficulty=q.get("difficulty") or _DEFAULT_DIFFICULTY,
        stem_text=q.get("stem_text", "") or "",
        created_by=reviewer,
    )

    question.tags.add(pack_tag)
    for tag_name in q.get("tags", []) or []:
        tag, _ = QuestionTag.objects.get_or_create(name=tag_name, defaults={"tag_type": "concept"})
        question.tags.add(tag)

    for sp in q.get("subparts", []):
        QuestionSubpart.objects.create(
            question=question,
            index=sp["index"],
            subpart_type=sp.get("subpart_type", "") or "",
            question_text=sp.get("question_text", "") or "",
            options=sp.get("options"),
            correct_answer=sp.get("correct_answer", {}) or {},
            variable_constraints=sp.get("variable_constraints"),
            image_url=sp.get("image_url", "") or "",
            solution_text=sp.get("solution_text", "") or "",
            hint_text=sp.get("hint_text", "") or "",
            widget_kind=sp.get("widget_kind", "") or "",
            widget_config=sp.get("widget_config", {}) or {},
        )

    return question
