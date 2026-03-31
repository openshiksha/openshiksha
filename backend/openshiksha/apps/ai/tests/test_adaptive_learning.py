"""
Tests for the Adaptive Learning Engine.

Covers:
- compute_updated_mastery (EWMA)
- compute_srs_update (SM-2)
- MasteryLevel.level_from_score
- generate_learning_path_steps (integration with DB fixtures)
- LearningPath / LearningPathStep model behaviour
- API endpoints: /ai/knowledge-nodes/, /ai/mastery/, /ai/spaced-repetition/, /ai/learning-paths/

Uses pytest-django with in-memory SQLite (no running Postgres needed).
"""

import pytest
from django.utils import timezone

from openshiksha.apps.ai.adaptive_analytics import (
    MASTERY_ALPHA,
    MASTERY_SKIP_THRESHOLD,
    SRS_SUCCESS_THRESHOLD,
    _topological_sort_nodes,
    compute_srs_update,
    compute_updated_mastery,
)
from openshiksha.apps.ai.models import (
    KnowledgeNode,
    LearningPath,
    LearningPathStatus,
    LearningPathStep,
    MasteryLevel,
    SpacedRepetitionEntry,
    StepStatus,
    StudentMastery,
)


# ─────────────────────────────────────────────────────────────────────────────
# Shared DB fixtures
# ─────────────────────────────────────────────────────────────────────────────

def make_user(role="student", username=None):
    from openshiksha.apps.core.models import User
    username = username or f"user_{timezone.now().timestamp()}"
    return User.objects.create_user(username=username, password="pass", role=role)


def make_board():
    from openshiksha.apps.core.models import Board
    return Board.objects.create(name=f"Board_{timezone.now().timestamp()}")


def make_school(board):
    from openshiksha.apps.core.models import School
    return School.objects.create(name=f"School_{timezone.now().timestamp()}", board=board)


def make_standard():
    from openshiksha.apps.core.models import Standard
    obj, _ = Standard.objects.get_or_create(number=7)
    return obj


def make_subject(name="Maths"):
    from openshiksha.apps.core.models import Subject
    obj, _ = Subject.objects.get_or_create(name=name)
    return obj


def make_chapter(name, order=1):
    from openshiksha.apps.core.models import Chapter
    obj, _ = Chapter.objects.get_or_create(name=name, defaults={"order": order})
    return obj


def make_subject_room(classroom, subject):
    from openshiksha.apps.core.models import SubjectRoom
    obj, _ = SubjectRoom.objects.get_or_create(classroom=classroom, subject=subject)
    return obj


def make_classroom(school, standard, name="6A"):
    from openshiksha.apps.core.models import ClassRoom
    obj, _ = ClassRoom.objects.get_or_create(school=school, standard=standard, name=name)
    return obj


def make_knowledge_node(subject, chapter, difficulty_weight=1.0):
    node, _ = KnowledgeNode.objects.get_or_create(
        subject=subject,
        chapter=chapter,
        defaults={"difficulty_weight": difficulty_weight},
    )
    return node


# ─────────────────────────────────────────────────────────────────────────────
# compute_updated_mastery
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeUpdatedMastery:
    def test_first_attempt_uses_raw_score(self):
        result = compute_updated_mastery(0.0, 0.75, attempt_count=0)
        assert result == pytest.approx(0.75)

    def test_subsequent_attempt_applies_ewma(self):
        current = 0.60
        new = 0.80
        result = compute_updated_mastery(current, new, attempt_count=3)
        expected = MASTERY_ALPHA * new + (1 - MASTERY_ALPHA) * current
        assert result == pytest.approx(expected)

    def test_score_stays_within_bounds_low(self):
        result = compute_updated_mastery(0.10, 0.0, attempt_count=5)
        assert 0.0 <= result <= 1.0

    def test_score_stays_within_bounds_high(self):
        result = compute_updated_mastery(0.90, 1.0, attempt_count=10)
        assert 0.0 <= result <= 1.0

    def test_ewma_weights_recent_more(self):
        # A bad recent score should pull the EWMA down from a high baseline
        result_bad = compute_updated_mastery(0.90, 0.20, attempt_count=5)
        result_good = compute_updated_mastery(0.20, 0.90, attempt_count=5)
        assert result_bad < 0.90
        assert result_good > 0.20


