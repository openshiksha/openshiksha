"""
Registration endpoints for self-service onboarding.

Two registration paths:
  POST /api/v1/auth/register/open/   — creates an open_student account
  POST /api/v1/auth/register/school/ — creates a student account via classroom join code
"""

from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from openshiksha.apps.core.models import ClassroomInviteCode, User, UserRole


class _RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class _SchoolRegistrationSerializer(_RegistrationSerializer):
    join_code = serializers.CharField(max_length=8)

    def validate_join_code(self, value):
        code = value.upper().strip()
        try:
            invite = ClassroomInviteCode.objects.select_related("classroom__school").get(code=code, is_active=True)
        except ClassroomInviteCode.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive join code.")
        if invite.expires_at and invite.expires_at < timezone.now():
            raise serializers.ValidationError("This join code has expired.")
        self.context["invite"] = invite
        return code


def _token_response(user):
    """Return JWT token pair for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        },
    }


class RegisterOpenView(APIView):
    """
    POST /api/v1/auth/register/open/

    Creates an open_student account. No join code required.
    Returns JWT token pair on success.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = _RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.create_user(
            username=data["username"],
            password=data["password"],
            email=data.get("email", ""),
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            role=UserRole.OPEN_STUDENT,
        )
        return Response(_token_response(user), status=status.HTTP_201_CREATED)


class RegisterSchoolView(APIView):
    """
    POST /api/v1/auth/register/school/

    Creates a student account using a classroom join code.
    Atomically enrolls the student in the classroom + all active SubjectRooms.
    Returns JWT token pair on success.
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        ctx: dict = {}
        serializer = _SchoolRegistrationSerializer(data=request.data, context=ctx)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        invite: ClassroomInviteCode = ctx["invite"]

        with transaction.atomic():
            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
                email=data.get("email", ""),
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                role=UserRole.STUDENT,
                school=invite.classroom.school,
            )
            classroom = invite.classroom
            classroom.students.add(user)
            for subject_room in classroom.subject_rooms.filter(is_active=True):
                subject_room.students.add(user)

        return Response(_token_response(user), status=status.HTTP_201_CREATED)
