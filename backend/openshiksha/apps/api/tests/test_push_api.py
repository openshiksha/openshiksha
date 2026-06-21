"""
API + helper tests for Web Push (MPN-2):
- subscribe creates a row and is idempotent on repeat (upsert by endpoint)
- unsubscribe deletes the caller's row
- vapid-public-key reflects settings
- send_web_push prunes stale (410) subscriptions and no-ops without a key
"""

from unittest import mock

import pytest

from rest_framework import status
from rest_framework.test import APIClient

from openshiksha.apps.core.models import PushSubscription, User, UserRole


@pytest.fixture
def student(db):
    return User.objects.create_user(username="push_api_student", password="pass", role=UserRole.STUDENT)


@pytest.fixture
def client(student):
    c = APIClient()
    c.force_authenticate(user=student)
    return c


SUB_BODY = {
    "endpoint": "https://push.example.com/endpoint-1",
    "keys": {"p256dh": "pub-key", "auth": "auth-secret"},
}


class TestPushSubscribeAPI:
    def test_subscribe_creates_row(self, db, client, student):
        resp = client.post("/api/v1/push/subscribe/", SUB_BODY, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["created"] is True
        sub = PushSubscription.objects.get(endpoint=SUB_BODY["endpoint"])
        assert sub.user == student
        assert sub.p256dh == "pub-key"

    def test_subscribe_is_idempotent(self, db, client):
        client.post("/api/v1/push/subscribe/", SUB_BODY, format="json")
        resp = client.post("/api/v1/push/subscribe/", SUB_BODY, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["created"] is False
        assert PushSubscription.objects.filter(endpoint=SUB_BODY["endpoint"]).count() == 1

    def test_subscribe_requires_keys(self, db, client):
        resp = client.post(
            "/api/v1/push/subscribe/",
            {"endpoint": "https://push.example.com/x", "keys": {"p256dh": "only-one"}},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_subscribe_requires_auth(self, db):
        resp = APIClient().post("/api/v1/push/subscribe/", SUB_BODY, format="json")
        assert resp.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_unsubscribe_deletes_row(self, db, client, student):
        client.post("/api/v1/push/subscribe/", SUB_BODY, format="json")
        resp = client.post("/api/v1/push/unsubscribe/", {"endpoint": SUB_BODY["endpoint"]}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["deleted"] == 1
        assert PushSubscription.objects.count() == 0


class TestVapidPublicKey:
    def test_returns_configured_key(self, db, settings):
        settings.VAPID_PUBLIC_KEY = "test-public-key"
        resp = APIClient().get("/api/v1/push/vapid-public-key/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["publicKey"] == "test-public-key"

    def test_blank_when_unconfigured(self, db, settings):
        settings.VAPID_PUBLIC_KEY = ""
        resp = APIClient().get("/api/v1/push/vapid-public-key/")
        assert resp.data["publicKey"] == ""


class TestSendWebPush:
    def test_noop_when_key_blank(self, db, student, settings):
        settings.VAPID_PRIVATE_KEY = ""
        PushSubscription.objects.create(user=student, endpoint="https://push.example.com/a", p256dh="k", auth="a")
        from openshiksha.apps.core.push import send_web_push

        assert send_web_push(student, {"title": "Hi"}) == 0

    def test_sends_to_all_subscriptions(self, db, student, settings):
        settings.VAPID_PRIVATE_KEY = "private"
        for i in range(2):
            PushSubscription.objects.create(
                user=student, endpoint=f"https://push.example.com/{i}", p256dh="k", auth="a"
            )
        with mock.patch("pywebpush.webpush") as m:
            from openshiksha.apps.core.push import send_web_push

            sent = send_web_push(student, {"title": "Hi"})
        assert sent == 2
        assert m.call_count == 2

    def test_prunes_stale_410(self, db, student, settings):
        settings.VAPID_PRIVATE_KEY = "private"
        PushSubscription.objects.create(user=student, endpoint="https://push.example.com/stale", p256dh="k", auth="a")
        from pywebpush import WebPushException

        fake_response = mock.Mock(status_code=410)
        with mock.patch("pywebpush.webpush", side_effect=WebPushException("gone", response=fake_response)):
            from openshiksha.apps.core.push import send_web_push

            sent = send_web_push(student, {"title": "Hi"})
        assert sent == 0
        assert PushSubscription.objects.count() == 0

    def test_keeps_subscription_on_transient_error(self, db, student, settings):
        settings.VAPID_PRIVATE_KEY = "private"
        PushSubscription.objects.create(
            user=student, endpoint="https://push.example.com/transient", p256dh="k", auth="a"
        )
        from pywebpush import WebPushException

        fake_response = mock.Mock(status_code=500)
        with mock.patch("pywebpush.webpush", side_effect=WebPushException("boom", response=fake_response)):
            from openshiksha.apps.core.push import send_web_push

            sent = send_web_push(student, {"title": "Hi"})
        assert sent == 0
        assert PushSubscription.objects.count() == 1  # transient → not pruned
