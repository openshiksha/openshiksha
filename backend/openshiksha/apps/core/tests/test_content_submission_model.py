"""
Tests for CP-3 (T-3) — the ``ContentSubmission`` model + its state machine.

Model-only slice: no API/UI yet. Verifies defaults, the legal/illegal
transitions of the four-state lifecycle, idempotent re-approval, and that the
reviewer/note/timestamp metadata is recorded on transitions.
"""

import pytest

from openshiksha.apps.core.models import (
    ContentSubmission,
    ContentSubmissionState,
    User,
    UserRole,
)

pytestmark = pytest.mark.django_db


def _submission(**kwargs) -> ContentSubmission:
    defaults = dict(
        name="Fractions starter pack",
        pack_hash="a" * 64,
        provenance={"author": "Jane", "license": "CC-BY-4.0"},
        payload={"pack_version": "1.0"},
    )
    defaults.update(kwargs)
    return ContentSubmission.objects.create(**defaults)


def _admin() -> User:
    return User.objects.create_user(username="admin1", password="x", role=UserRole.ADMIN)


# ── defaults ─────────────────────────────────────────────────────────────────


def test_new_submission_defaults_to_pending():
    sub = _submission()
    assert sub.state == ContentSubmissionState.PENDING
    assert sub.reviewer is None
    assert sub.reviewed_at is None
    assert sub.note == ""


# ── legal transitions ────────────────────────────────────────────────────────


def test_pending_to_approved():
    sub = _submission()
    admin = _admin()
    sub.transition_to(ContentSubmissionState.APPROVED, reviewer=admin, note="looks good")
    sub.refresh_from_db()
    assert sub.state == ContentSubmissionState.APPROVED
    assert sub.reviewer == admin
    assert sub.note == "looks good"
    assert sub.reviewed_at is not None


def test_pending_to_rejected_records_reason():
    sub = _submission()
    admin = _admin()
    sub.transition_to(ContentSubmissionState.REJECTED, reviewer=admin, note="off-syllabus")
    sub.refresh_from_db()
    assert sub.state == ContentSubmissionState.REJECTED
    assert sub.note == "off-syllabus"
    assert sub.reviewed_at is not None


def test_pending_to_superseded():
    sub = _submission()
    sub.transition_to(ContentSubmissionState.SUPERSEDED)
    assert sub.state == ContentSubmissionState.SUPERSEDED


def test_rejected_can_reopen_to_pending():
    sub = _submission()
    sub.transition_to(ContentSubmissionState.REJECTED)
    sub.transition_to(ContentSubmissionState.PENDING)
    assert sub.state == ContentSubmissionState.PENDING


def test_reopen_to_pending_clears_reviewed_timestamp_semantics():
    """Re-opening lands in PENDING; reviewed_at is not stamped for a PENDING move."""

    sub = _submission()
    sub.transition_to(ContentSubmissionState.REJECTED)
    prior = sub.reviewed_at
    assert prior is not None
    sub.reviewed_at = None
    sub.transition_to(ContentSubmissionState.PENDING)
    assert sub.reviewed_at is None


# ── illegal transitions ──────────────────────────────────────────────────────


def test_approved_is_terminal():
    sub = _submission()
    sub.transition_to(ContentSubmissionState.APPROVED)
    with pytest.raises(ValueError):
        sub.transition_to(ContentSubmissionState.REJECTED)
    with pytest.raises(ValueError):
        sub.transition_to(ContentSubmissionState.PENDING)


def test_superseded_is_terminal():
    sub = _submission()
    sub.transition_to(ContentSubmissionState.SUPERSEDED)
    with pytest.raises(ValueError):
        sub.transition_to(ContentSubmissionState.APPROVED)


def test_rejected_cannot_jump_to_approved():
    sub = _submission()
    sub.transition_to(ContentSubmissionState.REJECTED)
    with pytest.raises(ValueError):
        sub.transition_to(ContentSubmissionState.APPROVED)


def test_unknown_state_rejected():
    sub = _submission()
    with pytest.raises(ValueError):
        sub.transition_to("published")


def test_illegal_transition_does_not_persist():
    sub = _submission()
    sub.transition_to(ContentSubmissionState.APPROVED)
    with pytest.raises(ValueError):
        sub.transition_to(ContentSubmissionState.REJECTED)
    sub.refresh_from_db()
    assert sub.state == ContentSubmissionState.APPROVED


# ── idempotent re-approval (keyed on pack_hash semantics) ────────────────────


def test_reapprove_same_state_is_noop():
    sub = _submission()
    admin = _admin()
    sub.transition_to(ContentSubmissionState.APPROVED, reviewer=admin)
    # Re-approving is a legal no-op — approval must be idempotent.
    sub.transition_to(ContentSubmissionState.APPROVED, reviewer=admin, note="re-run")
    assert sub.state == ContentSubmissionState.APPROVED
    assert sub.note == "re-run"


def test_can_transition_to_matches_transition_to():
    sub = _submission()
    assert sub.can_transition_to(ContentSubmissionState.APPROVED)
    assert sub.can_transition_to(ContentSubmissionState.PENDING)  # self-state is allowed
    sub.transition_to(ContentSubmissionState.APPROVED)
    assert not sub.can_transition_to(ContentSubmissionState.REJECTED)
    assert sub.can_transition_to(ContentSubmissionState.APPROVED)  # self-state no-op


def test_transition_without_save_defers_persistence():
    sub = _submission()
    sub.transition_to(ContentSubmissionState.APPROVED, save=False)
    fresh = ContentSubmission.objects.get(pk=sub.pk)
    assert fresh.state == ContentSubmissionState.PENDING  # not yet saved
    sub.save()
    fresh.refresh_from_db()
    assert fresh.state == ContentSubmissionState.APPROVED


def test_multiple_rows_can_share_pack_hash():
    """Supersede leaves two rows with the same pack_hash — not unique-constrained."""

    first = _submission()
    first.transition_to(ContentSubmissionState.SUPERSEDED)
    second = _submission()  # same default pack_hash
    assert second.pack_hash == first.pack_hash
    assert second.state == ContentSubmissionState.PENDING
