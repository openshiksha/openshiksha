"""
Tests for UserViewSet, SubjectRoomViewSet, and health check endpoint.

Covers:
- /api/users/me/ — authenticated user profile
- /api/subject-rooms/ — role-based CRUD and visibility
- /api/v1/health/ — service health check
- /api/auth/login/ — JWT token issuance
"""

import pytest

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from openshiksha.apps.core.models import (
    Board,
    Chapter,
    ClassRoom,
    School,
    Standard,
    Subject,
    SubjectRoom,
    User,
    UserRole,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def board(db):
    return Board.objects.create(name="CBSE")


@pytest.fixture
def school(db, board):
    return School.objects.create(name="Test School", board=board)


@pytest.fixture
def other_school(db, board):
    return School.objects.create(name="Other School", board=board)


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=9)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Mathematics")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Algebra", subject=subject, standard=standard, order=1)


@pytest.fixture
def classroom(db, school, standard):
    return ClassRoom.objects.create(school=school, standard=standard, division="A", academic_year="2025-26")


@pytest.fixture
def other_classroom(db, other_school, standard):
    return ClassRoom.objects.create(school=other_school, standard=standard, division="B", academic_year="2025-26")


@pytest.fixture
def teacher(db, school):
    return User.objects.create_user(username="teacher_core", password="pass", role=UserRole.TEACHER, school=school)


@pytest.fixture
def other_teacher(db, school):
    return User.objects.create_user(
        username="other_teacher_core", password="pass", role=UserRole.TEACHER, school=school
    )


@pytest.fixture
def student(db, school):
    return User.objects.create_user(username="student_core", password="pass", role=UserRole.STUDENT, school=school)


@pytest.fixture
def admin_user(db, school):
    return User.objects.create_user(username="admin_core", password="pass", role=UserRole.ADMIN, school=school)


@pytest.fixture
def other_school_admin(db, other_school):
    return User.objects.create_user(
        username="other_admin_core", password="pass", role=UserRole.ADMIN, school=other_school
    )


@pytest.fixture
def subject_room(db, classroom, subject, teacher, student):
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def other_subject_room(db, other_classroom, subject, other_teacher):
    """A room in a different school, taught by a different teacher."""
    return SubjectRoom.objects.create(classroom=other_classroom, subject=subject, teacher=other_teacher)


# ---------------------------------------------------------------------------
# UserViewSet: /api/users/me/
# ---------------------------------------------------------------------------


