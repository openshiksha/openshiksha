"""
Tests for the PushSubscription model (MPN-1).

Web Push subscriptions persist a browser's W3C Push API subscription so the
backend can deliver due-date reminders to a home-screen PWA install.
"""

import pytest

from django.db import IntegrityError


@pytest.fixture
def student(db):
    from openshiksha.apps.core.models import User, UserRole

    return User.objects.create_user(username="push_student", password="pass", role=UserRole.STUDENT)


class TestPushSubscriptionModel:
    def test_create_subscription(self, db, student):
        from openshiksha.apps.core.models import PushSubscription

        sub = PushSubscription.objects.create(
            user=student,
            endpoint="https://push.example.com/abc123",
            p256dh="pub-key",
            auth="auth-secret",
            user_agent="Mozilla/5.0",
        )
        assert sub.pk is not None
        assert sub.user == student
        assert student.push_subscriptions.count() == 1

    def test_str_truncates_endpoint(self, db, student):
        from openshiksha.apps.core.models import PushSubscription

        sub = PushSubscription.objects.create(
            user=student,
            endpoint="https://push.example.com/" + ("x" * 100),
            p256dh="pub-key",
            auth="auth-secret",
        )
        rendered = str(sub)
        assert "PushSubscription" in rendered
        assert str(student.id) in rendered

    def test_endpoint_unique(self, db, student):
        from openshiksha.apps.core.models import PushSubscription

        PushSubscription.objects.create(
            user=student,
            endpoint="https://push.example.com/dup",
            p256dh="k1",
            auth="a1",
        )
        with pytest.raises(IntegrityError):
            PushSubscription.objects.create(
                user=student,
                endpoint="https://push.example.com/dup",
                p256dh="k2",
                auth="a2",
            )

    def test_cascade_delete_with_user(self, db, student):
        from openshiksha.apps.core.models import PushSubscription

        PushSubscription.objects.create(
            user=student,
            endpoint="https://push.example.com/cascade",
            p256dh="k",
            auth="a",
        )
        student.delete()
        assert PushSubscription.objects.count() == 0