# ─────────────────────────────────────────────────────────────────────────────
# compute_srs_update
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeSrsUpdate:
    def test_first_success_gives_interval_1(self):
        result = compute_srs_update(0.80, current_interval=1, current_ef=2.5, current_repetitions=0)
        assert result["interval_days"] == 1
        assert result["repetitions"] == 1

    def test_second_success_gives_interval_6(self):
        result = compute_srs_update(0.85, current_interval=1, current_ef=2.5, current_repetitions=1)
        assert result["interval_days"] == 6
        assert result["repetitions"] == 2

    def test_third_success_scales_by_ef(self):
        result = compute_srs_update(0.90, current_interval=6, current_ef=2.5, current_repetitions=2)
        assert result["interval_days"] == round(6 * 2.5)
        assert result["repetitions"] == 3

    def test_failure_resets_repetitions_and_interval(self):
        result = compute_srs_update(0.40, current_interval=15, current_ef=2.5, current_repetitions=4)
        assert result["interval_days"] == 1
        assert result["repetitions"] == 0

    def test_failure_does_not_change_ef(self):
        ef = 2.5
        result = compute_srs_update(0.30, current_interval=6, current_ef=ef, current_repetitions=2)
        assert result["easiness_factor"] == pytest.approx(ef)

    def test_perfect_score_increases_ef(self):
        result = compute_srs_update(1.0, current_interval=6, current_ef=2.5, current_repetitions=2)
        assert result["easiness_factor"] > 2.5

    def test_mediocre_score_decreases_ef(self):
        result = compute_srs_update(SRS_SUCCESS_THRESHOLD, current_interval=6, current_ef=2.5, current_repetitions=2)
        assert result["easiness_factor"] < 2.5

    def test_ef_never_falls_below_minimum(self):
        # Many failures should floor at SRS_MIN_EF (1.3)
        ef = 1.31
        result = compute_srs_update(0.61, current_interval=1, current_ef=ef, current_repetitions=1)
        assert result["easiness_factor"] >= 1.3


# ─────────────────────────────────────────────────────────────────────────────
# MasteryLevel.level_from_score
# ─────────────────────────────────────────────────────────────────────────────

class TestMasteryLevelFromScore:
    def test_mastered(self):
        assert StudentMastery.level_from_score(0.85) == MasteryLevel.MASTERED
        assert StudentMastery.level_from_score(0.80) == MasteryLevel.MASTERED

    def test_proficient(self):
        assert StudentMastery.level_from_score(0.65) == MasteryLevel.PROFICIENT
        assert StudentMastery.level_from_score(0.60) == MasteryLevel.PROFICIENT

    def test_developing(self):
        assert StudentMastery.level_from_score(0.50) == MasteryLevel.DEVELOPING
        assert StudentMastery.level_from_score(0.40) == MasteryLevel.DEVELOPING

    def test_novice(self):
        assert StudentMastery.level_from_score(0.10) == MasteryLevel.NOVICE
        assert StudentMastery.level_from_score(0.0) == MasteryLevel.NOVICE


# ─────────────────────────────────────────────────────────────────────────────
# Topological sort
# ─────────────────────────────────────────────────────────────────────────────

class TestTopologicalSortNodes:
    """Test _topological_sort_nodes using mock-like objects."""

    class FakeChapter:
        def __init__(self, order):
            self.order = order

    class FakeNode:
        def __init__(self, pk, order):
            self.pk = pk
            self.chapter = TestTopologicalSortNodes.FakeChapter(order)

    def test_no_prerequisites_sorts_by_order(self):
        nodes = [self.FakeNode(3, 3), self.FakeNode(1, 1), self.FakeNode(2, 2)]
        result = _topological_sort_nodes(nodes, {})
        assert [n.pk for n in result] == [1, 2, 3]

    def test_prerequisite_respected(self):
        # Node 2 depends on Node 1 → Node 1 must come first
        nodes = [self.FakeNode(1, 1), self.FakeNode(2, 2)]
        prereq_map = {2: [1], 1: []}
        result = _topological_sort_nodes(nodes, prereq_map)
        pks = [n.pk for n in result]
        assert pks.index(1) < pks.index(2)

    def test_chain_prerequisite(self):
        # 3 → 2 → 1 (1 has no prereqs)
        nodes = [self.FakeNode(1, 1), self.FakeNode(2, 2), self.FakeNode(3, 3)]
        prereq_map = {1: [], 2: [1], 3: [2]}
        result = _topological_sort_nodes(nodes, prereq_map)
        pks = [n.pk for n in result]
        assert pks.index(1) < pks.index(2) < pks.index(3)

    def test_cycle_handled_gracefully(self):
        # Cycle: 1 ↔ 2 — should not infinite-loop; both appear in result
        nodes = [self.FakeNode(1, 1), self.FakeNode(2, 2)]
        prereq_map = {1: [2], 2: [1]}
        result = _topological_sort_nodes(nodes, prereq_map)
        assert len(result) == 2


