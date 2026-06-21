"""
Tests for the TeacherWidget model (IW-9-backend, model-only slice).

DRF endpoints + serializer + scene-schema validation land in IW-9 proper
after IW-1/IW-2 ship; this slice ships the table.
"""

import pytest

from openshiksha.apps.core.models import Board, School, TeacherWidget, TeacherWidgetVisibility, User, UserRole


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Demo School", board=board)


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="t1", password="pw", role=UserRole.TEACHER, school=school)


class TestTeacherWidget:
    def test_create_with_school(self, db, school, teacher):
        w = TeacherWidget.objects.create(
            name="Slider+Plot demo",
            school=school,
            created_by=teacher,
            scene={"primitives": [], "bindings": [], "formulas": []},
        )
        assert w.visibility == TeacherWidgetVisibility.PERSONAL
        assert w.scene_version == 1
        assert str(w) == "Slider+Plot demo (personal)"

    def test_create_personal_widget_without_school(self, db, teacher):
        # Personal widgets are allowed without a school (open / unaffiliated teachers).
        w = TeacherWidget.objects.create(name="My toy", school=None, created_by=teacher)
        assert w.school is None
        assert w.visibility == TeacherWidgetVisibility.PERSONAL
        assert w.scene == {}

    def test_visibility_choices(self, db, school, teacher):
        w = TeacherWidget.objects.create(
            name="Shared",
            school=school,
            created_by=teacher,
            visibility=TeacherWidgetVisibility.SCHOOL,
        )
        assert w.visibility == "school"
        assert str(w) == "Shared (school)"

    def test_ordering_by_updated_at_desc(self, db, school, teacher):
        first = TeacherWidget.objects.create(name="A", school=school, created_by=teacher)
        second = TeacherWidget.objects.create(name="B", school=school, created_by=teacher)
        ids = list(TeacherWidget.objects.values_list("id", flat=True))
        assert ids[0] == second.id
        assert ids[1] == first.id
