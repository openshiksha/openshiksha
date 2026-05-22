"""
Tests for the SRS practice drill API.

Covers:
- /api/v1/ai/spaced-repetition/{id}/review/    — returns chapter questions (student-safe)
- /api/v1/ai/spaced-repetition/{id}/mark-reviewed/ — applies SM-2 update

Two grading shapes are supported:
- {"answers": {<subpart_id>: <answer>}} → server grades using core._grade_subpart
- {"score": 0.8}                        → client-supplied score (fallback)
"""

import json

import pytest

from django.test import Client
from django.utils import timezone

from openshiksha.apps.ai.models import SpacedRepetitionEntry
from openshiksha.apps.ai.tests.test_adaptive_learning import make_chapter, make_knowledge_node, make_subject, make_user

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_question_with_subpart(chapter, *, qtype="mcq", correct="A", options=None):
    """Create a Question with one QuestionSubpart in the given chapter."""
    from openshiksha.apps.core.models import Question, QuestionSubpart, Standard

    standard, _ = Standard.objects.get_or_create(number=7)
    q = Question.objects.create(
        standard=standard,
        subject=chapter.subject,
        chapter=chapter,
        question_type=qtype,
    )
    if options is None and qtype == "mcq":
        options = [
            {"key": "A", "text": "Photosynthesis"},
            {"key": "B", "text": "Respiration"},
            {"key": "C", "text": "Digestion"},
            {"key": "D", "text": "Excretion"},
        ]
    subpart = QuestionSubpart.objects.create(
        question=q,
        index=0,
        question_text="What process produces oxygen in plants?",
        options=options,
        correct_answer={"answer": correct},
    )
    return q, subpart


def _make_entry(student, subject_name="Biology", chapter_name="Plants"):
    subject = make_subject(subject_name)
    chapter = make_chapter(chapter_name, subject=subject)
    node = make_knowledge_node(subject, chapter)
    entry = SpacedRepetitionEntry.objects.create(
        student=student,
        knowledge_node=node,
        interval_days=1,
        easiness_factor=2.5,
        repetitions=0,
        next_review_date=timezone.localdate(),
    )
    return entry, chapter


def _client_for(student):
    client = Client()
    client.force_login(student)
    return client


# ─────────────────────────────────────────────────────────────────────────────
# review action
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestSRSReviewAction:
    def test_review_returns_chapter_questions(self):
        student = make_user(role="student", username="srs_review_student")
        entry, chapter = _make_entry(student)
        _make_question_with_subpart(chapter)
        _make_question_with_subpart(chapter)

        client = _client_for(student)
        response = client.get(f"/api/v1/ai/spaced-repetition/{entry.id}/review/")
        assert response.status_code == 200
        data = response.json()
        assert data["entry_id"] == entry.id
        assert data["chapter_name"] == chapter.name
        assert data["subject_name"] == chapter.subject.name
        assert len(data["questions"]) == 2
        # Student-safe serializer must not expose correct_answer
        for question in data["questions"]:
            for subpart in question["subparts"]:
                assert "correct_answer" not in subpart

    def test_review_requires_owning_student(self):
        owner = make_user(role="student", username="srs_owner")
        other = make_user(role="student", username="srs_other")
        entry, _ = _make_entry(owner)

        client = _client_for(other)
        response = client.get(f"/api/v1/ai/spaced-repetition/{entry.id}/review/")
        # other student can't even see the entry — get_queryset filters by student
        assert response.status_code == 404

    def test_review_caps_at_five_questions(self):
        student = make_user(role="student", username="srs_cap_student")
        entry, chapter = _make_entry(student)
        for _ in range(8):
            _make_question_with_subpart(chapter)

        client = _client_for(student)
        response = client.get(f"/api/v1/ai/spaced-repetition/{entry.id}/review/")
        assert response.status_code == 200
        assert len(response.json()["questions"]) == 5

    def test_review_empty_chapter(self):
        student = make_user(role="student", username="srs_empty_student")
        entry, _ = _make_entry(student)
        client = _client_for(student)
        response = client.get(f"/api/v1/ai/spaced-repetition/{entry.id}/review/")
        assert response.status_code == 200
        assert response.json()["questions"] == []


