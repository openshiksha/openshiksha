"""
Core ViewSets for OpenShiksha API

Covers User, SubjectRoom, Question, ProblemSet, Assignment, and Submission.
"""

from pathlib import Path
from uuid import uuid4

from django.contrib.auth.password_validation import validate_password
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from openshiksha.apps.api.serializers import (
    AssignmentDetailSerializer,
    AssignmentSerializer,
    ChapterSerializer,
    ClassRoomSerializer,
    ProblemSetSerializer,
    ProblemSetWriteSerializer,
    QuestionMistakeSerializer,
    QuestionSerializer,
    QuestionTagSerializer,
    QuestionWithSubpartsStudentSerializer,
    QuestionWriteSerializer,
    StudentProficiencySerializer,
    StudentProficiencySnapshotSerializer,
    SubjectRoomAdminSerializer,
    SubjectRoomSerializer,
    SubjectSerializer,
    SubmissionSerializer,
    UserSerializer,
)
from openshiksha.apps.core.models import (
    Assignment,
    Chapter,
    ClassRoom,
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


class IsSchoolAdmin(permissions.BasePermission):
    """Only authenticated users with the ADMIN role may proceed."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == UserRole.ADMIN)


class IsTeacherOrSchoolAdmin(permissions.BasePermission):
    """Teachers or school admins may proceed."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role in (UserRole.TEACHER, UserRole.ADMIN)
        )


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

        ALLOWED_FIELDS = {"first_name", "last_name", "email", "phone_number", "email_reminders_opt_out"}
        data = {k: v for k, v in request.data.items() if k in ALLOWED_FIELDS}
        serializer = UserProfileUpdateSerializer(request.user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)

    @action(detail=False, methods=["post"], url_path="me/password")
    def change_password(self, request):
        """POST /api/v1/users/me/password/ - change own password."""
        current_password = request.data.get("current_password", "")
        new_password = request.data.get("new_password", "")

        if not request.user.check_password(current_password):
            return Response({"current_password": ["Current password is incorrect."]}, status=400)

        try:
            validate_password(new_password, request.user)
        except Exception as exc:
            messages = getattr(exc, "messages", None)
            return Response({"new_password": messages or [str(exc)]}, status=400)

        request.user.set_password(new_password)
        request.user.save(update_fields=["password"])
        return Response({"detail": "Password changed successfully."})

    @action(detail=False, methods=["get", "post"], url_path="me/classroom-code", permission_classes=[IsTeacher])
    def classroom_code(self, request):
        """
        GET  — returns all active join codes for classrooms this teacher can manage.
        POST — generates a new code for a specified classroom (body: {classroom_id}).

        A classroom is manageable by its homeroom ``class_teacher`` **and** by any
        teacher who runs a ``SubjectRoom`` inside it. The dashboard surfaces the
        join code per subject room, so a subject teacher (who is usually *not*
        the homeroom teacher) must be able to generate and read it — otherwise
        the widget silently 404s for them.
        """
        from django.db.models import Q

        from openshiksha.apps.api.serializers.core import ClassroomInviteCodeSerializer
        from openshiksha.apps.core.models import ClassRoom, ClassroomInviteCode

        manageable = Q(class_teacher=request.user) | Q(subject_rooms__teacher=request.user)

        if request.method == "GET":
            codes = (
                ClassroomInviteCode.objects.filter(is_active=True)
                .filter(Q(classroom__class_teacher=request.user) | Q(classroom__subject_rooms__teacher=request.user))
                .select_related("classroom")
                .distinct()
            )
            return Response(ClassroomInviteCodeSerializer(codes, many=True).data)

        classroom_id = request.data.get("classroom_id")
        if not classroom_id:
            return Response({"detail": "classroom_id is required."}, status=400)
        classroom = ClassRoom.objects.filter(manageable, id=classroom_id).distinct().first()
        if classroom is None:
            return Response({"detail": "Classroom not found, or you do not teach in it."}, status=404)
        ClassroomInviteCode.objects.filter(classroom=classroom).update(is_active=False)
        code = ClassroomInviteCode.objects.create(
            classroom=classroom,
            code=ClassroomInviteCode.generate_code(),
            created_by=request.user,
        )
        return Response(ClassroomInviteCodeSerializer(code).data, status=201)

    @action(detail=False, methods=["get"], url_path="school-teachers", permission_classes=[IsSchoolAdmin])
    def school_teachers(self, request):
        """GET /api/v1/users/school-teachers/ — teachers in the admin's own school (enrollment picker)."""
        if request.user.school_id is None:
            return Response({"detail": "Your account is not linked to a school."}, status=400)
        teachers = User.objects.filter(school_id=request.user.school_id, role=UserRole.TEACHER).order_by(
            "first_name", "last_name"
        )
        return Response([{"id": t.id, "full_name": t.full_name, "email": t.email} for t in teachers])

    @action(detail=False, methods=["get"], url_path="school-students", permission_classes=[IsSchoolAdmin])
    def school_students(self, request):
        """GET /api/v1/users/school-students/ — students in the admin's own school (enrollment picker)."""
        if request.user.school_id is None:
            return Response({"detail": "Your account is not linked to a school."}, status=400)
        students = User.objects.filter(
            school_id=request.user.school_id, role__in=[UserRole.STUDENT, UserRole.OPEN_STUDENT]
        ).order_by("first_name", "last_name")
        return Response([{"id": s.id, "full_name": s.full_name, "email": s.email} for s in students])


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
        # Students and open students get the safe serializer: no correct_answer,
        # MCQ options shuffled, and {{var}} tokens substituted per-student.
        if self.action in ["list", "retrieve"]:
            role = getattr(getattr(self, "request", None) and self.request.user, "role", None)
            if role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
                return QuestionWithSubpartsStudentSerializer
        return QuestionSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "upload_image"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        from django.db.models import Count, Exists, OuterRef, Q

        from openshiksha.apps.core.models import Submission as SubmissionModel

        user = self.request.user
        base_qs = (
            Question.objects.filter(is_active=True)
            .select_related("standard", "subject", "chapter")
            .prefetch_related("tags", "subparts__tags")
        )

        # AIV-3a: edit-safety flag annotations — avoid N+1 on list views.
        graded_subs_using = SubmissionModel.objects.filter(
            assignment__problem_set__questions=OuterRef("pk"), score__isnull=False
        )
        base_qs = base_qs.annotate(
            assigned_count_anno=Count("problem_sets__assignments", distinct=True),
            has_graded_submissions_anno=Exists(graded_subs_using),
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
            # Match the Browse endpoint (#194): callers send the standard number
            # (1..12), not the PK. Keeps the QuestionBank's eventual Grade filter
            # consistent with Browse.
            qs = qs.filter(standard__number=standard)
        if difficulty := params.get("difficulty"):
            qs = qs.filter(difficulty=difficulty)
        if question_type := params.get("question_type"):
            qs = qs.filter(question_type=question_type)

        # `search_fields` joins through subparts.question_text and tags.name —
        # a question with two matching subparts (or several matching tags) would
        # otherwise appear once per match. Deduplicate at the queryset level so
        # paginated + non-paginated callers both see one row per question.
        return qs.distinct()

    def perform_create(self, serializer):
        school = getattr(self.request.user, "school", None)
        serializer.save(created_by=self.request.user, school=school)

    @action(
        detail=False,
        methods=["post"],
        url_path="upload-image",
        parser_classes=[parsers.MultiPartParser, parsers.FormParser],
    )
    def upload_image(self, request):
        """POST /api/v1/questions/upload-image/ - upload an authoring image."""
        upload = request.FILES.get("image")
        if upload is None:
            return Response({"image": ["No image file provided."]}, status=400)

        content_type = getattr(upload, "content_type", "") or ""
        if not content_type.startswith("image/"):
            return Response({"image": ["Upload must be an image file."]}, status=400)

        max_size = 5 * 1024 * 1024
        if upload.size > max_size:
            return Response({"image": ["Image must be 5 MB or smaller."]}, status=400)

        suffix = Path(upload.name).suffix.lower()
        if suffix not in {".gif", ".jpg", ".jpeg", ".png", ".webp"}:
            suffix = ".png"

        path = default_storage.save(f"question_uploads/{uuid4().hex}{suffix}", upload)
        return Response({"image_url": request.build_absolute_uri(default_storage.url(path))}, status=201)

    @action(detail=False, methods=["get"], url_path="browse")
    def browse_chapters(self, request):
        """
        GET /api/v1/questions/browse/

        Returns chapters from the shared question bank with question counts.
        Filtered by ?subject=<subject_id> and/or ?standard=<standard_number>
        (e.g. `?standard=7` selects Grade 7 chapters; the BrowsePage dropdown
        sends standard numbers, not standard PKs).
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
            qs = qs.filter(standard__number=standard)

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


class ClassRoomViewSet(viewsets.ModelViewSet):
    """
    School-scoped classroom management for school admins.

    Every queryset and write is hard-scoped to the admin's own school — an admin
    can never see or mutate another school's classrooms. Deletion is a soft-delete
    (is_active=False) to preserve historical assignments and submissions.
    """

    serializer_class = ClassRoomSerializer
    permission_classes = [permissions.IsAuthenticated, IsSchoolAdmin]

    def get_queryset(self):
        from django.db.models import Count

        if getattr(self, "swagger_fake_view", False):
            return ClassRoom.objects.none()
        user = self.request.user
        if user.school_id is None:
            return ClassRoom.objects.none()
        qs = (
            ClassRoom.objects.filter(school_id=user.school_id)
            .select_related("standard", "class_teacher")
            .annotate(num_students=Count("students", distinct=True))
        )
        if self.request.query_params.get("include_inactive") != "true":
            qs = qs.filter(is_active=True)
        return qs.order_by("standard__number", "division")

    def _require_school(self):
        if self.request.user.school_id is None:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("Your account is not linked to a school.")

    def perform_create(self, serializer):
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError

        self._require_school()
        try:
            serializer.save(school=self.request.user.school)
        except IntegrityError:
            raise ValidationError("A classroom with this standard, division, and academic year already exists.")

    def destroy(self, request, *args, **kwargs):
        classroom = self.get_object()
        classroom.is_active = False
        classroom.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _resolve_students(self, request):
        """Return (valid_students, invalid_ids) scoped to the admin's school."""
        student_ids = request.data.get("student_ids", [])
        if not isinstance(student_ids, list):
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"student_ids": "Expected a list of student IDs."})
        found = User.objects.filter(
            id__in=student_ids,
            school_id=request.user.school_id,
            role__in=[UserRole.STUDENT, UserRole.OPEN_STUDENT],
        )
        valid_ids = {u.id for u in found}
        invalid_ids = [sid for sid in student_ids if sid not in valid_ids]
        return list(found), invalid_ids

    @action(detail=True, methods=["post"], url_path="enroll")
    def enroll(self, request, pk=None):
        """POST — body {"student_ids": [..]}; add same-school students to the classroom roster."""
        classroom = self.get_object()
        students, invalid_ids = self._resolve_students(request)
        classroom.students.add(*students)
        return Response(
            {
                "enrolled": [s.id for s in students],
                "invalid_ids": invalid_ids,
                "student_count": classroom.students.count(),
            }
        )

    @action(detail=True, methods=["post"], url_path="unenroll")
    def unenroll(self, request, pk=None):
        """POST — body {"student_ids": [..]}; remove students from the classroom roster."""
        classroom = self.get_object()
        students, invalid_ids = self._resolve_students(request)
        classroom.students.remove(*students)
        return Response(
            {
                "unenrolled": [s.id for s in students],
                "invalid_ids": invalid_ids,
                "student_count": classroom.students.count(),
            }
        )

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """GET — counts for the admin's school dashboard."""
        if request.user.school_id is None:
            return Response({"detail": "Your account is not linked to a school."}, status=400)
        school = request.user.school
        school_users = User.objects.filter(school_id=school.id)
        return Response(
            {
                "school": {"id": school.id, "name": school.name},
                "classroom_count": ClassRoom.objects.filter(school_id=school.id, is_active=True).count(),
                "teacher_count": school_users.filter(role=UserRole.TEACHER).count(),
                "student_count": school_users.filter(role__in=[UserRole.STUDENT, UserRole.OPEN_STUDENT]).count(),
                "active_subject_rooms": SubjectRoom.objects.filter(
                    classroom__school_id=school.id, is_active=True
                ).count(),
            }
        )


