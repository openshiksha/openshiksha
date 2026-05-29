"""
Tests for the School Admin API (P4 backend).

Covers:
- IsSchoolAdmin permission + school-scoped ClassRoom CRUD
- Cross-tenant isolation (the critical multi-tenancy guard)
- Classroom enroll / unenroll (validate-and-report)
- Admin SubjectRoom create + enroll
- School summary + enrollment-picker lists
"""

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.test import APIClient

from openshiksha.apps.core.models import Board, ClassRoom, School, Standard, Subject, SubjectRoom, User, UserRole


def auth(user):
    client = APIClient()
    token = RefreshToken.for_user(user).access_token
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def rows(response):
    """Unwrap a (possibly paginated) list response into a plain list of items."""
    data = response.json()
    return data["results"] if isinstance(data, dict) and "results" in data else data


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=7)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Mathematics")


@pytest.fixture
def school_a(db, board):
    return School.objects.create(name="School A", board=board)


@pytest.fixture
def school_b(db, board):
    return School.objects.create(name="School B", board=board)


@pytest.fixture
def admin_a(db, school_a):
    return User.objects.create_user(username="admin_a", password="pw", role=UserRole.ADMIN, school=school_a)


@pytest.fixture
def admin_b(db, school_b):
    return User.objects.create_user(username="admin_b", password="pw", role=UserRole.ADMIN, school=school_b)


@pytest.fixture
def teacher_a(db, school_a):
    return User.objects.create_user(
        username="teacher_a", password="pw", role=UserRole.TEACHER, school=school_a, first_name="Tara"
    )


@pytest.fixture
def teacher_b(db, school_b):
    return User.objects.create_user(username="teacher_b", password="pw", role=UserRole.TEACHER, school=school_b)


@pytest.fixture
def student_a(db, school_a):
    return User.objects.create_user(
        username="student_a", password="pw", role=UserRole.STUDENT, school=school_a, first_name="Sam"
    )


@pytest.fixture
def student_a2(db, school_a):
    return User.objects.create_user(username="student_a2", password="pw", role=UserRole.STUDENT, school=school_a)


@pytest.fixture
def student_b(db, school_b):
    return User.objects.create_user(username="student_b", password="pw", role=UserRole.STUDENT, school=school_b)


@pytest.fixture
def classroom_a(db, school_a, standard, teacher_a):
    return ClassRoom.objects.create(
        school=school_a, standard=standard, division="A", class_teacher=teacher_a, academic_year="2025-26"
    )


@pytest.fixture
def classroom_b(db, school_b, standard):
    return ClassRoom.objects.create(school=school_b, standard=standard, division="A", academic_year="2025-26")


# ── Permission / role guards ──────────────────────────────────────────────


@pytest.mark.django_db
def test_non_admin_forbidden(teacher_a, student_a):
    for user in (teacher_a, student_a):
        res = auth(user).get("/api/v1/classrooms/")
        assert res.status_code == 403


@pytest.mark.django_db
def test_unauthenticated_forbidden():
    res = APIClient().get("/api/v1/classrooms/")
    assert res.status_code == 401


# ── School scoping / tenancy ──────────────────────────────────────────────


@pytest.mark.django_db
def test_admin_lists_only_own_school_classrooms(admin_a, classroom_a, classroom_b):
    res = auth(admin_a).get("/api/v1/classrooms/")
    assert res.status_code == 200
    ids = [c["id"] for c in rows(res)]
    assert classroom_a.id in ids
    assert classroom_b.id not in ids


@pytest.mark.django_db
def test_admin_cannot_mutate_other_school_classroom(admin_b, classroom_a):
    """The tenancy guard: school-B admin gets 404 on school-A's classroom."""
    client = auth(admin_b)
    assert client.get(f"/api/v1/classrooms/{classroom_a.id}/").status_code == 404
    assert client.patch(f"/api/v1/classrooms/{classroom_a.id}/", {"division": "Z"}, format="json").status_code == 404
    assert client.delete(f"/api/v1/classrooms/{classroom_a.id}/").status_code == 404


@pytest.mark.django_db
def test_create_classroom_forces_own_school(admin_a, school_b, standard):
    res = auth(admin_a).post(
        "/api/v1/classrooms/",
        {"standard": standard.id, "division": "B", "academic_year": "2025-26", "school": school_b.id},
        format="json",
    )
    assert res.status_code == 201
    classroom = ClassRoom.objects.get(id=res.json()["id"])
    assert classroom.school_id == admin_a.school_id  # body "school" ignored


