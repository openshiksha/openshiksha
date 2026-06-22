"""Tests for GET /api/v1/ai/practice-plans/today/."""

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from openshiksha.apps.core.models import User, UserRole


@pytest.mark.django_db
def test_today_returns_204_when_no_plan():
    """A student with no plan for today gets 204 (empty state), not 404."""
    student = User.objects.create_user(username="pp_student", password="pw12345", role=UserRole.STUDENT)
    client = APIClient()
    client.force_authenticate(user=student)

    resp = client.get("/api/v1/ai/practice-plans/today/")

    assert resp.status_code == status.HTTP_204_NO_CONTENT
    assert not resp.data


@pytest.mark.django_db
def test_today_forbidden_for_non_student():
    teacher = User.objects.create_user(username="pp_teacher", password="pw12345", role=UserRole.TEACHER)
    client = APIClient()
    client.force_authenticate(user=teacher)

    resp = client.get("/api/v1/ai/practice-plans/today/")

    assert resp.status_code == status.HTTP_403_FORBIDDEN
