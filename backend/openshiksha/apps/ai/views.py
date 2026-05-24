"""
AI Analytics API views.

Permission rules:
- LearningGaps: student sees their own; teacher sees gaps for students in their rooms.
- ClassInsights: teacher sees insights for their subject_rooms.
- PerformancePredictions: student sees their own; teacher sees their students'.
- ContentRecommendations: student sees their own active recommendations.
- PracticePlans: student sees their own plans; today's plan auto-generated on demand.
- TriggerAnalysis: any authenticated user can trigger for a room they're associated with.
"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from openshiksha.apps.core.models import SubjectRoom, UserRole

from .models import (
    ClassInsight,
    ContentRecommendation,
    KnowledgeNode,
    LearningGap,
    LearningPath,
    LearningPathStatus,
    LearningPathStep,
    PerformancePrediction,
    PracticePlan,
    SpacedRepetitionEntry,
    StudentMastery,
)
from .serializers import (
    ClassInsightSerializer,
    CompleteStepSerializer,
    ContentRecommendationSerializer,
    KnowledgeNodeSerializer,
    LearningGapSerializer,
    LearningPathSerializer,
    PerformancePredictionSerializer,
    PracticePlanSerializer,
    SpacedRepetitionEntrySerializer,
    StudentMasterySerializer,
    TriggerAdaptiveSerializer,
    TriggerAnalysisSerializer,
    TriggerRecommendationsSerializer,
)
from .tasks import (
    analyze_student_subject_room,
    complete_learning_path_step,
    generate_class_insights_for_subject_room,
    generate_daily_practice_plan,
    rebuild_learning_path,
    refresh_recommendations_for_student,
)


class LearningGapViewSet(ReadOnlyModelViewSet):
    """
    list:   GET /api/v1/ai/learning-gaps/          — student's own active gaps
    retrieve: GET /api/v1/ai/learning-gaps/{id}/   — single gap detail

    Query params:
      ?include_resolved=true  — include resolved gaps (default: only active)
    """

    serializer_class = LearningGapSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        include_resolved = self.request.query_params.get("include_resolved", "").lower() == "true"

        qs = LearningGap.objects.select_related("chapter__subject").order_by("severity", "avg_score")

        if user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            qs = qs.filter(student=user)
        elif user.role == UserRole.TEACHER:
            # Teachers see gaps for students in their subject rooms
            their_rooms = SubjectRoom.objects.filter(teacher=user)
            qs = qs.filter(subject_room__in=their_rooms)
        else:
            return LearningGap.objects.none()

        if not include_resolved:
            qs = qs.filter(is_resolved=False)

        return qs


class ClassInsightViewSet(ReadOnlyModelViewSet):
    """
    list:     GET /api/v1/ai/class-insights/           — all insights for teacher's rooms
    retrieve: GET /api/v1/ai/class-insights/{id}/      — single insight
    by_room:  GET /api/v1/ai/class-insights/by-room/{subject_room_id}/
    """

    serializer_class = ClassInsightSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = ClassInsight.objects.select_related("chapter").order_by("-pct_struggling")

        if user.role == UserRole.TEACHER:
            their_rooms = SubjectRoom.objects.filter(teacher=user)
            return qs.filter(subject_room__in=their_rooms)

        # Students can also see class context for rooms they're enrolled in
        if user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            enrolled_rooms = SubjectRoom.objects.filter(classroom__students=user)
            return qs.filter(subject_room__in=enrolled_rooms)

        return ClassInsight.objects.none()

    @action(detail=False, url_path=r"by-room/(?P<subject_room_id>\d+)")
    def by_room(self, request, subject_room_id=None):
        subject_room = get_object_or_404(SubjectRoom, pk=subject_room_id)
        qs = self.get_queryset().filter(subject_room=subject_room)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class PerformancePredictionViewSet(ReadOnlyModelViewSet):
    """
    list:     GET /api/v1/ai/predictions/       — student's own predictions
    retrieve: GET /api/v1/ai/predictions/{id}/  — single prediction
    """

    serializer_class = PerformancePredictionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = PerformancePrediction.objects.select_related("subject_room__subject").order_by("readiness_level")

        if user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return qs.filter(student=user)

        if user.role == UserRole.TEACHER:
            their_rooms = SubjectRoom.objects.filter(teacher=user)
            return qs.filter(subject_room__in=their_rooms)

        return PerformancePrediction.objects.none()


class AnalysisTriggerViewSet(ViewSet):
    """
    POST /api/v1/ai/trigger/student/   — trigger gap+prediction analysis for current student
    POST /api/v1/ai/trigger/class/     — trigger class insight analysis for a subject room
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="student")
    def trigger_student(self, request):
        serializer = TriggerAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_room_id = serializer.validated_data["subject_room_id"]
        user = request.user

        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return Response(
                {"detail": "Only students can trigger personal analysis."},
                status=status.HTTP_403_FORBIDDEN,
            )

        subject_room = get_object_or_404(SubjectRoom, pk=subject_room_id)

        # Verify student is enrolled in this room (directly or via classroom)
        enrolled = (
            subject_room.students.filter(pk=user.pk).exists()
            or subject_room.classroom.students.filter(pk=user.pk).exists()
        )
        if not enrolled:
            return Response(
                {"detail": "You are not enrolled in this subject room."},
                status=status.HTTP_403_FORBIDDEN,
            )

        analyze_student_subject_room.delay(user.pk, subject_room.pk)
        return Response({"detail": "Analysis queued."}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["post"], url_path="class")
    def trigger_class(self, request):
        serializer = TriggerAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_room_id = serializer.validated_data["subject_room_id"]
        user = request.user

        if user.role != UserRole.TEACHER:
            return Response(
                {"detail": "Only teachers can trigger class analysis."},
                status=status.HTTP_403_FORBIDDEN,
            )

        subject_room = get_object_or_404(SubjectRoom, pk=subject_room_id)

        # Verify teacher owns this room
        is_teacher = subject_room.teacher_id == user.pk
        if not is_teacher:
            return Response(
                {"detail": "You do not teach this subject room."},
                status=status.HTTP_403_FORBIDDEN,
            )

        generate_class_insights_for_subject_room.delay(subject_room.pk)
        return Response({"detail": "Class analysis queued."}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=["post"], url_path="recommendations")
    def trigger_recommendations(self, request):
        """
        POST /api/v1/ai/trigger/recommendations/
        Refresh content recommendations and queue daily practice plan generation.
        """
        serializer = TriggerRecommendationsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_room_id = serializer.validated_data["subject_room_id"]
        user = request.user

        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return Response(
                {"detail": "Only students can trigger recommendations."},
                status=status.HTTP_403_FORBIDDEN,
            )

        subject_room = get_object_or_404(SubjectRoom, pk=subject_room_id)

        enrolled = (
            subject_room.students.filter(pk=user.pk).exists()
            or subject_room.classroom.students.filter(pk=user.pk).exists()
        )
        if not enrolled:
            return Response(
                {"detail": "You are not enrolled in this subject room."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh_recommendations_for_student.delay(user.pk, subject_room.pk)
        generate_daily_practice_plan.delay(user.pk, subject_room.pk)
        return Response(
            {"detail": "Recommendations and practice plan generation queued."},
            status=status.HTTP_202_ACCEPTED,
        )


class ContentRecommendationViewSet(ReadOnlyModelViewSet):
    """
    list:     GET /api/v1/ai/recommendations/        — student's active recommendations
    retrieve: GET /api/v1/ai/recommendations/{id}/   — single recommendation

    Query params:
      ?include_inactive=true  — include superseded recommendations (default: active only)

    Custom action:
      POST /api/v1/ai/recommendations/{id}/action/   — mark a recommendation as actioned
    """

    serializer_class = ContentRecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        include_inactive = self.request.query_params.get("include_inactive", "").lower() == "true"

        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return ContentRecommendation.objects.none()

        qs = (
            ContentRecommendation.objects.select_related("chapter__subject", "problem_set")
            .filter(student=user)
            .order_by("priority", "score_snapshot")
        )

        if not include_inactive:
            qs = qs.filter(is_active=True)

        return qs

    @action(detail=True, methods=["post"])
    def action(self, request, pk=None):
        """Mark this recommendation as actioned (student opened / started the problem set)."""
        from django.utils import timezone

        rec = self.get_object()
        if not rec.is_actioned:
            rec.is_actioned = True
            rec.actioned_at = timezone.now()
            rec.save(update_fields=["is_actioned", "actioned_at"])
        return Response(self.get_serializer(rec).data)


class PracticePlanViewSet(ReadOnlyModelViewSet):
    """
    list:     GET /api/v1/ai/practice-plans/         — student's practice plans
    retrieve: GET /api/v1/ai/practice-plans/{id}/    — single plan

    Custom action:
      GET  /api/v1/ai/practice-plans/today/           — today's plan (auto-triggers generation)
      POST /api/v1/ai/practice-plans/today/complete/  — mark today's plan as completed
    """

    serializer_class = PracticePlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return PracticePlan.objects.none()
        return (
            PracticePlan.objects.prefetch_related("recommendations__chapter__subject")
            .filter(student=user)
            .order_by("-plan_date")
        )

    @action(detail=False, methods=["get"], url_path="today")
    def today(self, request):
        """Return today's practice plan; if none exists, return 204 with a generation hint."""
        from django.utils import timezone

        user = request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return Response(
                {"detail": "Only students have practice plans."},
                status=status.HTTP_403_FORBIDDEN,
            )

        today = timezone.localdate()
        try:
            plan = PracticePlan.objects.prefetch_related("recommendations__chapter__subject").get(
                student=user, plan_date=today
            )
            return Response(self.get_serializer(plan).data)
        except PracticePlan.DoesNotExist:
            return Response(
                {"detail": "No practice plan for today yet. Trigger generation via POST /ai/trigger/recommendations/."},
                status=status.HTTP_404_NOT_FOUND,
            )


# ─────────────────────────────────────────────────────────────────────────────
# Adaptive Learning Engine Views
# ─────────────────────────────────────────────────────────────────────────────


class KnowledgeNodeViewSet(ReadOnlyModelViewSet):
    """
    list:     GET /api/v1/ai/knowledge-nodes/          — nodes for a subject
    retrieve: GET /api/v1/ai/knowledge-nodes/{id}/

    Query params:
      ?subject_id=<int>   — filter by subject (required for useful results)
    """

    serializer_class = KnowledgeNodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = KnowledgeNode.objects.select_related("subject", "chapter").prefetch_related("prerequisites")
        subject_id = self.request.query_params.get("subject_id")
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        return qs.filter(is_active=True).order_by("chapter__order", "chapter__name")


class StudentMasteryViewSet(ReadOnlyModelViewSet):
    """
    list:     GET /api/v1/ai/mastery/         — student's mastery levels for all nodes
    retrieve: GET /api/v1/ai/mastery/{id}/

    Query params:
      ?mastery_level=<level>   — filter: unknown | novice | developing | proficient | mastered
    """

    serializer_class = StudentMasterySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return StudentMastery.objects.none()

        qs = StudentMastery.objects.select_related("knowledge_node__chapter", "knowledge_node__subject").filter(
            student=user
        )

        mastery_level = self.request.query_params.get("mastery_level")
        if mastery_level:
            qs = qs.filter(mastery_level=mastery_level)

        return qs.order_by("knowledge_node__chapter__order")


class SpacedRepetitionViewSet(ReadOnlyModelViewSet):
    """
    list:     GET /api/v1/ai/spaced-repetition/         — student's SRS entries
    retrieve: GET /api/v1/ai/spaced-repetition/{id}/

    Custom action:
      GET /api/v1/ai/spaced-repetition/due/  — entries due for review today/soon
    """

    serializer_class = SpacedRepetitionEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return SpacedRepetitionEntry.objects.none()
        return (
            SpacedRepetitionEntry.objects.select_related("knowledge_node__chapter")
            .filter(student=user)
            .order_by("next_review_date")
        )

    @action(detail=True, methods=["get"], url_path="review")
    def review(self, request, pk=None):
        """
        GET /api/v1/ai/spaced-repetition/{id}/review/
        Returns up to 5 questions from the chapter associated with this SRS entry.
        Only the owning student may access this — uses student-safe serializer
        (no correct_answer exposed; grading happens in mark_reviewed).
        """
        entry = self.get_object()
        if entry.student_id != request.user.id:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        from openshiksha.apps.api.serializers.core import QuestionWithSubpartsStudentSerializer
        from openshiksha.apps.core.models import Question

        questions = list(
            Question.objects.filter(
                chapter=entry.knowledge_node.chapter,
                is_active=True,
            )
            .prefetch_related("subparts__tags", "tags")
            .order_by("?")[:5]
        )

        return Response(
            {
                "entry_id": entry.id,
                "chapter_name": entry.knowledge_node.chapter.name,
                "subject_name": entry.knowledge_node.subject.name,
                "questions": QuestionWithSubpartsStudentSerializer(
                    questions, many=True, context={"request": request}
                ).data,
            }
        )

    @action(detail=True, methods=["post"], url_path="mark-reviewed")
    def mark_reviewed(self, request, pk=None):
        """
        POST /api/v1/ai/spaced-repetition/{id}/mark-reviewed/

        Two accepted body shapes:
          {"answers": {"<subpart_id>": "<student_answer>", ...}}  (preferred — server grades)
          {"score": 0.8}                                          (fallback — client-supplied score)

        Updates SM-2 schedule:
          score >= 0.6 → successful recall, interval grows
          score <  0.6 → failed recall, reset to interval=1
        """
        entry = self.get_object()
        if entry.student_id != request.user.id:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        from datetime import timedelta

        from django.utils import timezone

        from openshiksha.apps.core.models import QuestionSubpart
        from openshiksha.apps.core.tasks import _grade_subpart

        answers = request.data.get("answers")
        # per_subpart_fractions: subpart_id → grade fraction (populated when answers provided)
        per_subpart_fractions: dict[int, float] = {}
        graded_subparts: list = []

        if answers is not None:
            if not isinstance(answers, dict):
                return Response({"detail": "answers must be an object."}, status=400)
            if not answers:
                return Response({"detail": "answers must not be empty."}, status=400)
            subparts = list(
                QuestionSubpart.objects.select_related("question").filter(
                    id__in=[int(k) for k in answers.keys() if str(k).isdigit()],
                    question__chapter=entry.knowledge_node.chapter,
                )
            )
            total = 0
            correct_sum = 0.0
            for subpart in subparts:
                student_answer = answers.get(str(subpart.id))
                if student_answer is None or student_answer == "":
                    total += 1
                    continue
                fraction = _grade_subpart(
                    question_type=subpart.question.question_type,
                    student_answer=student_answer,
                    correct_answer=subpart.correct_answer or {},
                    student_id=request.user.id,
                    subpart_id=subpart.id,
                    original_options=subpart.options,
                    variable_constraints=subpart.variable_constraints,
                )
                per_subpart_fractions[subpart.id] = fraction
                graded_subparts.append(subpart)
                correct_sum += fraction
                total += 1
            if total == 0:
                return Response({"detail": "no valid subparts to grade."}, status=400)
            score = correct_sum / total
        else:
            raw_score = request.data.get("score")
            try:
                score = float(raw_score)
                if not (0.0 <= score <= 1.0):
                    raise ValueError()
            except (TypeError, ValueError):
                return Response(
                    {"detail": "Provide either answers (object) or score (0.0–1.0)."},
                    status=400,
                )

        if score >= 0.60:
            if entry.repetitions == 0:
                new_interval = 1
            elif entry.repetitions == 1:
                new_interval = 6
            else:
                new_interval = max(1, round(entry.interval_days * entry.easiness_factor))
            new_ef = max(1.3, entry.easiness_factor + 0.1 - (1 - score) * 0.8)
            new_reps = entry.repetitions + 1
        else:
            new_interval = 1
            new_ef = entry.easiness_factor
            new_reps = 0

        entry.interval_days = new_interval
        entry.easiness_factor = new_ef
        entry.repetitions = new_reps
        entry.next_review_date = timezone.localdate() + timedelta(days=new_interval)
        entry.last_reviewed_at = timezone.now()
        entry.save(
            update_fields=[
                "interval_days",
                "easiness_factor",
                "repetitions",
                "next_review_date",
                "last_reviewed_at",
                "updated_at",
            ]
        )

        # Side effects: proficiency engine and streak
        if graded_subparts:
            from openshiksha.apps.core.models import SubjectRoom
            from openshiksha.apps.core.tasks import update_proficiency
            from openshiksha.apps.edge.models import Tick

            subject_room = (
                SubjectRoom.objects.filter(
                    students=entry.student,
                    subject=entry.knowledge_node.chapter.subject,
                )
                .order_by("-id")
                .first()
            )
            if subject_room:
                ticks = [
                    Tick(
                        student=entry.student,
                        question_subpart=sp,
                        submission=None,
                        subject_room=subject_room,
                        mark=per_subpart_fractions[sp.id],
                    )
                    for sp in graded_subparts
                ]
                Tick.objects.bulk_create(ticks)
                update_proficiency.delay(entry.student_id, subject_room.id)

        from openshiksha.apps.core.models import StudentStreak

        streak_obj, _ = StudentStreak.objects.get_or_create(student=entry.student)
        streak_obj.record_activity(timezone.localdate())

        data = self.get_serializer(entry).data
        data["score"] = round(score, 4)
        return Response(data)

    @action(detail=False, methods=["get"], url_path="due")
    def due(self, request):
        """Return SRS entries due for review today or in the next 3 days."""
        from datetime import timedelta

        from django.utils import timezone

        user = request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return Response(
                {"detail": "Only students have SRS entries."},
                status=status.HTTP_403_FORBIDDEN,
            )

        lookahead = timezone.localdate() + timedelta(days=3)
        entries = (
            SpacedRepetitionEntry.objects.select_related("knowledge_node__chapter")
            .filter(student=user, next_review_date__lte=lookahead)
            .order_by("next_review_date")
        )

        return Response(self.get_serializer(entries, many=True).data)


class LearningPathViewSet(ReadOnlyModelViewSet):
    """
    list:     GET /api/v1/ai/learning-paths/          — student's learning paths
    retrieve: GET /api/v1/ai/learning-paths/{id}/

    Custom actions:
      GET  /api/v1/ai/learning-paths/active/         — current active path
      POST /api/v1/ai/learning-paths/rebuild/        — trigger path regeneration
      POST /api/v1/ai/learning-paths/steps/{id}/complete/ — mark a step complete
    """

    serializer_class = LearningPathSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return LearningPath.objects.none()
        return (
            LearningPath.objects.prefetch_related(
                "steps__knowledge_node__chapter",
                "steps__knowledge_node__subject",
                "steps__problem_set",
            )
            .filter(student=user)
            .order_by("-generated_at")
        )

    @action(detail=False, methods=["get"], url_path="active")
    def active(self, request):
        """Return the current ACTIVE learning path for the student."""
        user = request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return Response(
                {"detail": "Only students have learning paths."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            path = LearningPath.objects.prefetch_related(
                "steps__knowledge_node__chapter",
                "steps__knowledge_node__subject",
                "steps__problem_set",
            ).get(student=user, status=LearningPathStatus.ACTIVE)
            return Response(self.get_serializer(path).data)
        except LearningPath.DoesNotExist:
            return Response(
                {"detail": "No active learning path. POST to /ai/learning-paths/rebuild/ to generate one."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["post"], url_path="rebuild")
    def rebuild(self, request):
        """Trigger async regeneration of the student's learning path."""
        serializer = TriggerAdaptiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return Response(
                {"detail": "Only students can rebuild their learning paths."},
                status=status.HTTP_403_FORBIDDEN,
            )

        subject_room_id = serializer.validated_data["subject_room_id"]
        subject_room = get_object_or_404(SubjectRoom, pk=subject_room_id)

        rebuild_learning_path.delay(user.pk, subject_room.pk)

        return Response(
            {"detail": "Learning path regeneration queued."},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["post"], url_path="steps/(?P<step_pk>[^/.]+)/complete")
    def complete_step(self, request, step_pk=None):
        """
        Mark a LearningPathStep as completed with a score.

        POST /api/v1/ai/learning-paths/steps/{step_id}/complete/
        Body: {"score": 0.85}
        """
        step = get_object_or_404(
            LearningPathStep,
            pk=step_pk,
            learning_path__student=request.user,
        )

        serializer = CompleteStepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        score = serializer.validated_data["score"]
        complete_learning_path_step.delay(step.pk, score)

        return Response(
            {"detail": f"Step {step.pk} completion queued with score {score}."},
            status=status.HTTP_202_ACCEPTED,
        )
