"""
Tests for the build-info endpoint (OBS-2): /api/v1/version/.
"""

import pytest

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


class TestVersionEndpoint:
    def test_returns_all_four_keys(self, api_client):
        response = api_client.get(reverse("version_info"))
        assert response.status_code == status.HTTP_200_OK
        assert set(response.data.keys()) == {"version", "git_sha", "built_at", "environment"}

    @override_settings(APP_VERSION="9.9.9", ENVIRONMENT="prod")
    def test_reflects_settings(self, api_client):
        response = api_client.get(reverse("version_info"))
        assert response.data["version"] == "9.9.9"
        assert response.data["environment"] == "prod"

    def test_git_sha_and_built_at_default_to_unknown(self, api_client, monkeypatch):
        monkeypatch.delenv("GIT_SHA", raising=False)
        monkeypatch.delenv("BUILD_TIME", raising=False)
        response = api_client.get(reverse("version_info"))
        assert response.data["git_sha"] == "unknown"
        assert response.data["built_at"] == "unknown"

    def test_reads_build_env_vars(self, api_client, monkeypatch):
        monkeypatch.setenv("GIT_SHA", "abc123")
        monkeypatch.setenv("BUILD_TIME", "2026-06-25T00:00:00Z")
        response = api_client.get(reverse("version_info"))
        assert response.data["git_sha"] == "abc123"
        assert response.data["built_at"] == "2026-06-25T00:00:00Z"

    def test_accessible_without_authentication(self, api_client):
        response = api_client.get(reverse("version_info"))
        assert response.status_code not in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
