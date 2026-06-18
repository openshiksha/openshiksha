"""
Web Push delivery helper (MPN-2).

Sends an encrypted Web Push payload to every browser a user has subscribed
(see ``PushSubscription``). This is the mobile-native counterpart to
``core.emails`` — it reaches a student's home-screen PWA install even when the
app is closed (docs/initiatives/2026-mobile-shell-pwa-offline.md, web-push phase).

Design rules:
- **Never raise into a caller.** A reminder/grading task must never fail because
  one push endpoint is dead, so every send is wrapped per-subscription.
- **Self-pruning.** A push service returning 404/410 means the subscription is
  permanently gone; we delete that row so it never retries.
- **No-op without keys.** If ``VAPID_PRIVATE_KEY`` is blank (dev/CI), send
  nothing and return 0 — push is an additive channel, never required.
"""

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def send_web_push(user, payload: dict) -> int:
    """
    Deliver ``payload`` (a JSON-serializable dict, e.g.
    ``{"title", "body", "url", "tag"}``) to all of ``user``'s push subscriptions.

    Returns the number of subscriptions successfully sent to. Stale (404/410)
    subscriptions are deleted. No-op (returns 0) when VAPID is not configured.
    """
    private_key = getattr(settings, "VAPID_PRIVATE_KEY", "")
    if not private_key:
        return 0

    # Imported lazily so the dependency is only needed when push is configured.
    from pywebpush import WebPushException, webpush

    from openshiksha.apps.core.models import PushSubscription

    admin_email = getattr(settings, "VAPID_ADMIN_EMAIL", "admin@openshiksha.org")
    vapid_claims = {"sub": f"mailto:{admin_email}"}
    data = json.dumps(payload)

    sent = 0
    for sub in PushSubscription.objects.filter(user=user):
        subscription_info = {
            "endpoint": sub.endpoint,
            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=data,
                vapid_private_key=private_key,
                vapid_claims=dict(vapid_claims),
            )
            sent += 1
        except WebPushException as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code in (404, 410):
                # Subscription is permanently gone — prune it.
                logger.info("send_web_push: pruning stale subscription %s (%s)", sub.endpoint[:40], status_code)
                sub.delete()
            else:
                logger.warning("send_web_push: failed for %s: %s", sub.endpoint[:40], exc)
        except Exception:
            logger.exception("send_web_push: unexpected error for %s", sub.endpoint[:40])

    return sent
