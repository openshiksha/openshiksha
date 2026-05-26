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
    ChapterSerializer,
    ProblemSetSerializer,
    ProblemSetWriteSerializer,
    QuestionMistakeSerializer,
    QuestionSerializer,
    QuestionTagSerializer,
    QuestionWriteSerializer,
    StudentProficiencySerializer,
    StudentProficiencySnapshotSerializer,
    SubjectRoomSerializer,
    SubjectSerializer,
    SubmissionSerializer,
    UserSerializer,
)
from openshiksha.apps.core.models import (
    Assignment,
    Chapter,
    ProblemSet,
    Question,
    QuestionTag,
    Subject,
    SubjectRoom,
    Submission,
    User,
    UserRole,
)
from openshiksha.apps.edge.models import StudentProficiency, StudentProficiencySnapshot, SubjectRoomQuestionMistake


class IsTeacher(permissions.BasePermission):
    """Only teachers may proceed."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.TEACHER


class IsStudent(permissions.BasePermission):
    """Only students (including open students) may proceed."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [UserRole.STUDENT, UserRole.OPEN_STUDENT]


class IsParent(permissions.BasePermission):
    """Only parents may proceed."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.PARENT


class IsStudentOrParent(permissions.BasePermission):
    """Students (including open) and parents may proceed."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            UserRole.STUDENT,
            UserRole.OPEN_STUDENT,
            UserRole.PARENT,
        ]


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

    @action(detail=False, methods=["get"], url_path="me/children", permission_classes=[IsParent])
    def children(self, request):
        """GET /api/users/me/children/ — returns authenticated parent's linked children."""
        kids = request.user.children.select_related("school").all()
        return Response(UserSerializer(kids, many=True).data)

    @action(detail=False, methods=["get"], url_path="me/streak")
    def me_streak(self, request):
        """GET /api/users/me/streak/ — returns authenticated student's current streak."""
        from openshiksha.apps.core.models import StudentStreak, UserRole

        user = request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return Response({"detail": "Only students have streaks."}, status=403)

        streak, _ = StudentStreak.objects.get_or_create(student=user)
        return Response(
            {
                "current_streak": streak.current_streak,
                "longest_streak": streak.longest_streak,
                "last_activity_date": streak.last_activity_date,
                "streak_grace_used": streak.streak_grace_used,
                "milestone_tier": streak.milestone_tier,
            }
        )

    @action(detail=False, methods=["patch"], url_path="me/profile")
    def update_profile(self, request):
        """PATCH /api/v1/users/me/profile/ — update own profile fields."""
        from openshiksha.apps.api.serializers.core import UserProfileUpdateSerializer

        ALLOWED_FIELDS = {"first_name", "last_name", "email", "phone_number"}
        data = {k: v for k, v in request.data.items() if k in ALLOWED_FIELDS}
        serializer = UserProfileUpdateSerializer(request.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["get", "post"], url_path="me/classroom-code", permission_classes=[IsTeacher])
    def classroom_code(self, request):
        """
        GET  — returns all active join codes for classrooms taught by this teacher.
        POST — generates a new code for a specified classroom (body: {classroom_id}).
        """
        from django.shortcuts import get_object_or_404

        from openshiksha.apps.api.serializers.core import ClassroomInviteCodeSerializer
        from openshiksha.apps.core.models import ClassRoom, ClassroomInviteCode

        if request.method == "GET":
            codes = ClassroomInviteCode.objects.filter(
                classroom__class_teacher=request.user, is_active=True
            ).select_related("classroom")
            return Response(ClassroomInviteCodeSerializer(codes, many=True).data)

        classroom_id = request.data.get("classroom_id")
        if not classroom_id:
            return Response({"detail": "classroom_id is required."}, status=400)
        classroom = get_object_or_404(ClassRoom, id=classroom_id, class_teacher=request.user)
        ClassroomInviteCode.objects.filter(classroom=classroom).update(is_active=False)
        code = ClassroomInviteCode.objects.create(
            classroom=classroom,
            code=ClassroomInviteCode.generate_code(),
            created_by=request.user,
        )
        return Response(ClassroomInviteCodeSerializer(code).data, status=201)


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


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve subjects.
    Used by question authoring UI to populate chapter picker.
    """

    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Subject.objects.all().order_by("name")
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class ChapterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve chapters.

    Filtering:
    - ?subject=<id>
    - ?standard=<id>
    """

    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["order"]
    ordering = ["order"]

    def get_queryset(self):
        qs = Chapter.objects.select_related("subject", "standard").order_by("order")
        params = self.request.query_params
        if subject := params.get("subject"):
            qs = qs.filter(subject_id=subject)
        if standard := params.get("standard"):
            qs = qs.filter(standard_id=standard)
        return qs


