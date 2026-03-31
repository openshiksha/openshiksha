"""
Core ViewSets for OpenShiksha API

Covers User, SubjectRoom, Question, ProblemSet, Assignment, and Submission.
"""

from rest_framework import filters, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from openshiksha.apps.api.serializers import (
    AssignmentDetailSerializer,
    AssignmentSerializer,
    ProblemSetSerializer,
    QuestionSerializer,
    QuestionTagSerializer,
    SubjectRoomSerializer,
    SubmissionSerializer,
    UserSerializer,
)
from openshiksha.apps.core.models import (
    Assignment,
    ProblemSet,
    Question,
    QuestionTag,
    SubjectRoom,
    Submission,
    User,
    UserRole,
)


class IsTeacher(permissions.BasePermission):
    """Only teachers may proceed."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.TEACHER


class IsStudent(permissions.BasePermission):
    """Only students (including open students) may proceed."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [UserRole.STUDENT, UserRole.OPEN_STUDENT]


class IsTeacherOrReadOnly(permissions.BasePermission):
    """Teachers have full access; authenticated users have read access."""

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.role == UserRole.TEACHER


class UserViewSet(viewsets.GenericViewSet):
    """
    User profile endpoints.

    GET /api/users/me/ -- returns the current authenticated user's profile.
    """

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.none()

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class QuestionTagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve question tags.
    Read-only -- tags are managed via admin.
    """

    queryset = QuestionTag.objects.all().order_by("name")
    serializer_class = QuestionTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "tag_type"]


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve questions.

    Filtering:
    - ?chapter=<id>
    - ?subject=<id>
    - ?standard=<id>
    - ?difficulty=<1-5>
    - ?question_type=<mcq|fill_blank|matching|multi_select|numeric>
    """

    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["chapter__name", "subject__name"]
    ordering_fields = ["difficulty", "created_at"]
    ordering = ["created_at"]

    def get_queryset(self):
        from django.db.models import Q

        user = self.request.user
        base_qs = (
            Question.objects.filter(is_active=True)
            .select_related("standard", "subject", "chapter")
            .prefetch_related("tags", "subparts__tags")
        )

        if hasattr(user, "school") and user.school:
            qs = base_qs.filter(Q(school__isnull=True) | Q(school=user.school))
        else:
            qs = base_qs.filter(school__isnull=True)

        params = self.request.query_params
        if chapter := params.get("chapter"):
            qs = qs.filter(chapter_id=chapter)
        if subject := params.get("subject"):
            qs = qs.filter(subject_id=subject)
        if standard := params.get("standard"):
            qs = qs.filter(standard_id=standard)
        if difficulty := params.get("difficulty"):
            qs = qs.filter(difficulty=difficulty)
        if question_type := params.get("question_type"):
            qs = qs.filter(question_type=question_type)

        return qs


class SubjectRoomViewSet(viewsets.ModelViewSet):
    """
    CRUD for SubjectRooms.

    - Teachers see and manage rooms they teach.
    - Students see rooms they are enrolled in.
    - Admins see all rooms for their school.
    """

    serializer_class = SubjectRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SubjectRoom.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return SubjectRoom.objects.none()
        user = self.request.user
        qs = SubjectRoom.objects.select_related("classroom__school", "subject", "teacher").prefetch_related("students")

        if user.role == UserRole.TEACHER:
            return qs.filter(teacher=user)
        elif user.role in [UserRole.STUDENT, UserRole.OPEN_STUDENT]:
            return qs.filter(students=user, is_active=True)
        elif user.role == UserRole.ADMIN:
            return qs.filter(classroom__school=user.school)
        return qs.none()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]


class ProblemSetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve problem sets.
    """

    serializer_class = ProblemSetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        from django.db.models import Q

        qs = ProblemSet.objects.filter(is_active=True).select_related("standard", "subject", "chapter")

        if hasattr(user, "school") and user.school:
            qs = qs.filter(Q(school__isnull=True) | Q(school=user.school))
        else:
            qs = qs.filter(school__isnull=True)

        params = self.request.query_params
        if chapter := params.get("chapter"):
            qs = qs.filter(chapter_id=chapter)
        if subject := params.get("subject"):
            qs = qs.filter(subject_id=subject)
        if standard := params.get("standard"):
            qs = qs.filter(standard_id=standard)

        return qs


class AssignmentViewSet(viewsets.ModelViewSet):
    """
    Assignment CRUD.

    - GET /api/assignments/ -- students see their pending/active assignments;
      teachers see assignments they created.
    - POST /api/assignments/ -- teachers only.
    - GET /api/assignments/{id}/ -- detail view with questions + submission status.
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = Assignment.objects.none()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AssignmentDetailSerializer
        return AssignmentSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Assignment.objects.none()
        user = self.request.user
        qs = Assignment.objects.select_related(
            "problem_set__subject",
            "problem_set__chapter",
            "subject_room__classroom",
            "subject_room__subject",
            "assigned_by",
        )

        if user.role in [UserRole.STUDENT, UserRole.OPEN_STUDENT]:
            return qs.filter(subject_room__students=user, subject_room__is_active=True)
        elif user.role == UserRole.TEACHER:
            return qs.filter(assigned_by=user)
        elif user.role == UserRole.ADMIN:
            return qs.filter(subject_room__classroom__school=user.school)
        return qs.none()

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["get"], url_path="submissions")
    def submissions(self, request, pk=None):
        """GET /api/assignments/{id}/submissions/ -- teacher views all submissions."""
        assignment = self.get_object()
        if request.user.role != UserRole.TEACHER:
            return Response({"detail": "Forbidden."}, status=403)
        subs = assignment.submissions.select_related("student")
        serializer = SubmissionSerializer(subs, many=True, context={"request": request})
        return Response(serializer.data)


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    Submission CRUD.

    - POST /api/submissions/ -- student creates submission (saves answers in progress)
    - PATCH /api/submissions/{id}/ -- student updates answers or sets submitted_at
    - GET /api/submissions/{id}/ -- student views their own submission
    """

    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Submission.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Submission.objects.none()
        user = self.request.user
        qs = Submission.objects.select_related("assignment__problem_set", "student")

        if user.role in [UserRole.STUDENT, UserRole.OPEN_STUDENT]:
            return qs.filter(student=user)
        elif user.role == UserRole.TEACHER:
            return qs.filter(assignment__subject_room__teacher=user)
        elif user.role == UserRole.ADMIN:
            return qs.filter(assignment__subject_room__classroom__school=user.school)
        return qs.none()

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated()]