@pytest.mark.django_db
def test_create_classroom_rejects_foreign_teacher(admin_a, standard, teacher_b):
    res = auth(admin_a).post(
        "/api/v1/classrooms/",
        {"standard": standard.id, "division": "C", "academic_year": "2025-26", "class_teacher": teacher_b.id},
        format="json",
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_create_duplicate_classroom_returns_400(admin_a, classroom_a, standard):
    res = auth(admin_a).post(
        "/api/v1/classrooms/",
        {"standard": standard.id, "division": "A", "academic_year": "2025-26"},
        format="json",
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_soft_delete_classroom(admin_a, classroom_a):
    res = auth(admin_a).delete(f"/api/v1/classrooms/{classroom_a.id}/")
    assert res.status_code == 204
    classroom_a.refresh_from_db()
    assert classroom_a.is_active is False
    # default list hides inactive
    listed = rows(auth(admin_a).get("/api/v1/classrooms/"))
    assert classroom_a.id not in [c["id"] for c in listed]
    # escape hatch surfaces it
    included = rows(auth(admin_a).get("/api/v1/classrooms/?include_inactive=true"))
    assert classroom_a.id in [c["id"] for c in included]


# ── Enrollment ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_enroll_students_validate_and_report(admin_a, classroom_a, student_a, student_a2, student_b):
    res = auth(admin_a).post(
        f"/api/v1/classrooms/{classroom_a.id}/enroll/",
        {"student_ids": [student_a.id, student_a2.id, student_b.id, 99999]},
        format="json",
    )
    assert res.status_code == 200
    data = res.json()
    assert set(data["enrolled"]) == {student_a.id, student_a2.id}
    assert student_b.id in data["invalid_ids"] and 99999 in data["invalid_ids"]
    assert data["student_count"] == 2


@pytest.mark.django_db
def test_unenroll_students(admin_a, classroom_a, student_a):
    classroom_a.students.add(student_a)
    res = auth(admin_a).post(
        f"/api/v1/classrooms/{classroom_a.id}/unenroll/",
        {"student_ids": [student_a.id]},
        format="json",
    )
    assert res.status_code == 200
    assert res.json()["student_count"] == 0


# ── SubjectRoom admin path ────────────────────────────────────────────────


@pytest.mark.django_db
def test_admin_create_subject_room(admin_a, classroom_a, subject, teacher_a):
    res = auth(admin_a).post(
        "/api/v1/subject-rooms/",
        {"classroom": classroom_a.id, "subject": subject.id, "teacher": teacher_a.id},
        format="json",
    )
    assert res.status_code == 201, res.content
    assert SubjectRoom.objects.filter(classroom=classroom_a, subject=subject).exists()


@pytest.mark.django_db
def test_admin_subject_room_rejects_foreign_classroom(admin_a, classroom_b, subject, teacher_a):
    res = auth(admin_a).post(
        "/api/v1/subject-rooms/",
        {"classroom": classroom_b.id, "subject": subject.id, "teacher": teacher_a.id},
        format="json",
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_subject_room_duplicate_rejected(admin_a, classroom_a, subject, teacher_a):
    SubjectRoom.objects.create(classroom=classroom_a, subject=subject, teacher=teacher_a)
    res = auth(admin_a).post(
        "/api/v1/subject-rooms/",
        {"classroom": classroom_a.id, "subject": subject.id, "teacher": teacher_a.id},
        format="json",
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_admin_enroll_subject_room(admin_a, classroom_a, subject, teacher_a, student_a):
    room = SubjectRoom.objects.create(classroom=classroom_a, subject=subject, teacher=teacher_a)
    res = auth(admin_a).post(
        f"/api/v1/subject-rooms/{room.id}/enroll/",
        {"student_ids": [student_a.id]},
        format="json",
    )
    assert res.status_code == 200
    assert res.json()["student_count"] == 1


# ── Roster / summary reads ────────────────────────────────────────────────


@pytest.mark.django_db
def test_school_summary_counts(admin_a, classroom_a, subject, teacher_a, student_a, student_a2):
    SubjectRoom.objects.create(classroom=classroom_a, subject=subject, teacher=teacher_a)
    res = auth(admin_a).get("/api/v1/classrooms/summary/")
    assert res.status_code == 200
    data = res.json()
    assert data["school"]["id"] == admin_a.school_id
    assert data["classroom_count"] == 1
    assert data["teacher_count"] == 1
    assert data["student_count"] == 2
    assert data["active_subject_rooms"] == 1


@pytest.mark.django_db
def test_admin_user_lists_scoped_to_school(admin_a, teacher_a, teacher_b, student_a, student_b):
    client = auth(admin_a)
    teachers = client.get("/api/v1/users/school-teachers/").json()
    assert teacher_a.id in [t["id"] for t in teachers]
    assert teacher_b.id not in [t["id"] for t in teachers]

    students = client.get("/api/v1/users/school-students/").json()
    assert student_a.id in [s["id"] for s in students]
    assert student_b.id not in [s["id"] for s in students]


@pytest.mark.django_db
def test_classroom_includes_student_count(admin_a, classroom_a, student_a):
    classroom_a.students.add(student_a)
    res = auth(admin_a).get("/api/v1/classrooms/")
    row = next(c for c in rows(res) if c["id"] == classroom_a.id)
    assert row["student_count"] == 1
