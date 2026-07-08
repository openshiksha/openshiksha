"""
Tests for CP-3 (T-5) — the admin content-submission review API + materialization.

Covers the maintainer approval surface: the admin permission wall, the
list/detail queue, and the approve/reject/reopen actions driving the
``ContentSubmission`` state machine. Approval materializes the pack's questions
into the shared bank (``school=None``, ``created_by``=reviewer, attributed via
the pack-marker tag) and is idempotent on re-approve; rejection requires a note;
illegal transitions are 409s.
"""

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.test import APIClient

from openshiksha.apps.core.content_submissions import pack_marker_name
from openshiksha.apps.core.models import (
    ContentSubmission,
    ContentSubmissionState,
    Question,
    User,
    UserRole,
)

pytestmark = pytest.mark.django_db


def auth(user):
    client = APIClient()
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def rows(response):
    data = response.json()
    return data["results"] if isinstance(data, dict) and "results" in data else data


def _pack() -> dict:
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
                "difficulty": 3,
                "tags": ["fractions"],
                "subparts": [
                    {
                        "index": 0,
                        "subpart_type": "mcq",
                        "question_text": "Which is one half?",
                        "options": [{"key": "A", "text": "1/2"}, {"key": "B", "text": "1/3"}],
                        "correct_answer": {"type": "mcq", "answer": "A"},
                    }
                ],
            }
        ],
    }


def _submission(**kwargs) -> ContentSubmission:
    pack = kwargs.pop("payload", None) or _pack()
    defaults = dict(
        name=pack.get("name", ""),
        pack_hash=kwargs.pop("pack_hash", "a" * 64),
        provenance=pack.get("provenance", {}),
        payload=pack,
    )
    defaults.update(kwargs)
    return ContentSubmission.objects.create(**defaults)


@pytest.fixture
def admin(db):
    return User.objects.create_user(username="admin1", password="x", role=UserRole.ADMIN)


@pytest.fixture
def teacher(db):
    return User.objects.create_user(username="teacher1", password="x", role=UserRole.TEACHER)


# ── permission wall ──────────────────────────────────────────────────────────


def test_anonymous_cannot_list(db):
    resp = APIClient().get("/api/v1/content-submissions/")
    assert resp.status_code == 401


def test_teacher_cannot_list(teacher):
    resp = auth(teacher).get("/api/v1/content-submissions/")
    assert resp.status_code == 403


def test_teacher_cannot_approve(teacher):
    sub = _submission()
    resp = auth(teacher).post(f"/api/v1/content-submissions/{sub.pk}/approve/")
    assert resp.status_code == 403
    assert Question.objects.count() == 0


# ── queue (list / detail) ────────────────────────────────────────────────────


def test_admin_lists_and_filters_by_state(admin):
    _submission(pack_hash="a" * 64)
    _submission(pack_hash="b" * 64, state=ContentSubmissionState.REJECTED)

    all_rows = rows(auth(admin).get("/api/v1/content-submissions/"))
    assert len(all_rows) == 2

    pending = rows(auth(admin).get("/api/v1/content-submissions/?state=pending"))
    assert len(pending) == 1
    assert pending[0]["state"] == "pending"
    assert pending[0]["question_count"] == 1
    # List view omits the heavy payload.
    assert "payload" not in pending[0]


def test_detail_includes_payload_for_preview(admin):
    sub = _submission()
    resp = auth(admin).get(f"/api/v1/content-submissions/{sub.pk}/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["payload"]["questions"][0]["subparts"][0]["question_text"] == "Which is one half?"


# ── approve → materialize ────────────────────────────────────────────────────


def test_approve_materializes_into_shared_bank(admin):
    sub = _submission()
    resp = auth(admin).post(f"/api/v1/content-submissions/{sub.pk}/approve/")
    assert resp.status_code == 200
    assert resp.json()["state"] == "approved"

    sub.refresh_from_db()
    assert sub.state == ContentSubmissionState.APPROVED
    assert sub.reviewer == admin

    q = Question.objects.get()
    assert q.school is None  # shared bank
    assert q.created_by == admin
    assert q.difficulty == 3
    assert q.standard.number == 5
    assert q.subject.name == "Mathematics"
    assert q.chapter.name == "Fractions"
    assert q.subparts.count() == 1
    # Attribution: linked to the pack via the marker tag.
    assert q.tags.filter(name=pack_marker_name(sub.pack_hash)).exists()


def test_reapprove_is_idempotent(admin):
    sub = _submission()
    client = auth(admin)
    client.post(f"/api/v1/content-submissions/{sub.pk}/approve/")
    resp = client.post(f"/api/v1/content-submissions/{sub.pk}/approve/")

    assert resp.status_code == 200
    assert resp.json()["state"] == "approved"
    # No duplicate questions on re-approve.
    assert Question.objects.count() == 1


# ── reject / reopen ──────────────────────────────────────────────────────────


def test_reject_requires_a_note(admin):
    sub = _submission()
    resp = auth(admin).post(f"/api/v1/content-submissions/{sub.pk}/reject/", {"note": ""})
    assert resp.status_code == 400
    sub.refresh_from_db()
    assert sub.state == ContentSubmissionState.PENDING


def test_reject_archives_with_reason(admin):
    sub = _submission()
    resp = auth(admin).post(f"/api/v1/content-submissions/{sub.pk}/reject/", {"note": "off-syllabus"})
    assert resp.status_code == 200
    sub.refresh_from_db()
    assert sub.state == ContentSubmissionState.REJECTED
    assert sub.note == "off-syllabus"
    assert sub.reviewer == admin
    assert Question.objects.count() == 0


def test_reopen_moves_rejected_back_to_pending(admin):
    sub = _submission(state=ContentSubmissionState.REJECTED)
    resp = auth(admin).post(f"/api/v1/content-submissions/{sub.pk}/reopen/")
    assert resp.status_code == 200
    sub.refresh_from_db()
    assert sub.state == ContentSubmissionState.PENDING


# ── illegal transitions are 409 ──────────────────────────────────────────────


def test_reopen_pending_is_a_noop(admin):
    # Same-state is the model's idempotent no-op contract, not a conflict.
    sub = _submission()  # PENDING
    resp = auth(admin).post(f"/api/v1/content-submissions/{sub.pk}/reopen/")
    assert resp.status_code == 200
    sub.refresh_from_db()
    assert sub.state == ContentSubmissionState.PENDING


def test_reject_approved_is_conflict(admin):
    sub = _submission(state=ContentSubmissionState.APPROVED)
    resp = auth(admin).post(f"/api/v1/content-submissions/{sub.pk}/reject/", {"note": "too late"})
    assert resp.status_code == 409


def test_approve_rejected_is_conflict(admin):
    sub = _submission(state=ContentSubmissionState.REJECTED)
    resp = auth(admin).post(f"/api/v1/content-submissions/{sub.pk}/approve/")
    assert resp.status_code == 409
    assert Question.objects.count() == 0
