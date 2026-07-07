"""
Tests for CP-1 — the pure content-pack validator
(``openshiksha.apps.core.content_packs``).

No DB: every case is a dict validated against the vendored schema + the widget
config validator. Covers the accept path and a reject case per field class
(missing required, wrong type, bad enum, bounds, unknown key, empty pack,
provenance gaps, and a bad widget config), plus the hash contract.
"""

import copy

import pytest

from openshiksha.apps.core.content_packs import (
    ContentPackError,
    content_pack_errors,
    content_pack_hash,
    is_valid_content_pack,
    validate_content_pack,
)


def _valid_pack() -> dict:
    """A minimal, fully valid pack with one MCQ subpart and one widget subpart."""

    return {
        "pack_version": "1.0",
        "name": "Fractions starter pack",
        "provenance": {
            "author": "Jane Contributor",
            "license": "CC-BY-4.0",
            "source": "https://example.org/fractions",
            "contact": "jane@example.org",
        },
        "questions": [
            {
                "standard": 5,
                "subject": "Mathematics",
                "chapter": "Fractions",
                "question_type": "mcq",
                "difficulty": 2,
                "tags": ["fractions", "basics"],
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
            },
            {
                "standard": 6,
                "subject": "Mathematics",
                "chapter": "Number line",
                "subparts": [
                    {
                        "index": 0,
                        "question_text": "Mark 3 on the line.",
                        "correct_answer": {"type": "numeric", "answer": 3},
                        "widget_kind": "number-line",
                        "widget_config": {"min": 0, "max": 10, "step": 1},
                    }
                ],
            },
        ],
    }


# ── accept path ──────────────────────────────────────────────────────────────


def test_valid_pack_passes():
    pack = _valid_pack()
    assert content_pack_errors(pack) == []
    assert is_valid_content_pack(pack)
    validate_content_pack(pack)  # does not raise


def test_widget_token_binding_is_accepted():
    """A ``{{var}}`` token in a widget field is a valid deferred croupier binding."""

    pack = _valid_pack()
    pack["questions"][1]["subparts"][0]["widget_config"] = {"min": 0, "max": "{{hi}}", "step": 1}
    assert is_valid_content_pack(pack)


# ── reject: top-level structure ──────────────────────────────────────────────


def test_missing_pack_version_rejected():
    pack = _valid_pack()
    del pack["pack_version"]
    errors = content_pack_errors(pack)
    assert errors
    assert any("pack_version" in e for e in errors)


def test_wrong_pack_version_rejected():
    pack = _valid_pack()
    pack["pack_version"] = "2.0"
    assert not is_valid_content_pack(pack)


def test_empty_questions_rejected():
    pack = _valid_pack()
    pack["questions"] = []
    assert not is_valid_content_pack(pack)


def test_unknown_top_level_key_rejected():
    pack = _valid_pack()
    pack["surprise"] = True
    errors = content_pack_errors(pack)
    assert any("surprise" in e or "additional" in e.lower() for e in errors)


# ── reject: provenance ───────────────────────────────────────────────────────


def test_missing_provenance_rejected():
    pack = _valid_pack()
    del pack["provenance"]
    assert not is_valid_content_pack(pack)


def test_provenance_without_license_rejected():
    pack = _valid_pack()
    del pack["provenance"]["license"]
    errors = content_pack_errors(pack)
    assert any("license" in e for e in errors)


def test_provenance_blank_author_rejected():
    pack = _valid_pack()
    pack["provenance"]["author"] = ""
    assert not is_valid_content_pack(pack)


# ── reject: question / subpart field classes ─────────────────────────────────


def test_standard_out_of_range_rejected():
    pack = _valid_pack()
    pack["questions"][0]["standard"] = 13
    assert not is_valid_content_pack(pack)


def test_bad_question_type_enum_rejected():
    pack = _valid_pack()
    pack["questions"][0]["question_type"] = "essay"
    assert not is_valid_content_pack(pack)


def test_difficulty_out_of_range_rejected():
    pack = _valid_pack()
    pack["questions"][0]["difficulty"] = 9
    assert not is_valid_content_pack(pack)


def test_subpart_missing_question_text_rejected():
    pack = _valid_pack()
    del pack["questions"][0]["subparts"][0]["question_text"]
    assert not is_valid_content_pack(pack)


def test_subpart_blank_question_text_rejected():
    pack = _valid_pack()
    pack["questions"][0]["subparts"][0]["question_text"] = ""
    assert not is_valid_content_pack(pack)


def test_negative_subpart_index_rejected():
    pack = _valid_pack()
    pack["questions"][0]["subparts"][0]["index"] = -1
    assert not is_valid_content_pack(pack)


def test_no_subparts_rejected():
    pack = _valid_pack()
    pack["questions"][0]["subparts"] = []
    assert not is_valid_content_pack(pack)


def test_unknown_subpart_key_rejected():
    pack = _valid_pack()
    pack["questions"][0]["subparts"][0]["reward"] = 100
    assert not is_valid_content_pack(pack)


def test_malformed_option_rejected():
    pack = _valid_pack()
    pack["questions"][0]["subparts"][0]["options"] = [{"key": "A"}]  # missing text
    assert not is_valid_content_pack(pack)


# ── reject: widget config (the DRF-coupling boundary) ────────────────────────


def test_unknown_widget_kind_rejected_as_pack_error():
    pack = _valid_pack()
    pack["questions"][1]["subparts"][0]["widget_kind"] = "not-a-widget"
    with pytest.raises(ContentPackError) as exc_info:
        validate_content_pack(pack)
    # The DRF ValidationError is folded into pack-native strings, not leaked.
    assert exc_info.value.errors
    assert any("not-a-widget" in e for e in exc_info.value.errors)


def test_invalid_widget_config_rejected():
    pack = _valid_pack()
    # step must be > 0 (exclusiveMinimum) per the number-line schema.
    pack["questions"][1]["subparts"][0]["widget_config"] = {"step": -5}
    errors = content_pack_errors(pack)
    assert errors
    assert any("subparts" in e for e in errors)


def test_widget_config_error_is_never_drf_type():
    pack = _valid_pack()
    pack["questions"][1]["subparts"][0]["widget_kind"] = "not-a-widget"
    try:
        validate_content_pack(pack)
    except ContentPackError:
        pass  # expected
    except Exception as exc:  # pragma: no cover - guards the DRF-leak contract
        pytest.fail(f"leaked non-pack exception type: {type(exc)!r}")


def test_structural_errors_short_circuit_widget_validation():
    """A structurally broken pack reports structure, not widget, errors."""

    pack = _valid_pack()
    del pack["pack_version"]
    pack["questions"][1]["subparts"][0]["widget_kind"] = "not-a-widget"
    errors = content_pack_errors(pack)
    # widget check is skipped, so no 'not-a-widget' message surfaces.
    assert not any("not-a-widget" in e for e in errors)


# ── hash contract ────────────────────────────────────────────────────────────


def test_hash_is_stable_across_key_order():
    pack = _valid_pack()
    reordered = copy.deepcopy(pack)
    reordered["provenance"] = dict(reversed(list(reordered["provenance"].items())))
    assert content_pack_hash(pack) == content_pack_hash(reordered)


def test_hash_changes_with_content():
    pack = _valid_pack()
    mutated = copy.deepcopy(pack)
    mutated["questions"][0]["difficulty"] = 5
    assert content_pack_hash(pack) != content_pack_hash(mutated)
