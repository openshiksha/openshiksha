"""
Public enquiry endpoint.

    POST /api/v1/enquire/   — public (no auth), creates an Enquirer + notifies admins
"""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .emails import notify_enquiry_received
from .serializers import EnquirerSerializer


class EnquireView(APIView):
    """Accept enquiries from prospective schools. No authentication required."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request):
        serializer = EnquirerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enquirer = serializer.save()
        notify_enquiry_received(enquirer)
        return Response(
            {"detail": "Thank you for your enquiry. Our team will be in touch shortly."},
            status=status.HTTP_201_CREATED,
        )
