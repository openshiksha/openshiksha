"""
Web Push subscription endpoints (MPN-2).

  GET  /api/v1/push/vapid-public-key/ — public key the frontend needs to
                                        subscribe (empty ⇒ push disabled)
  POST /api/v1/push/subscribe/        — upsert a browser subscription
  POST /api/v1/push/unsubscribe/      — remove a browser subscription

All require authentication; subscriptions are always scoped to request.user.
"""

from django.conf import settings
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from openshiksha.apps.core.models import PushSubscription


class VapidPublicKeyView(APIView):
    """Expose the VAPID public key. Empty string ⇒ frontend hides push UI."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"publicKey": getattr(settings, "VAPID_PUBLIC_KEY", "")})


class _SubscribeSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=512)
    keys = serializers.DictField(child=serializers.CharField())

    def validate_keys(self, value):
        if "p256dh" not in value or "auth" not in value:
            raise serializers.ValidationError("keys must contain 'p256dh' and 'auth'.")
        return value


class PushSubscribeView(APIView):
    """Register (or upsert) the caller's browser push subscription."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = _SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]
        sub, created = PushSubscription.objects.update_or_create(
            endpoint=data["endpoint"],
            defaults={
                "user": request.user,
                "p256dh": data["keys"]["p256dh"],
                "auth": data["keys"]["auth"],
                "user_agent": user_agent,
            },
        )
        return Response(
            {"id": sub.id, "created": created},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class _UnsubscribeSerializer(serializers.Serializer):
    endpoint = serializers.URLField(max_length=512)


class PushUnsubscribeView(APIView):
    """Remove the caller's subscription for a given endpoint (own rows only)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = _UnsubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        deleted, _ = PushSubscription.objects.filter(
            user=request.user, endpoint=serializer.validated_data["endpoint"]
        ).delete()
        return Response({"deleted": deleted}, status=status.HTTP_200_OK)
