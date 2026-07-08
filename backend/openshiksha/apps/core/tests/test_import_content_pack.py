"""
Tests for CP-2 (T-4) — the ``import_content_pack`` management command.

The command is the first writer into ``ContentSubmission``: it validates a pack
via CP-1 and stages the whole pack as one ``PENDING`` row, never touching the
live question bank. Covers the accept path (import + dry-run), idempotency
(re-import no-dupe, blocked while APPROVED), the reject path (invalid pack, bad
JSON, missing file), and that a REJECTED pack can be re-staged.
"""

import json
from io import StringIO

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError

from openshiksha.apps.core.content_packs import content_pack_hash
from openshiksha.apps.core.models import ContentSubmission, ContentSubmissionState

pytestmark = pytest.mark.django_db


def _valid_pack() -> dict:
    """A minimal, fully valid pack (one MCQ subpart)."""

    return {
        "pack_version": "1.0",
        "name": "Fractions starter pack",
        "provenance": {"author": "Jane Contributor", "license": "CC-BY-4.0"},
        "questions": [
            {
                "standard": 5,
                "subject": "Mathematics",
                "chapter": "Fractions",
                "question_type": "mcq",
                "subparts": [
                    {
                        "index": 0,
                        "subpart_type": "mcq",
                        "question_text": "Which is one half?",
                        "options": [
                            {"key": "A", "text": "1/2"},
                            {"key": "B", "text": "1/3"},
                        ],
                        "correct_answer": {"type": "mcq", "answer": "A"},
                    }
                ],
            }
        ],
    }


def _write_pack(tmp_path, pack, name="pack.json"):
    path = tmp_path / name
    path.write_text(json.dumps(pack), encoding="utf-8")
    return str(path)


def _run(path, **kwargs):
    out = StringIO()
    call_command("import_content_pack", path, stdout=out, **kwargs)
    return out.getvalue()


# ── accept path ──────────────────────────────────────────────────────────────


def test_import_stages_one_pending_submission(tmp_path):
    pack = _valid_pack()
    out = _run(_write_pack(tmp_path, pack))

    subs = ContentSubmission.objects.all()
    assert subs.count() == 1
    sub = subs.get()
    assert sub.state == ContentSubmissionState.PENDING
    assert sub.name == "Fractions starter pack"
    assert sub.pack_hash == content_pack_hash(pack)
    assert sub.provenance == pack["provenance"]
    assert sub.payload == pack
    assert "PENDING" in out


def test_dry_run_writes_nothing(tmp_path):
    out = _run(_write_pack(tmp_path, _valid_pack()), dry_run=True)

    assert ContentSubmission.objects.count() == 0
    assert "dry-run" in out


# ── idempotency ──────────────────────────────────────────────────────────────


def test_reimport_is_a_no_op_while_pending(tmp_path):
    path = _write_pack(tmp_path, _valid_pack())
    _run(path)
    out = _run(path)

    assert ContentSubmission.objects.count() == 1
    assert "already pending" in out.lower()


def test_reimport_blocked_while_approved(tmp_path):
    pack = _valid_pack()
    _run(_write_pack(tmp_path, pack))
    sub = ContentSubmission.objects.get()
    sub.transition_to(ContentSubmissionState.APPROVED)

    out = _run(_write_pack(tmp_path, pack))

    assert ContentSubmission.objects.count() == 1
    assert "already approved" in out.lower()


def test_rejected_pack_can_be_restaged(tmp_path):
    pack = _valid_pack()
    path = _write_pack(tmp_path, pack)
    _run(path)
    sub = ContentSubmission.objects.get()
    sub.transition_to(ContentSubmissionState.REJECTED, note="off-syllabus")

    _run(path)

    assert ContentSubmission.objects.count() == 2
    assert ContentSubmission.objects.filter(state=ContentSubmissionState.PENDING).count() == 1
    # Same pack identity across the rejected + re-staged rows.
    assert set(ContentSubmission.objects.values_list("pack_hash", flat=True)) == {content_pack_hash(pack)}


def test_dry_run_does_not_block_a_later_real_import(tmp_path):
    path = _write_pack(tmp_path, _valid_pack())
    _run(path, dry_run=True)
    _run(path)

    assert ContentSubmission.objects.filter(state=ContentSubmissionState.PENDING).count() == 1


# ── reject path ──────────────────────────────────────────────────────────────


def test_invalid_pack_is_rejected_and_writes_nothing(tmp_path):
    pack = _valid_pack()
    del pack["provenance"]  # required block missing

    with pytest.raises(CommandError) as exc:
        _run(_write_pack(tmp_path, pack))

    assert "failed validation" in str(exc.value).lower()
    assert ContentSubmission.objects.count() == 0


def test_bad_widget_config_is_rejected(tmp_path):
    pack = _valid_pack()
    pack["questions"][0]["subparts"][0]["widget_kind"] = "number-line"
    pack["questions"][0]["subparts"][0]["widget_config"] = {"min": "not-a-number"}

    with pytest.raises(CommandError):
        _run(_write_pack(tmp_path, pack))

    assert ContentSubmission.objects.count() == 0


def test_malformed_json_is_rejected(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{ not json", encoding="utf-8")

    with pytest.raises(CommandError) as exc:
        _run(str(path))

    assert "not valid json" in str(exc.value).lower()
    assert ContentSubmission.objects.count() == 0


def test_missing_file_is_rejected(tmp_path):
    with pytest.raises(CommandError) as exc:
        _run(str(tmp_path / "nope.json"))

    assert "no such content-pack file" in str(exc.value).lower()
