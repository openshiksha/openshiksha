"""Tests for the public enquiry endpoint."""

import pytest

from django.core import mail
from django.urls import reverse
from rest_framework.test import APIClient

from openshiksha.apps.concierge.models import Enquirer


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def url():
    return reverse("enquire")


@pytest.mark.django_db
def test_enquiry_creates_record(api_client, url):
    payload = {
        "name": "Asha Rao",
        "school": "Sunrise Public School",
        "email": "asha@sunrise.edu",
        "phone": "9876543210",
        "message": "Interested in a pilot for grades 6-8.",
    }
    response = api_client.post(url, payload, format="json")

    assert response.status_code == 201
    assert Enquirer.objects.count() == 1
    enquirer = Enquirer.objects.get()
    assert enquirer.name == "Asha Rao"
    assert enquirer.school == "Sunrise Public School"


@pytest.mark.django_db
def test_enquiry_is_public_no_auth_required(api_client, url):
    response = api_client.post(
        url,
        {"name": "X", "school": "Y", "email": "x@y.com"},
        format="json",
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_enquiry_phone_and_message_optional(api_client, url):
    response = api_client.post(
        url,
        {"name": "Min", "school": "Org", "email": "min@org.com"},
        format="json",
    )
    assert response.status_code == 201
    enquirer = Enquirer.objects.get()
    assert enquirer.phone == ""
    assert enquirer.message == ""


@pytest.mark.django_db
def test_enquiry_requires_name_school_email(api_client, url):
    response = api_client.post(url, {"name": "Only Name"}, format="json")
    assert response.status_code == 400
    details = response.data.get("details", response.data)
    assert "school" in details
    assert "email" in details


@pytest.mark.django_db
def test_enquiry_invalid_email_rejected(api_client, url):
    response = api_client.post(
        url,
        {"name": "A", "school": "B", "email": "not-an-email"},
        format="json",
    )
    assert response.status_code == 400
    details = response.data.get("details", response.data)
    assert "email" in details


@pytest.mark.django_db
def test_enquiry_notifies_admins(api_client, url, settings):
    settings.ADMINS = [("Admin", "admin@openshiksha.org")]
    api_client.post(
        url,
        {"name": "Notify", "school": "Notify School", "email": "n@s.com"},
        format="json",
    )
    assert len(mail.outbox) == 1
    assert "Notify School" in mail.outbox[0].subject