class SubjectRoomViewSet(viewsets.ModelViewSet):
    """
    CRUD for SubjectRooms.

    - Teachers see and manage rooms they teach.
    - Students see rooms they are enrolled in.
    - Admins see and manage (create/enroll) all rooms for their school.
    """

    serializer_class = SubjectRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = SubjectRoom.objects.none()

    def get_serializer_class(self):
        user = getattr(self.request, "user", None)
        if user is not None and getattr(user, "is_admin", False):
            return SubjectRoomAdminSerializer
        return SubjectRoomSerializer

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
        if self.action in ["create", "update", "partial_update", "destroy", "enroll", "unenroll"]:
            return [permissions.IsAuthenticated(), IsTeacherOrSchoolAdmin()]
        return [permissions.IsAuthenticated()]

    def _resolve_students(self, request):
        student_ids = request.data.get("student_ids", [])
        if not isinstance(student_ids, list):
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"student_ids": "Expected a list of student IDs."})
        found = User.objects.filter(
            id__in=student_ids,
            school_id=request.user.school_id,
            role__in=[UserRole.STUDENT, UserRole.OPEN_STUDENT],
        )
        valid_ids = {u.id for u in found}
        invalid_ids = [sid for sid in student_ids if sid not in valid_ids]
        return list(found), invalid_ids

    @action(detail=True, methods=["post"], url_path="enroll")
    def enroll(self, request, pk=None):
        """POST — body {"student_ids": [..]}; add same-school students to the subject room."""
        room = self.get_object()
        students, invalid_ids = self._resolve_students(request)
        room.students.add(*students)
        return Response(
            {"enrolled": [s.id for s in students], "invalid_ids": invalid_ids, "student_count": room.students.count()}
        )

    @action(detail=True, methods=["post"], url_path="unenroll")
    def unenroll(self, request, pk=None):
        """POST — body {"student_ids": [..]}; remove students from the subject room."""
        room = self.get_object()
        students, invalid_ids = self._resolve_students(request)
        room.students.remove(*students)
        return Response(
            {"unenrolled": [s.id for s in students], "invalid_ids": invalid_ids, "student_count": room.students.count()}
        )


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
        # `preview` (view-as-student) is a teacher-only authoring aid — this
        # overridden get_permissions takes precedence over the @action's own
        # permission_classes, so it must be listed here explicitly.
        if self.action in ["create", "update", "partial_update", "destroy", "preview"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        from django.db.models import Count, Exists, OuterRef, Q

        from openshiksha.apps.core.models import Submission as SubmissionModel

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

        # AIV-3a: annotate edit-safety flags so the serializer reads them off
        # the queryset row instead of issuing one query per ProblemSet.
        graded_subs = SubmissionModel.objects.filter(assignment__problem_set=OuterRef("pk"), score__isnull=False)
        qs = qs.annotate(
            assigned_count_anno=Count("assignments", distinct=True),
            has_graded_submissions_anno=Exists(graded_subs),
        )

        return qs

    def perform_create(self, serializer):
        school = getattr(self.request.user, "school", None)
        serializer.save(school=school, created_by=self.request.user)

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        """
        GET /api/v1/problem-sets/<id>/preview/

        Renders the set **exactly as a student sees it** — correct answers
        stripped, ``{{var}}`` tokens substituted, and MCQ options shuffled via
        the same student serializer the assignment page uses. Read-only; lets a
        teacher sanity-check a set before assigning it.
        """
        from openshiksha.apps.api.serializers.core import ProblemSetStudentDetailSerializer

        problem_set = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = ProblemSetStudentDetailSerializer(problem_set, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="add-question")
    def add_question(self, request, pk=None):
        """
        POST /api/v1/problem-sets/<id>/add-question/
        Body: {"question_id": <int>}

        Adds a question to this problem set.  Teacher must have created the set.
        """
        if request.user.role != UserRole.TEACHER:
            return Response({"detail": "Only teachers can modify problem sets."}, status=status.HTTP_403_FORBIDDEN)

        problem_set = get_object_or_404(ProblemSet, pk=pk, is_active=True)
        if problem_set.created_by_id != request.user.pk:
            return Response(
                {"detail": "You can only modify problem sets you created."}, status=status.HTTP_403_FORBIDDEN
            )

        question_id = request.data.get("question_id")
        if not question_id:
            return Response({"detail": "question_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        question = get_object_or_404(Question, pk=question_id, is_active=True)
        problem_set.questions.add(question)
        return Response({"detail": "Question added.", "question_id": question.id, "problem_set_id": problem_set.id})

    @action(detail=True, methods=["post"], url_path="remove-question")
    def remove_question(self, request, pk=None):
        """
        POST /api/v1/problem-sets/<id>/remove-question/
        Body: {"question_id": <int>}

        Removes a question from this problem set. Teacher must have created the
        set. Per AIV-1/2, this **only** affects the live set + future assignments
        — every existing ``Assignment.assigned_content`` snapshot keeps the
        question and students/teachers viewing past assignments are unaffected.
        That's the property that makes TW-2 editable preview safe to ship.
        """
        if request.user.role != UserRole.TEACHER:
            return Response({"detail": "Only teachers can modify problem sets."}, status=status.HTTP_403_FORBIDDEN)

        problem_set = get_object_or_404(ProblemSet, pk=pk, is_active=True)
        if problem_set.created_by_id != request.user.pk:
            return Response(
                {"detail": "You can only modify problem sets you created."}, status=status.HTTP_403_FORBIDDEN
            )

        question_id = request.data.get("question_id")
        if not question_id:
            return Response({"detail": "question_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        question = get_object_or_404(Question, pk=question_id)
        problem_set.questions.remove(question)
        return Response({"detail": "Question removed.", "question_id": question.id, "problem_set_id": problem_set.id})


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

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action == "retrieve":
            user = self.request.user
            if getattr(user, "role", None) in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
                from openshiksha.apps.core.models import Submission

                context["include_solutions"] = Submission.objects.filter(
                    assignment_id=self.kwargs.get("pk"),
                    student=user,
                    score__isnull=False,
                ).exists()
        return context

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
            from django.db.models import Prefetch, Q

            from openshiksha.apps.core.models import Submission

            # Prefetch only *this* student's submission per assignment so
            # AssignmentSerializer.get_my_submission can read it off the
            # cache without falling into N+1 over a class-sized list.
            return (
                qs.filter(
                    subject_room__students=user,
                    subject_room__is_active=True,
                )
                .filter(Q(target_student=None) | Q(target_student=user))
                .prefetch_related(
                    Prefetch(
                        "submissions",
                        queryset=Submission.objects.filter(student=user),
                        to_attr="my_submissions",
                    )
                )
            )
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

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        """POST /api/assignments/{id}/close/ — teacher stops accepting submissions."""
        if request.user.role != UserRole.TEACHER:
            return Response({"detail": "Forbidden."}, status=403)
        assignment = self.get_object()  # already scoped to assigned_by=user
        if assignment.closed_at is None:
            from django.utils import timezone

            assignment.closed_at = timezone.now()
            assignment.save(update_fields=["closed_at"])
        serializer = self.get_serializer(assignment)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="reopen")
    def reopen(self, request, pk=None):
        """POST /api/assignments/{id}/reopen/ — teacher resumes accepting submissions."""
        if request.user.role != UserRole.TEACHER:
            return Response({"detail": "Forbidden."}, status=403)
        assignment = self.get_object()
        if assignment.closed_at is not None:
            assignment.closed_at = None
            assignment.save(update_fields=["closed_at"])
        serializer = self.get_serializer(assignment)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="resync-preview")
    def resync_preview(self, request, pk=None):
        """
        GET /api/v1/assignments/{id}/resync-preview/

        AIV-6: shows the blast-radius of re-syncing this assignment's content to
        the live ``ProblemSet``. Returns a structured diff plus counts of how
        many submissions would be re-graded. Read-only; never mutates state.
        """
        if request.user.role != UserRole.TEACHER:
            return Response({"detail": "Forbidden."}, status=403)
        assignment = self.get_object()

        from openshiksha.apps.core.snapshots import build_assignment_snapshot, diff_snapshots

        fresh = build_assignment_snapshot(assignment.problem_set)
        diff = diff_snapshots(assignment.assigned_content, fresh)

        graded_count = assignment.submissions.filter(score__isnull=False).count()
        submitted_count = assignment.submissions.filter(submitted_at__isnull=False).count()

        return Response(
            {
                "assignment_id": assignment.pk,
                "has_drift": (
                    bool(diff["questions_added"])
                    or bool(diff["questions_removed"])
                    or bool(diff["answer_changes"])
                    or bool(diff["content_changes"])
                ),
                "diff": diff,
                "affected": {
                    "submitted_count": submitted_count,
                    "graded_count": graded_count,
                    # If any answer changes, every graded submission needs re-grading
                    # because their per-subpart ticks were computed against the old key.
                    "regrade_on_apply": graded_count if diff["answer_changes"] else 0,
                },
            }
        )

    @action(detail=True, methods=["post"], url_path="resync")
    def resync(self, request, pk=None):
        """
        POST /api/v1/assignments/{id}/resync/

        AIV-6: re-snapshot this assignment from the live ``ProblemSet``,
        archiving the prior snapshot in ``AssignmentSnapshotHistory``. If the
        diff contains answer changes, queues a re-grade for every already-graded
        submission so scores reflect the new key. Reversible via ``undo-resync``.
        """
        if request.user.role != UserRole.TEACHER:
            return Response({"detail": "Forbidden."}, status=403)
        assignment = self.get_object()

        from django.db import transaction

        from openshiksha.apps.core.models import AssignmentSnapshotHistory
        from openshiksha.apps.core.snapshots import build_assignment_snapshot, diff_snapshots

        fresh = build_assignment_snapshot(assignment.problem_set)
        diff = diff_snapshots(assignment.assigned_content, fresh)

        prior = assignment.assigned_content
        regrade_ids: list[int] = []

        with transaction.atomic():
            if prior:
                AssignmentSnapshotHistory.objects.create(assignment=assignment, content=prior, replaced_by=request.user)
            assignment.assigned_content = fresh
            assignment.save(update_fields=["assigned_content"])

            if diff["answer_changes"]:
                from openshiksha.apps.edge.models import Tick

                regrade_ids = list(assignment.submissions.filter(score__isnull=False).values_list("id", flat=True))
                # Drop the stale ticks; the grade_submission task will rebuild
                # them against the new snapshot.
                Tick.objects.filter(submission_id__in=regrade_ids).delete()

        # Queue re-grading outside the transaction so failures don't roll back
        # the snapshot swap (which itself is the recovery point — undo restores).
        if regrade_ids:
            from openshiksha.apps.core.tasks import grade_submission

            for sub_id in regrade_ids:
                grade_submission.delay(sub_id)

        serializer = self.get_serializer(assignment)
        return Response(
            {
                "assignment": serializer.data,
                "applied_diff": diff,
                "regraded_submission_count": len(regrade_ids),
            }
        )

    @action(detail=True, methods=["post"], url_path="undo-resync")
    def undo_resync(self, request, pk=None):
        """
        POST /api/v1/assignments/{id}/undo-resync/

        AIV-6: restore the most recent superseded snapshot, removing its
        history row. Idempotent: if no history exists, returns 404.
        """
        if request.user.role != UserRole.TEACHER:
            return Response({"detail": "Forbidden."}, status=403)
        assignment = self.get_object()

        from django.db import transaction

        last = assignment.snapshot_history.first()  # ordering is -replaced_at
        if last is None:
            return Response({"detail": "No prior snapshot to restore."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            assignment.assigned_content = last.content
            assignment.save(update_fields=["assigned_content"])
            last.delete()

        serializer = self.get_serializer(assignment)
        return Response({"assignment": serializer.data, "restored_at": last.replaced_at.isoformat()})


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