class QuestionViewSet(viewsets.ModelViewSet):
    """
    Question bank CRUD.

    Read: all authenticated users can list/retrieve questions.
    Write (create/update/delete): teachers only.

    Filtering:
    - ?chapter=<id>
    - ?subject=<id>
    - ?standard=<id>
    - ?difficulty=<1-5>
    - ?question_type=<mcq|fill_blank|matching|multi_select|numeric>
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["chapter__name", "subject__name", "subparts__question_text", "tags__name"]
    ordering_fields = ["difficulty", "created_at"]
    ordering = ["created_at"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return QuestionWriteSerializer
        return QuestionSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]

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

    def perform_create(self, serializer):
        school = getattr(self.request.user, "school", None)
        serializer.save(created_by=self.request.user, school=school)

    @action(detail=False, methods=["get"], url_path="browse")
    def browse_chapters(self, request):
        """
        GET /api/v1/questions/browse/

        Returns chapters from the shared question bank with question counts.
        Filtered by ?subject=<id> and/or ?standard=<id>.
        """
        from django.db.models import Count, Q

        qs = (
            Chapter.objects.annotate(
                question_count=Count(
                    "questions",
                    filter=Q(questions__school__isnull=True, questions__is_active=True),
                )
            )
            .filter(question_count__gt=0)
            .select_related("subject", "standard")
            .order_by("standard__number", "subject__name", "order")
        )

        params = request.query_params
        if subject := params.get("subject"):
            qs = qs.filter(subject_id=subject)
        if standard := params.get("standard"):
            qs = qs.filter(standard_id=standard)

        data = [
            {
                "id": ch.id,
                "name": ch.name,
                "subject_id": ch.subject_id,
                "subject": ch.subject.name,
                "standard_id": ch.standard_id,
                "standard": ch.standard.number,
                "question_count": ch.question_count,
            }
            for ch in qs
        ]
        return Response(data)


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


class ProblemSetViewSet(viewsets.ModelViewSet):
    """
    Problem set CRUD.

    Read: all authenticated users.
    Write (create/update/delete): teachers only.

    Filtering:
    - ?chapter=<id>
    - ?subject=<id>
    - ?standard=<id>
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ProblemSetWriteSerializer
        return ProblemSetSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]

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

    def perform_create(self, serializer):
        school = getattr(self.request.user, "school", None)
        serializer.save(school=school, created_by=self.request.user)


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
        ).prefetch_related(
            "problem_set__questions__subparts__tags",
            "problem_set__questions__tags",
        )

        if user.role in [UserRole.STUDENT, UserRole.OPEN_STUDENT]:
            from django.db.models import Q

            return qs.filter(
                subject_room__students=user,
                subject_room__is_active=True,
            ).filter(Q(target_student=None) | Q(target_student=user))
        elif user.role == UserRole.TEACHER:
            return qs.filter(assigned_by=user)
        elif user.role == UserRole.ADMIN:
            return qs.filter(subject_room__classroom__school=user.school)
        elif user.role == UserRole.PARENT:
            child_id = self.request.query_params.get("student")
            if not child_id:
                return qs.none()
            try:
                child_pk = int(child_id)
            except (ValueError, TypeError):
                return qs.none()
            if not user.children.filter(id=child_pk).exists():
                return qs.none()
            return (
                qs.filter(
                    subject_room__students__id=child_pk,
                    subject_room__is_active=True,
                )
                .prefetch_related("submissions")
                .order_by("-assigned_at")
            )
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
            qs = qs.filter(student=user)
        elif user.role == UserRole.TEACHER:
            qs = qs.filter(assignment__subject_room__teacher=user)
        elif user.role == UserRole.ADMIN:
            qs = qs.filter(assignment__subject_room__classroom__school=user.school)
        else:
            return qs.none()

        assignment_id = self.request.query_params.get("assignment")
        if assignment_id:
            qs = qs.filter(assignment_id=assignment_id)
        return qs

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), IsStudent()]
        return [permissions.IsAuthenticated()]


class StudentProficiencyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only view of a student's proficiency per question tag.

    - Students see their own records.
    - Parents see a child's records via ?student=<child_id> (ownership enforced).

    GET /api/proficiency/ — list all proficiency records for the current student
    GET /api/proficiency/?student=<id> — parent reads child's proficiency
    GET /api/proficiency/{id}/ — retrieve a single record
    """

    serializer_class = StudentProficiencySerializer
    permission_classes = [permissions.IsAuthenticated, IsStudentOrParent]

    def get_queryset(self):
        user = self.request.user
        base_select = {
            "question_tag",
            "subject_room__subject",
            "subject_room__classroom__standard",
        }

        if user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return (
                StudentProficiency.objects.filter(student=user)
                .select_related(*base_select)
                .order_by("subject_room__subject__name", "question_tag__name")
            )

        if user.role == UserRole.PARENT:
            child_id_param = self.request.query_params.get("student")
            if not child_id_param:
                return StudentProficiency.objects.none()
            try:
                child_pk = int(child_id_param)
            except (ValueError, TypeError):
                return StudentProficiency.objects.none()
            if not user.children.filter(id=child_pk).exists():
                return StudentProficiency.objects.none()
            return (
                StudentProficiency.objects.filter(student_id=child_pk)
                .select_related(*base_select)
                .order_by("subject_room__subject__name", "question_tag__name")
            )

        return StudentProficiency.objects.none()

    @action(detail=False, methods=["get"], url_path="history")
    def history(self, request):
        """
        GET /api/v1/proficiency/history/?tag=<id>&subject_room=<id>
        GET /api/v1/proficiency/history/?tag=<id>&subject_room=<id>&student=<id>  (parent)

        Returns append-only snapshot history for trend sparklines.
        Students see their own history; parents see a child's history (ownership enforced).
        """
        tag_id = request.query_params.get("tag")
        room_id = request.query_params.get("subject_room")
        if not tag_id or not room_id:
            return Response({"detail": "tag and subject_room are required."}, status=400)

        user = request.user

        if user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            student_id = user.id
        elif user.role == UserRole.PARENT:
            child_id = request.query_params.get("student")
            if not child_id:
                return Response([], status=200)
            try:
                child_pk = int(child_id)
            except (ValueError, TypeError):
                return Response([], status=200)
            if not user.children.filter(id=child_pk).exists():
                return Response([], status=200)
            student_id = child_pk
        else:
            return Response([], status=200)

        snapshots = (
            StudentProficiencySnapshot.objects.filter(
                student_id=student_id,
                question_tag_id=tag_id,
                subject_room_id=room_id,
            )
            .order_by("recorded_at")
            .only("id", "score", "recorded_at")
        )
        return Response(StudentProficiencySnapshotSerializer(snapshots, many=True).data)


class QuestionMistakeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/question-mistakes/?subject_room=<id>

    Returns questions ordered by regression (hardest first).
    Restricted to teachers; only returns data for their own subject rooms.
    """

    serializer_class = QuestionMistakeSerializer
    permission_classes = [permissions.IsAuthenticated, IsTeacher]

    def get_queryset(self):
        qs = (
            SubjectRoomQuestionMistake.objects.filter(subject_room__teacher=self.request.user)
            .select_related("question", "subject_room")
            .prefetch_related("question__subparts")
            .order_by("-regression")
        )
        subject_room_id = self.request.query_params.get("subject_room")
        if subject_room_id:
            qs = qs.filter(subject_room_id=subject_room_id)
        return qs