class TestUserMeEndpoint:
    def test_unauthenticated_cannot_access_me(self, api_client):
        url = reverse("user-me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_teacher_gets_own_profile(self, api_client, teacher):
        api_client.force_authenticate(user=teacher)
        url = reverse("user-me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == teacher.username
        assert response.data["role"] == UserRole.TEACHER

    def test_authenticated_student_gets_own_profile(self, api_client, student):
        api_client.force_authenticate(user=student)
        url = reverse("user-me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == student.username
        assert response.data["role"] == UserRole.STUDENT

    def test_me_response_includes_expected_fields(self, api_client, teacher):
        api_client.force_authenticate(user=teacher)
        url = reverse("user-me")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        for field in ["id", "username", "email", "first_name", "last_name", "role"]:
            assert field in response.data, f"Expected field '{field}' in /users/me/ response"

    def test_me_does_not_expose_password(self, api_client, teacher):
        api_client.force_authenticate(user=teacher)
        url = reverse("user-me")
        response = api_client.get(url)
        assert "password" not in response.data

    def test_user_can_change_password(self, api_client, teacher):
        api_client.force_authenticate(user=teacher)
        url = reverse("user-change-password")
        response = api_client.post(
            url,
            {"current_password": "pass", "new_password": "new-secure-pass-123"},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK

        teacher.refresh_from_db()
        assert teacher.check_password("new-secure-pass-123")

    def test_change_password_rejects_wrong_current_password(self, api_client, teacher):
        api_client.force_authenticate(user=teacher)
        url = reverse("user-change-password")
        response = api_client.post(
            url,
            {"current_password": "wrong", "new_password": "new-secure-pass-123"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "current_password" in response.data


# ---------------------------------------------------------------------------
# Authentication: JWT login
# ---------------------------------------------------------------------------


class TestAuthEndpoints:
    def test_valid_credentials_return_tokens(self, api_client, teacher):
        url = reverse("token_obtain_pair")
        response = api_client.post(url, {"username": "teacher_core", "password": "pass"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

    def test_invalid_password_is_rejected(self, api_client, teacher):
        url = reverse("token_obtain_pair")
        response = api_client.post(url, {"username": "teacher_core", "password": "wrong"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_user_is_rejected(self, api_client, db):
        url = reverse("token_obtain_pair")
        response = api_client.post(url, {"username": "ghost", "password": "pass"}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh(self, api_client, teacher):
        login_url = reverse("token_obtain_pair")
        refresh_url = reverse("token_refresh")
        login_response = api_client.post(login_url, {"username": "teacher_core", "password": "pass"}, format="json")
        refresh_token = login_response.data["refresh"]
        response = api_client.post(refresh_url, {"refresh": refresh_token}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data


# ---------------------------------------------------------------------------
# Health check: /api/v1/health/
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_health_returns_200_when_healthy(self, api_client):
        url = reverse("health_check")
        response = api_client.get(url)
        # Accept 200 (healthy) or 503 (unhealthy but endpoint is up)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]

    def test_health_response_includes_status_field(self, api_client):
        url = reverse("health_check")
        response = api_client.get(url)
        assert "status" in response.data

    def test_health_response_includes_database_field(self, api_client):
        url = reverse("health_check")
        response = api_client.get(url)
        assert "database" in response.data

    def test_health_response_includes_cache_field(self, api_client):
        url = reverse("health_check")
        response = api_client.get(url)
        assert "cache" in response.data

    def test_health_accessible_without_authentication(self, api_client):
        """Health endpoint must be public — no auth token required."""
        url = reverse("health_check")
        response = api_client.get(url)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED
        assert response.status_code != status.HTTP_403_FORBIDDEN

    def test_health_returns_healthy_with_real_db(self, api_client, db):
        """With a real test database available, the health endpoint should report healthy."""
        url = reverse("health_check")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "healthy"
        assert response.data["database"] == "connected"


# ---------------------------------------------------------------------------
# SubjectRoomViewSet: /api/subject-rooms/
# ---------------------------------------------------------------------------


class TestSubjectRoomVisibility:
    def test_unauthenticated_cannot_list(self, api_client):
        url = reverse("subjectroom-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_teacher_sees_own_rooms_only(self, api_client, teacher, other_teacher, subject_room, other_subject_room):
        api_client.force_authenticate(user=teacher)
        url = reverse("subjectroom-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert subject_room.pk in ids
        assert other_subject_room.pk not in ids

    def test_student_sees_enrolled_rooms_only(self, api_client, student, subject_room, other_subject_room):
        # student is enrolled in subject_room but not other_subject_room
        api_client.force_authenticate(user=student)
        url = reverse("subjectroom-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert subject_room.pk in ids
        assert other_subject_room.pk not in ids

    def test_admin_sees_rooms_for_own_school_only(
        self, api_client, admin_user, other_school_admin, subject_room, other_subject_room
    ):
        api_client.force_authenticate(user=admin_user)
        url = reverse("subjectroom-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert subject_room.pk in ids
        assert other_subject_room.pk not in ids

    def test_other_school_admin_sees_only_their_rooms(
        self, api_client, other_school_admin, subject_room, other_subject_room
    ):
        api_client.force_authenticate(user=other_school_admin)
        url = reverse("subjectroom-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert other_subject_room.pk in ids
        assert subject_room.pk not in ids

    def test_student_cannot_see_inactive_rooms(self, api_client, student, subject_room):
        subject_room.is_active = False
        subject_room.save()
        api_client.force_authenticate(user=student)
        url = reverse("subjectroom-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        ids = [r["id"] for r in response.data["results"]]
        assert subject_room.pk not in ids


class TestSubjectRoomPermissions:
    def test_teacher_can_create_subject_room(self, api_client, teacher, classroom, subject):
        api_client.force_authenticate(user=teacher)
        url = reverse("subjectroom-list")
        data = {"classroom": classroom.pk, "subject": subject.pk, "teacher": teacher.pk}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    def test_student_cannot_create_subject_room(self, api_client, student, classroom, subject, teacher):
        api_client.force_authenticate(user=student)
        url = reverse("subjectroom-list")
        data = {"classroom": classroom.pk, "subject": subject.pk, "teacher": teacher.pk}
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_teacher_can_update_own_room(self, api_client, teacher, subject_room):
        api_client.force_authenticate(user=teacher)
        url = reverse("subjectroom-detail", kwargs={"pk": subject_room.pk})
        response = api_client.patch(url, {"is_active": True}, format="json")
        assert response.status_code == status.HTTP_200_OK

    def test_student_cannot_update_subject_room(self, api_client, student, subject_room):
        api_client.force_authenticate(user=student)
        url = reverse("subjectroom-detail", kwargs={"pk": subject_room.pk})
        response = api_client.patch(url, {"is_active": False}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_teacher_cannot_delete_other_teachers_room(self, api_client, other_teacher, subject_room):
        """other_teacher does not own subject_room — it should be invisible to them, so 404."""
        api_client.force_authenticate(user=other_teacher)
        url = reverse("subjectroom-detail", kwargs={"pk": subject_room.pk})
        response = api_client.delete(url)
        # Room is not in other_teacher's queryset so should be 404
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_teacher_can_retrieve_own_room(self, api_client, teacher, subject_room):
        api_client.force_authenticate(user=teacher)
        url = reverse("subjectroom-detail", kwargs={"pk": subject_room.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == subject_room.pk

    def test_response_includes_student_count(self, api_client, teacher, subject_room):
        api_client.force_authenticate(user=teacher)
        url = reverse("subjectroom-detail", kwargs={"pk": subject_room.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "student_count" in response.data
        assert response.data["student_count"] == 1


# ---------------------------------------------------------------------------
# QuestionViewSet: content search
# ---------------------------------------------------------------------------


class TestQuestionContentSearch:
    def test_search_by_subpart_text_returns_matching_question(
        self, db, api_client, teacher, school, standard, subject, chapter
    ):
        """?search=photosynthesis should find a question whose subpart contains that word."""
        from openshiksha.apps.core.models import Question, QuestionSubpart

        question = Question.objects.create(
            school=school,
            standard=standard,
            subject=subject,
            chapter=chapter,
            question_type="fill_blank",
        )
        QuestionSubpart.objects.create(
            question=question,
            index=0,
            question_text="The process of photosynthesis occurs in chloroplasts.",
            correct_answer={"answer": "chloroplasts"},
        )

        api_client.force_authenticate(user=teacher)
        response = api_client.get("/api/v1/questions/", {"search": "photosynthesis"})

        assert response.status_code == status.HTTP_200_OK
        ids = [q["id"] for q in response.data["results"]]
        assert question.id in ids

    def test_search_by_tag_name_returns_matching_question(
        self, db, api_client, teacher, school, standard, subject, chapter
    ):
        """?search=<tag name> should find a question with that tag."""
        from openshiksha.apps.core.models import Question, QuestionTag

        tag = QuestionTag.objects.create(name="quadratic-equations", tag_type="topic")
        question = Question.objects.create(
            school=school,
            standard=standard,
            subject=subject,
            chapter=chapter,
            question_type="mcq",
        )
        question.tags.add(tag)

        api_client.force_authenticate(user=teacher)
        response = api_client.get("/api/v1/questions/", {"search": "quadratic-equations"})

        assert response.status_code == status.HTTP_200_OK
        ids = [q["id"] for q in response.data["results"]]
        assert question.id in ids


# ---------------------------------------------------------------------------
# Question image_url field tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestQuestionSubpartImageUrl:
    def test_image_url_exposed_in_question_api(self, api_client, teacher, school, standard, subject, chapter):
        from openshiksha.apps.core.models import Question, QuestionSubpart

        question = Question.objects.create(
            school=school,
            standard=standard,
            subject=subject,
            chapter=chapter,
            question_type="mcq",
        )
        QuestionSubpart.objects.create(
            question=question,
            index=0,
            question_text="What is H2O?",
            correct_answer={"answer": "A"},
            image_url="https://example.com/diagram.png",
        )

        api_client.force_authenticate(user=teacher)
        response = api_client.get(f"/api/v1/questions/{question.id}/")

        assert response.status_code == 200
        subpart = response.data["subparts"][0]
        assert subpart["image_url"] == "https://example.com/diagram.png"

    def test_image_url_default_empty_string(self, api_client, teacher, school, standard, subject, chapter):
        from openshiksha.apps.core.models import Question, QuestionSubpart

        question = Question.objects.create(
            school=school,
            standard=standard,
            subject=subject,
            chapter=chapter,
            question_type="fill_blank",
        )
        QuestionSubpart.objects.create(
            question=question,
            index=0,
            question_text="Fill in the blank.",
            correct_answer={"answer": "water"},
        )

        api_client.force_authenticate(user=teacher)
        response = api_client.get(f"/api/v1/questions/{question.id}/")

        assert response.status_code == 200
        subpart = response.data["subparts"][0]
        assert subpart["image_url"] == ""

    @override_settings(MEDIA_ROOT="/tmp/openshiksha-test-media")
    def test_teacher_can_upload_question_image(self, api_client, teacher):
        api_client.force_authenticate(user=teacher)
        upload = SimpleUploadedFile(
            "diagram.png",
            b"\x89PNG\r\n\x1a\n",
            content_type="image/png",
        )

        response = api_client.post("/api/v1/questions/upload-image/", {"image": upload}, format="multipart")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["image_url"].startswith("http://testserver/media/question_uploads/")
        assert response.data["image_url"].endswith(".png")

    def test_student_cannot_upload_question_image(self, api_client, student):
        api_client.force_authenticate(user=student)
        upload = SimpleUploadedFile("diagram.png", b"png", content_type="image/png")

        response = api_client.post("/api/v1/questions/upload-image/", {"image": upload}, format="multipart")

        assert response.status_code == status.HTTP_403_FORBIDDEN