# ─────────────────────────────────────────────────────────────────────────────
# mark_reviewed action
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestMarkReviewedAction:
    def test_score_success_grows_interval(self):
        student = make_user(role="student", username="srs_success")
        entry, _ = _make_entry(student)
        entry.repetitions = 2
        entry.interval_days = 6
        entry.save()

        client = _client_for(student)
        response = client.post(
            f"/api/v1/ai/spaced-repetition/{entry.id}/mark-reviewed/",
            data=json.dumps({"score": 0.9}),
            content_type="application/json",
        )
        assert response.status_code == 200
        entry.refresh_from_db()
        assert entry.repetitions == 3
        # interval grows: 6 * easiness_factor (≥ 6)
        assert entry.interval_days >= 6
        assert entry.next_review_date > timezone.localdate()
        assert entry.last_reviewed_at is not None

    def test_score_failure_resets(self):
        student = make_user(role="student", username="srs_fail")
        entry, _ = _make_entry(student)
        entry.repetitions = 5
        entry.interval_days = 30
        entry.save()

        client = _client_for(student)
        response = client.post(
            f"/api/v1/ai/spaced-repetition/{entry.id}/mark-reviewed/",
            data=json.dumps({"score": 0.4}),
            content_type="application/json",
        )
        assert response.status_code == 200
        entry.refresh_from_db()
        assert entry.repetitions == 0
        assert entry.interval_days == 1

    def test_invalid_score_returns_400(self):
        student = make_user(role="student", username="srs_invalid")
        entry, _ = _make_entry(student)
        client = _client_for(student)
        response = client.post(
            f"/api/v1/ai/spaced-repetition/{entry.id}/mark-reviewed/",
            data=json.dumps({"score": "banana"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_answers_grading_correct_mcq(self):
        student = make_user(role="student", username="srs_grade_mcq")
        entry, chapter = _make_entry(student)
        _, subpart = _make_question_with_subpart(chapter, qtype="mcq", correct="A")

        # Fetch what the student actually sees (croupier may shuffle MCQ keys)
        client = _client_for(student)
        review = client.get(f"/api/v1/ai/spaced-repetition/{entry.id}/review/").json()
        # Find the displayed key for the "Photosynthesis" option (correct text)
        displayed_subpart = review["questions"][0]["subparts"][0]
        displayed_key = next(o["key"] for o in displayed_subpart["options"] if o["text"] == "Photosynthesis")

        response = client.post(
            f"/api/v1/ai/spaced-repetition/{entry.id}/mark-reviewed/",
            data=json.dumps({"answers": {str(subpart.id): displayed_key}}),
            content_type="application/json",
        )
        assert response.status_code == 200
        body = response.json()
        assert body["score"] == 1.0
        entry.refresh_from_db()
        assert entry.repetitions == 1

    def test_answers_grading_partial(self):
        student = make_user(role="student", username="srs_grade_partial")
        entry, chapter = _make_entry(student)
        _, subpart_a = _make_question_with_subpart(chapter, qtype="numeric", correct="42", options=None)
        _, subpart_b = _make_question_with_subpart(chapter, qtype="numeric", correct="100", options=None)

        client = _client_for(student)
        response = client.post(
            f"/api/v1/ai/spaced-repetition/{entry.id}/mark-reviewed/",
            data=json.dumps({"answers": {str(subpart_a.id): "42", str(subpart_b.id): "1"}}),
            content_type="application/json",
        )
        assert response.status_code == 200
        body = response.json()
        # 1 of 2 correct = 0.5 — failed recall, resets
        assert body["score"] == 0.5
        entry.refresh_from_db()
        assert entry.repetitions == 0
        assert entry.interval_days == 1

    def test_other_student_cannot_mark_reviewed(self):
        owner = make_user(role="student", username="srs_mr_owner")
        other = make_user(role="student", username="srs_mr_other")
        entry, _ = _make_entry(owner)
        client = _client_for(other)
        response = client.post(
            f"/api/v1/ai/spaced-repetition/{entry.id}/mark-reviewed/",
            data=json.dumps({"score": 0.9}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_no_body_returns_400(self):
        student = make_user(role="student", username="srs_no_body")
        entry, _ = _make_entry(student)
        client = _client_for(student)
        response = client.post(
            f"/api/v1/ai/spaced-repetition/{entry.id}/mark-reviewed/",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400
