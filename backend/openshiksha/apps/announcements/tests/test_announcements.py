"""Tests for the announcements endpoints and visibility rules."""

import pytest

from django.urls import reverse
from rest_framework.test import APIClient

from openshiksha.apps.announcements.models import Announcement
from openshiksha.apps.core.models import Board, ClassRoom, School, Standard, Subject, SubjectRoom, User, UserRole


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def teacher(db):
    return User.objects.create_user(username="teach", password="pw12345678", role=UserRole.TEACHER)


@pytest.fixture
def other_teacher(db):
    return User.objects.create_user(username="teach2", password="pw12345678", role=UserRole.TEACHER)


@pytest.fixture
def student(db):
    return User.objects.create_user(username="stud", password="pw12345678", role=UserRole.STUDENT)


@pytest.fixture
def outside_student(db):
    return User.objects.create_user(username="stud2", password="pw12345678", role=UserRole.STUDENT)


@pytest.fixture
def parent(db, student):
    p = User.objects.create_user(username="par", password="pw12345678", role=UserRole.PARENT)
    p.children.add(student)
    return p


@pytest.fixture
def subject_room(db, teacher, student):
    board = Board.objects.create(name="CBSE")
    school = School.objects.create(name="Test School", board=board)
    standard = Standard.objects.create(number=10)
    classroom = ClassRoom.objects.create(
        school=school,
        standard=standard,
        division="A",
        class_teacher=teacher,
        academic_year="2025-26",
    )
    subject = Subject.objects.create(name="Mathematics")
    room = SubjectRoom.objects.create(classroom=classroom, subject=subject, teacher=teacher)
    room.students.add(student)
    return room


@pytest.fixture
def url():
    return reverse("announcement-list")


@pytest.mark.django_db
def test_teacher_can_post_to_own_room(api_client, url, teacher, subject_room):
    api_client.force_authenticate(teacher)
    response = api_client.post(
        url,
        {"subject_room": subject_room.id, "message": "Quiz on Friday."},
        format="json",
    )
    assert response.status_code == 201
    ann = Announcement.objects.get()
    assert ann.author == teacher
    assert ann.message == "Quiz on Friday."


@pytest.mark.django_db
def test_teacher_cannot_post_to_room_they_dont_teach(api_client, url, other_teacher, subject_room):
    api_client.force_authenticate(other_teacher)
    response = api_client.post(
        url,
        {"subject_room": subject_room.id, "message": "Not my class."},
        format="json",
    )
    assert response.status_code == 400
    assert Announcement.objects.count() == 0


@pytest.mark.django_db
def test_student_cannot_post(api_client, url, student, subject_room):
    api_client.force_authenticate(student)
    response = api_client.post(
        url,
        {"subject_room": subject_room.id, "message": "Hi"},
        format="json",
    )
    assert response.status_code in (400, 403)
    assert Announcement.objects.count() == 0


@pytest.mark.django_db
def test_enrolled_student_sees_announcement(api_client, url, teacher, student, subject_room):
    Announcement.objects.create(subject_room=subject_room, author=teacher, message="Hello class")
    api_client.force_authenticate(student)
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["message"] == "Hello class"


@pytest.mark.django_db
def test_outside_student_does_not_see_announcement(api_client, url, teacher, outside_student, subject_room):
    Announcement.objects.create(subject_room=subject_room, author=teacher, message="Hello class")
    api_client.force_authenticate(outside_student)
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data["results"]) == 0


@pytest.mark.django_db
def test_parent_sees_childs_room_announcement(api_client, url, teacher, parent, subject_room):
    Announcement.objects.create(subject_room=subject_room, author=teacher, message="Parents note")
    api_client.force_authenticate(parent)
    response = api_client.get(url)
    assert response.status_code == 200
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_inactive_announcement_hidden(api_client, url, teacher, student, subject_room):
    Announcement.objects.create(subject_room=subject_room, author=teacher, message="Old", is_active=False)
    api_client.force_authenticate(student)
    response = api_client.get(url)
    assert len(response.data["results"]) == 0


@pytest.mark.django_db
def test_author_can_delete_own_announcement(api_client, teacher, subject_room):
    ann = Announcement.objects.create(subject_room=subject_room, author=teacher, message="Delete me")
    api_client.force_authenticate(teacher)
    response = api_client.delete(reverse("announcement-detail", args=[ann.id]))
    assert response.status_code == 204
    assert Announcement.objects.count() == 0
