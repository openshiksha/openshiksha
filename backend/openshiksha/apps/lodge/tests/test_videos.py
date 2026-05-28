"""Tests for the lodge video content endpoints."""

import pytest

from django.urls import reverse
from rest_framework.test import APIClient

from openshiksha.apps.core.models import Chapter, Standard, Subject, User, UserRole
from openshiksha.apps.lodge.models import Video


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def standard(db):
    return Standard.objects.create(number=10)


@pytest.fixture
def subject(db):
    return Subject.objects.create(name="Mathematics")


@pytest.fixture
def chapter(db, subject, standard):
    return Chapter.objects.create(name="Quadratic Equations", subject=subject, standard=standard)


@pytest.fixture
def other_chapter(db, subject, standard):
    return Chapter.objects.create(name="Trigonometry", subject=subject, standard=standard)


@pytest.fixture
def teacher(db):
    return User.objects.create_user(username="teach", password="pw12345678", role=UserRole.TEACHER)


@pytest.fixture
def student(db):
    return User.objects.create_user(username="stud", password="pw12345678", role=UserRole.STUDENT)


@pytest.mark.django_db
def test_list_videos_filtered_by_chapter(api_client, student, chapter, other_chapter):
    Video.objects.create(chapter=chapter, title="A", embed_url="https://x/a", order=1)
    Video.objects.create(chapter=chapter, title="B", embed_url="https://x/b", order=0)
    Video.objects.create(chapter=other_chapter, title="C", embed_url="https://x/c")

    api_client.force_authenticate(student)
    response = api_client.get(reverse("video-list"), {"chapter": chapter.id})

    assert response.status_code == 200
    results = response.data["results"]
    assert len(results) == 2
    # ordering by `order` ascending
    assert [v["title"] for v in results] == ["B", "A"]


@pytest.mark.django_db
def test_students_do_not_see_inactive_videos(api_client, student, chapter):
    Video.objects.create(chapter=chapter, title="Live", embed_url="https://x/live", is_active=True)
    Video.objects.create(chapter=chapter, title="Hidden", embed_url="https://x/hidden", is_active=False)

    api_client.force_authenticate(student)
    response = api_client.get(reverse("video-list"), {"chapter": chapter.id})

    titles = [v["title"] for v in response.data["results"]]
    assert titles == ["Live"]


@pytest.mark.django_db
def test_teacher_can_create_video(api_client, teacher, chapter):
    api_client.force_authenticate(teacher)
    response = api_client.post(
        reverse("video-list"),
        {"chapter": chapter.id, "title": "Intro", "embed_url": "https://youtube.com/embed/abc"},
        format="json",
    )
    assert response.status_code == 201
    video = Video.objects.get()
    assert video.created_by == teacher
    assert video.title == "Intro"


@pytest.mark.django_db
def test_student_cannot_create_video(api_client, student, chapter):
    api_client.force_authenticate(student)
    response = api_client.post(
        reverse("video-list"),
        {"chapter": chapter.id, "title": "Nope", "embed_url": "https://x/nope"},
        format="json",
    )
    assert response.status_code == 403
    assert Video.objects.count() == 0


@pytest.mark.django_db
def test_anonymous_cannot_list_videos(api_client, chapter):
    response = api_client.get(reverse("video-list"), {"chapter": chapter.id})
    assert response.status_code == 401


@pytest.mark.django_db
def test_teacher_can_delete_video(api_client, teacher, chapter):
    video = Video.objects.create(chapter=chapter, title="Del", embed_url="https://x/del")
    api_client.force_authenticate(teacher)
    response = api_client.delete(reverse("video-detail", args=[video.id]))
    assert response.status_code == 204
    assert Video.objects.count() == 0
