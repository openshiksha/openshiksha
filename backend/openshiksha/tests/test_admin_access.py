"""The Django admin (/django-admin/) is restricted to superusers only."""

import pytest

from django.test import Client

from openshiksha.apps.core.models import User, UserRole


@pytest.mark.django_db
def test_django_admin_blocks_non_superuser_staff():
    """A school 'admin' (is_staff but not superuser) must not reach Django admin."""
    staff = User.objects.create_user(username="staffy", password="pw12345", role=UserRole.ADMIN)
    staff.is_staff = True
    staff.save()

    client = Client()
    client.force_login(staff)
    resp = client.get("/django-admin/")

    # has_permission() is False -> the admin bounces to its own login page.
    assert resp.status_code == 302
    assert "/django-admin/login" in resp.headers.get("Location", "")


@pytest.mark.django_db
def test_django_admin_allows_superuser():
    su = User.objects.create_user(username="super", password="pw12345", role=UserRole.ADMIN)
    su.is_staff = True
    su.is_superuser = True
    su.save()

    client = Client()
    client.force_login(su)
    resp = client.get("/django-admin/")

    assert resp.status_code == 200