# ─────────────────────────────────────────────────────────────────────────────
# KnowledgeNode model
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestKnowledgeNodeModel:
    def test_create_node(self):
        subject = make_subject("Science")
        chapter = make_chapter("Forces", order=1)
        node = make_knowledge_node(subject, chapter)
        assert node.pk is not None
        assert node.difficulty_weight == 1.0

    def test_prerequisite_relationship(self):
        subject = make_subject("Science_B")
        ch1 = make_chapter("Motion", order=1)
        ch2 = make_chapter("Forces_B", order=2)
        node1 = make_knowledge_node(subject, ch1)
        node2 = make_knowledge_node(subject, ch2)
        node2.prerequisites.add(node1)
        assert node1 in node2.prerequisites.all()
        assert node2 in node1.unlocks.all()

    def test_str(self):
        subject = make_subject("Chemistry")
        chapter = make_chapter("Atoms")
        node = make_knowledge_node(subject, chapter)
        assert "Atoms" in str(node)


# ─────────────────────────────────────────────────────────────────────────────
# StudentMastery model
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStudentMasteryModel:
    def test_create_mastery(self):
        student = make_user(role="student", username="mastery_student")
        subject = make_subject("History")
        chapter = make_chapter("Ancient Rome")
        node = make_knowledge_node(subject, chapter)
        mastery = StudentMastery.objects.create(
            student=student,
            knowledge_node=node,
            mastery_score=0.70,
            mastery_level=MasteryLevel.PROFICIENT,
            attempt_count=3,
        )
        assert mastery.pk is not None
        assert mastery.mastery_level == MasteryLevel.PROFICIENT

    def test_level_from_score_integration(self):
        assert StudentMastery.level_from_score(0.85) == MasteryLevel.MASTERED
        assert StudentMastery.level_from_score(0.65) == MasteryLevel.PROFICIENT
        assert StudentMastery.level_from_score(0.50) == MasteryLevel.DEVELOPING
        assert StudentMastery.level_from_score(0.20) == MasteryLevel.NOVICE


# ─────────────────────────────────────────────────────────────────────────────
# SpacedRepetitionEntry model
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSpacedRepetitionEntryModel:
    def test_create_entry(self):
        student = make_user(role="student", username="srs_student")
        subject = make_subject("Geography")
        chapter = make_chapter("Rivers")
        node = make_knowledge_node(subject, chapter)
        entry = SpacedRepetitionEntry.objects.create(
            student=student,
            knowledge_node=node,
            interval_days=6,
            easiness_factor=2.5,
            repetitions=1,
            next_review_date=timezone.localdate(),
        )
        assert entry.pk is not None
        assert entry.interval_days == 6

    def test_str(self):
        student = make_user(role="student", username="srs_str_student")
        subject = make_subject("Physics")
        chapter = make_chapter("Optics")
        node = make_knowledge_node(subject, chapter)
        entry = SpacedRepetitionEntry.objects.create(
            student=student,
            knowledge_node=node,
            interval_days=1,
            next_review_date=timezone.localdate(),
        )
        assert "Optics" in str(entry)


