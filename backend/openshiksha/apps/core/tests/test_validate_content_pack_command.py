"""
Tests for CP-5 — the ``validate_content_pack`` management command and the
shipped example pack.

The command is the CI half of the GitHub intake funnel: read-only, DB-free
validation of one or more pack files with per-file, per-error reporting and a
non-zero exit when anything fails. The example-pack test pins the repo's
``contrib/packs/*.json`` to the validator so the documented example can never
silently rot out of sync with the schema.
"""

import json
from io import StringIO
from pathlib import Path

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError

# Repo root, from backend/openshiksha/apps/core/tests/.
_REPO_ROOT = Path(__file__).resolve().parents[5]
_CONTRIB_PACKS = _REPO_ROOT / "contrib" / "packs"


def _valid_pack() -> dict:
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


def _write(tmp_path: Path, name: str, payload) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestValidateContentPackCommand:
    def test_valid_pack_passes(self, tmp_path):
        path = _write(tmp_path, "ok.json", _valid_pack())
        out = StringIO()
        call_command("validate_content_pack", str(path), stdout=out)
        assert "✓" in out.getvalue()
        assert "All 1 content pack(s) are valid." in out.getvalue()

    def test_valid_pack_reports_question_count_and_hash(self, tmp_path):
        path = _write(tmp_path, "ok.json", _valid_pack())
        out = StringIO()
        call_command("validate_content_pack", str(path), stdout=out)
        assert "1 question(s), hash " in out.getvalue()

    def test_invalid_pack_fails_with_per_error_detail(self, tmp_path):
        pack = _valid_pack()
        del pack["provenance"]["license"]  # required by the schema
        path = _write(tmp_path, "bad.json", pack)
        err = StringIO()
        with pytest.raises(CommandError, match="1 of 1 content pack"):
            call_command("validate_content_pack", str(path), stderr=err)
        assert "license" in err.getvalue()

    def test_invalid_widget_config_is_caught(self, tmp_path):
        pack = _valid_pack()
        pack["questions"][0]["subparts"][0]["widget_kind"] = "number-line"
        # step must be > 0 per the vendored number-line schema.
        pack["questions"][0]["subparts"][0]["widget_config"] = {"step": 0}
        path = _write(tmp_path, "bad-widget.json", pack)
        with pytest.raises(CommandError):
            call_command("validate_content_pack", str(path), stderr=StringIO())

    def test_malformed_json_fails_cleanly(self, tmp_path):
        path = tmp_path / "broken.json"
        path.write_text("{not json", encoding="utf-8")
        err = StringIO()
        with pytest.raises(CommandError):
            call_command("validate_content_pack", str(path), stderr=err)
        assert "not valid JSON" in err.getvalue()

    def test_missing_file_fails_cleanly(self, tmp_path):
        with pytest.raises(CommandError):
            call_command("validate_content_pack", str(tmp_path / "nope.json"), stderr=StringIO())

    def test_mixed_batch_reports_each_file_and_fails_overall(self, tmp_path):
        good = _write(tmp_path, "good.json", _valid_pack())
        bad_pack = _valid_pack()
        bad_pack["pack_version"] = "2.0"
        bad = _write(tmp_path, "bad.json", bad_pack)
        out, err = StringIO(), StringIO()
        with pytest.raises(CommandError, match="1 of 2 content pack"):
            call_command("validate_content_pack", str(good), str(bad), stdout=out, stderr=err)
        assert "✓" in out.getvalue()
        assert "bad.json" in err.getvalue()


class TestShippedExamplePacks:
    """Every pack shipped in contrib/packs/ must validate — the documented
    example is the first thing a contributor copies, so it can never rot."""

    def test_contrib_packs_directory_exists_with_at_least_one_example(self):
        assert _CONTRIB_PACKS.is_dir()
        assert list(_CONTRIB_PACKS.glob("*.json")), "contrib/packs/ has no example pack"

    def test_every_shipped_pack_validates(self):
        paths = [str(p) for p in sorted(_CONTRIB_PACKS.glob("*.json"))]
        out = StringIO()
        call_command("validate_content_pack", *paths, stdout=out)
        assert f"All {len(paths)} content pack(s) are valid." in out.getvalue()