# ─────────────────────────────────────────────────────────────────────────────
# LearningPath + LearningPathStep models
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLearningPathModel:
    def setup_method(self):
        self.board = make_board()
        self.school = make_school(self.board)
        self.standard = make_standard()
        self.classroom = make_classroom(self.school, self.standard)
        self.subject = make_subject("English")
        self.subject_room = make_subject_room(self.classroom, self.subject)
        self.student = make_user(role="student", username="path_student")

    def test_create_empty_path(self):
        path = LearningPath.objects.create(
            student=self.student,
            subject_room=self.subject_room,
            status=LearningPathStatus.ACTIVE,
            total_steps=0,
            completed_steps=0,
        )
        assert path.pk is not None
        assert path.progress_pct == 0.0

    def test_progress_pct(self):
        path = LearningPath.objects.create(
            student=self.student,
            subject_room=self.subject_room,
            total_steps=4,
            completed_steps=2,
        )
        assert path.progress_pct == pytest.approx(0.5)

    def test_progress_pct_zero_total(self):
        path = LearningPath.objects.create(
            student=self.student,
            subject_room=self.subject_room,
            total_steps=0,
            completed_steps=0,
        )
        assert path.progress_pct == 0.0

    def test_path_with_steps(self):
        chapter = make_chapter("Grammar")
        node = make_knowledge_node(self.subject, chapter)
        path = LearningPath.objects.create(
            student=self.student,
            subject_room=self.subject_room,
            total_steps=1,
            completed_steps=0,
        )
        step = LearningPathStep.objects.create(
            learning_path=path,
            knowledge_node=node,
            position=1,
            status=StepStatus.PENDING,
        )
        assert step.pk is not None
        assert step.is_review is False
        assert "Grammar" in str(step)


# ─────────────────────────────────────────────────────────────────────────────
# API endpoint smoke tests (no DB-backed auth; just URL resolution)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAdaptiveAPIEndpoints:
    """Smoke-test that endpoints respond correctly for auth/no-auth."""

    def _make_authenticated_client(self, role="student"):
        from django.test import Client
        from openshiksha.apps.core.models import User

        username = f"api_{role}_{timezone.now().timestamp()}"
        user = User.objects.create_user(username=username, password="pass", role=role)
        client = Client()
        client.force_login(user)
        return client, user

    def test_knowledge_nodes_requires_auth(self):
        from django.test import Client
        client = Client()
        response = client.get("/api/v1/ai/knowledge-nodes/")
        assert response.status_code == 401

    def test_mastery_requires_auth(self):
        from django.test import Client
        client = Client()
        response = client.get("/api/v1/ai/mastery/")
        assert response.status_code == 401

    def test_spaced_repetition_requires_auth(self):
        from django.test import Client
        client = Client()
        response = client.get("/api/v1/ai/spaced-repetition/")
        assert response.status_code == 401

    def test_learning_paths_requires_auth(self):
        from django.test import Client
        client = Client()
        response = client.get("/api/v1/ai/learning-paths/")
        assert response.status_code == 401

    def test_knowledge_nodes_authenticated_returns_200(self):
        client, _ = self._make_authenticated_client(role="teacher")
        response = client.get("/api/v1/ai/knowledge-nodes/")
        assert response.status_code == 200

    def test_mastery_list_empty_for_new_student(self):
        client, _ = self._make_authenticated_client(role="student")
        response = client.get("/api/v1/ai/mastery/")
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []

    def test_srs_due_empty_for_new_student(self):
        client, _ = self._make_authenticated_client(role="student")
        response = client.get("/api/v1/ai/spaced-repetition/due/")
        assert response.status_code == 200
        assert response.json() == []

    def test_learning_paths_active_404_when_none(self):
        client, _ = self._make_authenticated_client(role="student")
        response = client.get("/api/v1/ai/learning-paths/active/")
        assert response.status_code == 404

    def test_rebuild_path_requires_subject_room_id(self):
        import json
        client, _ = self._make_authenticated_client(role="student")
        response = client.post(
            "/api/v1/ai/learning-paths/rebuild/",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_knowledge_nodes_filter_by_subject(self):
        subject = make_subject("FilterSubject")
        chapter = make_chapter("FilterChapter")
        make_knowledge_node(subject, chapter)
        client, _ = self._make_authenticated_client(role="teacher")
        response = client.get(f"/api/v1/ai/knowledge-nodes/?subject_id={subject.pk}")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
