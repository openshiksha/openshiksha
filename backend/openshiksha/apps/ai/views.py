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

from django.db import transaction
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, ViewSet

from openshiksha.apps.ai.llm_client import generate_hint_sequence, generate_questions, generate_tutor_reply
from openshiksha.apps.core.models import (
    Assignment,
    Chapter,
    ProblemSet,
    Question,
    QuestionSubpart,
    SubjectRoom,
    User,
    UserRole,
)

from .models import (
    AssignmentDraft,
    AssignmentDraftStatus,
    CalibrationFlag,
    ClassInsight,
    ClassMisconceptionCluster,
    ContentRecommendation,
    HintSequence,
    InterventionStatus,
    InterventionSuggestion,
    KnowledgeNode,
    LearningGap,
    LearningPath,
    LearningPathStatus,
    LearningPathStep,
    OpenResponseGrade,
    OpenResponseGradeStatus,
    OpenResponseRubric,
    ParentProgressSummary,
    PerformancePrediction,
    PracticePlan,
    QuestionDifficultyCalibration,
    SpacedRepetitionEntry,
    StudentMastery,
    StudentMisconception,
    SubpartExplanation,
    TutorConversation,
    TutorMessage,
    TutorMessageRole,
    WeeklyClassReport,
)
from .serializers import (
    ApproveAssignmentDraftSerializer,
    AssignmentDraftSerializer,
    ClassInsightSerializer,
    ClassMisconceptionClusterSerializer,
    CompleteStepSerializer,
    ContentRecommendationSerializer,
    DiagnoseMisconceptionSerializer,
    GenerateAssignmentDraftSerializer,
    GeneratedQuestionDraftSerializer,
    GenerateExplanationSerializer,
    GenerateHintsSerializer,
    GenerateParentSummarySerializer,
    GenerateQuestionsRequestSerializer,
    HintSequenceSerializer,
    InterventionSuggestionSerializer,
    KnowledgeNodeSerializer,
    LearningGapSerializer,
    LearningPathSerializer,
    OpenResponseGradeSerializer,
    OpenResponseRubricSerializer,
    ParentProgressSummarySerializer,
    PerformancePredictionSerializer,
    PostTutorMessageSerializer,
    PracticePlanSerializer,
    QuestionDifficultyCalibrationSerializer,
    ReviewOpenResponseSerializer,
    SpacedRepetitionEntrySerializer,
    StartTutorConversationSerializer,
    StudentMasterySerializer,
    StudentMisconceptionSerializer,
    SubmitOpenResponseSerializer,
    SubpartExplanationSerializer,
    TriggerAdaptiveSerializer,
    TriggerAnalysisSerializer,
    TriggerDifficultyCalibrationSerializer,
    TriggerInterventionsSerializer,
    TriggerMisconceptionClusterSerializer,
    TriggerRecommendationsSerializer,
    TriggerWeeklyReportSerializer,
    TutorConversationListSerializer,
    TutorConversationSerializer,
    UpdateInterventionStatusSerializer,
    WeeklyClassReportSerializer,
)
from .tasks import (
    analyze_student_subject_room,
    build_assignment_draft,
    complete_learning_path_step,
    diagnose_misconception_for_subpart,
    generate_class_insights_for_subject_room,
    generate_daily_practice_plan,
    generate_explanation_for_subpart,
    generate_interventions_for_subject_room,
    generate_parent_progress_summary,
    generate_weekly_class_report,
    grade_open_response,
    rebuild_learning_path,
    refresh_class_misconception_clusters,
    refresh_difficulty_calibrations,
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


class SubpartExplanationViewSet(ReadOnlyModelViewSet):
    """
    Natural language explanations for student answers.

    list:     GET /api/v1/ai/explanations/                      — student's own explanations
              GET /api/v1/ai/explanations/?submission=<id>      — filter by submission
              GET /api/v1/ai/explanations/?subpart=<id>         — filter by subpart
    retrieve: GET /api/v1/ai/explanations/{id}/                 — single explanation
    generate: POST /api/v1/ai/explanations/generate/            — on-demand for SRS drill

    Only students (or open_students) can access their own explanations.
    """

    serializer_class = SubpartExplanationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return SubpartExplanation.objects.none()

        qs = (
            SubpartExplanation.objects.filter(student=user)
            .select_related(
                "question_subpart",
            )
            .order_by("-generated_at")
        )

        if submission_id := self.request.query_params.get("submission"):
            qs = qs.filter(submission_id=submission_id)
        if subpart_id := self.request.query_params.get("subpart"):
            qs = qs.filter(question_subpart_id=subpart_id)

        return qs

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        """
        POST /api/v1/ai/explanations/generate/

        Trigger on-demand explanation for a single subpart (e.g., SRS drill).
        Body: {subpart_id, student_answer, is_correct, grade_level?, language?}

        Returns 202 Accepted with the queued task description.
        """
        user = request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return Response({"detail": "Only students can request explanations."}, status=403)

        serializer = GenerateExplanationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        from openshiksha.apps.core.models import QuestionSubpart

        try:
            QuestionSubpart.objects.get(pk=d["subpart_id"])
        except QuestionSubpart.DoesNotExist:
            return Response({"detail": "Subpart not found."}, status=404)

        grade_level = d.get("grade_level") or user.grade or 8

        generate_explanation_for_subpart.delay(
            student_id=user.pk,
            subpart_id=d["subpart_id"],
            student_answer=d["student_answer"],
            is_correct=d["is_correct"],
            grade_level=grade_level,
            language=d.get("language", "en"),
        )

        return Response(
            {"detail": "Explanation generation queued."},
            status=status.HTTP_202_ACCEPTED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# AI Question Generation
# ─────────────────────────────────────────────────────────────────────────────


class GenerateQuestionsViewSet(ViewSet):
    """
    POST /api/v1/ai/generate-questions/   — teacher-only

    Generates question drafts using Claude AI.  Returns an array of draft
    objects that the teacher can review, edit, and save.

    Request body:
        topic          string     free-text description of the question topic
        chapter_id     int        FK to Chapter
        question_type  string     mcq | fill_blank | numeric | multi_select
        difficulty     int        1–5 (default 2)
        count          int        1–5 (default 3)

    Response: 200 with {"questions": [...draft objects...]}
    """

    permission_classes = [IsAuthenticated]

    def create(self, request):
        if request.user.role != UserRole.TEACHER:
            return Response(
                {"detail": "Only teachers can generate questions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = GenerateQuestionsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        chapter = get_object_or_404(
            Chapter.objects.select_related("subject", "standard"),
            pk=d["chapter_id"],
        )

        try:
            drafts = generate_questions(
                topic=d["topic"],
                chapter_name=chapter.name,
                subject_name=chapter.subject.name,
                standard_number=chapter.standard.number,
                question_type=d["question_type"],
                difficulty=d["difficulty"],
                count=d["count"],
            )
        except Exception:
            import logging

            logging.getLogger(__name__).exception("generate_questions: unexpected error")
            return Response(
                {"detail": "Question generation failed. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        out_serializer = GeneratedQuestionDraftSerializer(data=drafts, many=True)
        out_serializer.is_valid()
        return Response({"questions": out_serializer.data})


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Weekly Class Reports
# ─────────────────────────────────────────────────────────────────────────────


class WeeklyClassReportViewSet(ReadOnlyModelViewSet):
    """
    AI-generated weekly class summary reports — teacher-only.

    list:     GET  /api/v1/ai/weekly-reports/                    — reports for teacher's rooms
              GET  /api/v1/ai/weekly-reports/?subject_room=<id>  — filter by room
    retrieve: GET  /api/v1/ai/weekly-reports/{id}/               — single report
    latest:   GET  /api/v1/ai/weekly-reports/latest/?subject_room=<id>
                                                                 — most recent report for a room
    generate: POST /api/v1/ai/weekly-reports/generate/           — queue report generation
                  body: {subject_room_id, week_start?}

    A teacher only ever sees reports for SubjectRooms they teach.
    """

    serializer_class = WeeklyClassReportSerializer
    permission_classes = [IsAuthenticated]

    def _teacher_rooms(self):
        return SubjectRoom.objects.filter(teacher=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.role != UserRole.TEACHER:
            return WeeklyClassReport.objects.none()

        qs = WeeklyClassReport.objects.select_related(
            "subject_room__subject",
            "subject_room__classroom__standard",
            "subject_room__classroom__school",
        ).filter(subject_room__teacher=user)

        if subject_room_id := self.request.query_params.get("subject_room"):
            qs = qs.filter(subject_room_id=subject_room_id)

        return qs.order_by("-week_start")

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """Return the most recent report for a given subject_room."""
        if request.user.role != UserRole.TEACHER:
            return Response({"detail": "Only teachers have class reports."}, status=status.HTTP_403_FORBIDDEN)

        subject_room_id = request.query_params.get("subject_room")
        if not subject_room_id:
            return Response({"detail": "subject_room query param is required."}, status=status.HTTP_400_BAD_REQUEST)

        report = self.get_queryset().filter(subject_room_id=subject_room_id).first()
        if report is None:
            return Response(
                {"detail": "No report yet. Generate one via POST /ai/weekly-reports/generate/."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(self.get_serializer(report).data)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Queue async generation of a weekly report for a SubjectRoom the teacher owns."""
        if request.user.role != UserRole.TEACHER:
            return Response({"detail": "Only teachers can generate class reports."}, status=status.HTTP_403_FORBIDDEN)

        serializer = TriggerWeeklyReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_room_id = serializer.validated_data["subject_room_id"]
        subject_room = get_object_or_404(SubjectRoom, pk=subject_room_id)

        if subject_room.teacher_id != request.user.pk:
            return Response(
                {"detail": "You do not teach this subject room."},
                status=status.HTTP_403_FORBIDDEN,
            )

        week_start = serializer.validated_data.get("week_start")
        generate_weekly_class_report.delay(
            subject_room.pk,
            week_start.isoformat() if week_start else None,
        )
        return Response(
            {"detail": "Weekly report generation queued."},
            status=status.HTTP_202_ACCEPTED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Intelligent Hint System
# ─────────────────────────────────────────────────────────────────────────────


class HintSequenceViewSet(ReadOnlyModelViewSet):
    """
    Progressive AI hints for question subparts.

    list:     GET  /api/v1/ai/hints/?subpart=<id>   — cached hint sequence for a subpart
    retrieve: GET  /api/v1/ai/hints/{id}/           — single hint sequence
    generate: POST /api/v1/ai/hints/generate/       — synchronous generate-or-fetch

    Hints are student-agnostic and cached per subpart, so the first request for a
    subpart generates and stores them; later requests (by any student) reuse the
    cached sequence. The payload never includes the correct answer.

    Only students (and open_students) may access this.
    """

    serializer_class = HintSequenceSerializer
    permission_classes = [IsAuthenticated]

    def _student_only(self, user):
        return user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT)

    def get_queryset(self):
        user = self.request.user
        if not self._student_only(user):
            return HintSequence.objects.none()

        qs = HintSequence.objects.select_related("question_subpart").all()
        if subpart_id := self.request.query_params.get("subpart"):
            qs = qs.filter(question_subpart_id=subpart_id)
        return qs.order_by("-generated_at")

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        """
        POST /api/v1/ai/hints/generate/
        Body: {subpart_id, num_hints?, grade_level?}

        Returns 200 with the cached hint sequence if one already exists for the
        subpart, otherwise generates synchronously, caches, and returns it.
        """
        user = request.user
        if not self._student_only(user):
            return Response({"detail": "Only students can request hints."}, status=status.HTTP_403_FORBIDDEN)

        serializer = GenerateHintsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        from openshiksha.apps.core.models import QuestionSubpart

        try:
            subpart = QuestionSubpart.objects.select_related("question").get(pk=d["subpart_id"])
        except QuestionSubpart.DoesNotExist:
            return Response({"detail": "Subpart not found."}, status=status.HTTP_404_NOT_FOUND)

        existing = HintSequence.objects.filter(question_subpart=subpart).first()
        if existing:
            return Response(self.get_serializer(existing).data)

        grade_level = d.get("grade_level") or user.grade or 8
        try:
            result = generate_hint_sequence(
                question_text=subpart.question_text or subpart.question.question_type,
                options=subpart.options,
                correct_answer=subpart.correct_answer or {},
                grade_level=grade_level,
                num_hints=d["num_hints"],
                static_hint=subpart.hint_text or "",
            )
        except Exception:
            import logging

            logging.getLogger(__name__).exception("generate_hint_sequence: unexpected error")
            return Response(
                {"detail": "Hint generation failed. Please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        obj, _ = HintSequence.objects.update_or_create(
            question_subpart=subpart,
            defaults={
                "hints": result["hints"],
                "grade_level": grade_level,
                "model_used": result["model"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
            },
        )
        return Response(self.get_serializer(obj).data, status=status.HTTP_201_CREATED)


class StudentMisconceptionViewSet(ReadOnlyModelViewSet):
    """
    AI misconception diagnoses for wrong answers.

    list:     GET  /api/v1/ai/misconceptions/                  — student's own (or teacher's students')
              GET  /api/v1/ai/misconceptions/?subpart=<id>
    retrieve: GET  /api/v1/ai/misconceptions/{id}/
    diagnose: POST /api/v1/ai/misconceptions/diagnose/         — queue async diagnosis (students only)
                  body: {subpart_id, student_answer, submission_id?, grade_level?}

    Students see their own diagnoses; teachers see diagnoses for students in the
    subject rooms they teach (to surface shared misconceptions across the class).
    """

    serializer_class = StudentMisconceptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = StudentMisconception.objects.select_related("question_subpart", "student").order_by("-detected_at")

        if user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            qs = qs.filter(student=user)
        elif user.role == UserRole.TEACHER:
            from openshiksha.apps.core.models import Question

            taught_chapters = Question.objects.filter(
                subparts__misconceptions__isnull=False,
                chapter__subject__subject_rooms__teacher=user,
            ).values_list("chapter_id", flat=True)
            qs = qs.filter(question_subpart__question__chapter_id__in=list(taught_chapters))
        else:
            return StudentMisconception.objects.none()

        if subpart_id := self.request.query_params.get("subpart"):
            qs = qs.filter(question_subpart_id=subpart_id)
        return qs

    @action(detail=False, methods=["post"], url_path="diagnose")
    def diagnose(self, request):
        """Queue async misconception diagnosis for the current student's wrong answer."""
        user = request.user
        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return Response({"detail": "Only students can request diagnoses."}, status=status.HTTP_403_FORBIDDEN)

        serializer = DiagnoseMisconceptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        from openshiksha.apps.core.models import QuestionSubpart

        try:
            QuestionSubpart.objects.get(pk=d["subpart_id"])
        except QuestionSubpart.DoesNotExist:
            return Response({"detail": "Subpart not found."}, status=status.HTTP_404_NOT_FOUND)

        grade_level = d.get("grade_level") or user.grade or 8
        diagnose_misconception_for_subpart.delay(
            student_id=user.pk,
            subpart_id=d["subpart_id"],
            student_answer=d["student_answer"],
            grade_level=grade_level,
            submission_id=d.get("submission_id"),
        )
        return Response({"detail": "Misconception diagnosis queued."}, status=status.HTTP_202_ACCEPTED)


# ─────────────────────────────────────────────────────────────────────────────
# Parent Intelligence Dashboard
# ─────────────────────────────────────────────────────────────────────────────


class ParentProgressSummaryViewSet(ReadOnlyModelViewSet):
    """
    AI-generated weekly progress summaries for parents — parent-only.

    list:     GET  /api/v1/ai/parent-summaries/                  — summaries for all this parent's children
              GET  /api/v1/ai/parent-summaries/?child=<id>       — summaries for one child
    retrieve: GET  /api/v1/ai/parent-summaries/{id}/             — single summary
    latest:   GET  /api/v1/ai/parent-summaries/latest/?child=<id>
                                                                 — most recent summary for one child
    generate: POST /api/v1/ai/parent-summaries/generate/         — queue summary generation
                  body: {child_id, week_start?, language?}

    A parent only ever sees summaries about children linked via User.children.
    """

    serializer_class = ParentProgressSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != UserRole.PARENT:
            return ParentProgressSummary.objects.none()

        qs = ParentProgressSummary.objects.select_related("child").filter(parent=user)

        if child_id := self.request.query_params.get("child"):
            qs = qs.filter(child_id=child_id)

        return qs.order_by("-week_start")

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """Return the most recent summary for one child."""
        if request.user.role != UserRole.PARENT:
            return Response(
                {"detail": "Only parents have progress summaries."},
                status=status.HTTP_403_FORBIDDEN,
            )

        child_id = request.query_params.get("child")
        if not child_id:
            return Response(
                {"detail": "child query param is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        summary = self.get_queryset().filter(child_id=child_id).first()
        if summary is None:
            return Response(
                {"detail": "No summary yet. Generate one via POST /ai/parent-summaries/generate/."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(self.get_serializer(summary).data)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Queue async generation of a weekly summary for one of the parent's children."""
        if request.user.role != UserRole.PARENT:
            return Response(
                {"detail": "Only parents can generate parent summaries."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = GenerateParentSummarySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        child_id = serializer.validated_data["child_id"]
        if not request.user.children.filter(pk=child_id).exists():
            return Response(
                {"detail": "This child is not linked to your account."},
                status=status.HTTP_403_FORBIDDEN,
            )

        week_start = serializer.validated_data.get("week_start")
        language = serializer.validated_data.get("language", "en")
        generate_parent_progress_summary.delay(
            request.user.pk,
            child_id,
            week_start.isoformat() if week_start else None,
            language,
        )
        return Response(
            {"detail": "Parent progress summary generation queued."},
            status=status.HTTP_202_ACCEPTED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Class Misconception Insights — teacher-only
# ─────────────────────────────────────────────────────────────────────────────


class ClassMisconceptionClusterViewSet(ReadOnlyModelViewSet):
    """
    Class-level misconception clusters for a teacher's SubjectRooms.

    list:     GET  /api/v1/ai/misconception-clusters/                    — all clusters across teacher's rooms
              GET  /api/v1/ai/misconception-clusters/?subject_room=<id>  — filter by room
    retrieve: GET  /api/v1/ai/misconception-clusters/{id}/
    refresh:  POST /api/v1/ai/misconception-clusters/refresh/            — queue async recompute
                  body: {subject_room_id, lookback_days?}

    Teachers only ever see clusters for SubjectRooms they teach. The underlying
    per-student StudentMisconception rows already have their own permission
    boundary; this endpoint is the aggregated teacher view.
    """

    serializer_class = ClassMisconceptionClusterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != UserRole.TEACHER:
            return ClassMisconceptionCluster.objects.none()

        qs = ClassMisconceptionCluster.objects.select_related(
            "subject_room__subject",
        ).filter(subject_room__teacher=user)

        if subject_room_id := self.request.query_params.get("subject_room"):
            qs = qs.filter(subject_room_id=subject_room_id)

        return qs

    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request):
        """Queue async recomputation of clusters for a SubjectRoom the teacher owns."""
        if request.user.role != UserRole.TEACHER:
            return Response(
                {"detail": "Only teachers can refresh class misconception clusters."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TriggerMisconceptionClusterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_room = get_object_or_404(SubjectRoom, pk=serializer.validated_data["subject_room_id"])
        if subject_room.teacher_id != request.user.pk:
            return Response(
                {"detail": "You do not teach this subject room."},
                status=status.HTTP_403_FORBIDDEN,
            )

        lookback_days = serializer.validated_data.get("lookback_days")
        refresh_class_misconception_clusters.delay(subject_room.pk, lookback_days)
        return Response(
            {"detail": "Class misconception cluster refresh queued."},
            status=status.HTTP_202_ACCEPTED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Empirical Question Difficulty Calibration
# ─────────────────────────────────────────────────────────────────────────────


class QuestionDifficultyCalibrationViewSet(ReadOnlyModelViewSet):
    """
    Empirical item-analysis calibrations for a teacher's SubjectRooms.

    list:     GET  /api/v1/ai/difficulty-calibrations/                    — all calibrations across teacher's rooms
              GET  /api/v1/ai/difficulty-calibrations/?subject_room=<id>  — filter by room
              GET  /api/v1/ai/difficulty-calibrations/?flag=mislabeled    — filter by quality flag
              GET  /api/v1/ai/difficulty-calibrations/?needs_review=true  — only flagged (non-OK) items
    retrieve: GET  /api/v1/ai/difficulty-calibrations/{id}/
    summary:  GET  /api/v1/ai/difficulty-calibrations/summary/?subject_room=<id>
                  — per-flag counts + totals for a room (dashboard header)
    refresh:  POST /api/v1/ai/difficulty-calibrations/refresh/            — queue async recompute
                  body: {subject_room_id}

    Calibrations are derived purely from the room's grading data (no LLM); a
    teacher only ever sees calibrations for SubjectRooms they teach.
    """

    serializer_class = QuestionDifficultyCalibrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != UserRole.TEACHER:
            return QuestionDifficultyCalibration.objects.none()

        qs = QuestionDifficultyCalibration.objects.select_related(
            "subject_room__subject",
            "question_subpart__question__chapter",
        ).filter(subject_room__teacher=user)

        if subject_room_id := self.request.query_params.get("subject_room"):
            qs = qs.filter(subject_room_id=subject_room_id)
        if flag := self.request.query_params.get("flag"):
            qs = qs.filter(flag=flag)
        if self.request.query_params.get("needs_review", "").lower() == "true":
            qs = qs.exclude(flag=CalibrationFlag.OK)

        return qs

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Per-flag counts and totals for one room — feeds the dashboard header."""
        if request.user.role != UserRole.TEACHER:
            return Response(
                {"detail": "Only teachers have difficulty calibrations."},
                status=status.HTTP_403_FORBIDDEN,
            )

        subject_room_id = request.query_params.get("subject_room")
        if not subject_room_id:
            return Response(
                {"detail": "subject_room query param is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        qs = self.get_queryset().filter(subject_room_id=subject_room_id)
        counts = {flag.value: 0 for flag in CalibrationFlag}
        for row in qs.values("flag").annotate(n=Count("id")):
            counts[row["flag"]] = row["n"]

        total = sum(counts.values())
        flagged = total - counts[CalibrationFlag.OK]
        return Response(
            {
                "subject_room": int(subject_room_id),
                "total_calibrated": total,
                "flagged": flagged,
                "by_flag": counts,
            }
        )

    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request):
        """Queue async recomputation of calibrations for a SubjectRoom the teacher owns."""
        if request.user.role != UserRole.TEACHER:
            return Response(
                {"detail": "Only teachers can refresh difficulty calibrations."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TriggerDifficultyCalibrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_room = get_object_or_404(SubjectRoom, pk=serializer.validated_data["subject_room_id"])
        if subject_room.teacher_id != request.user.pk:
            return Response(
                {"detail": "You do not teach this subject room."},
                status=status.HTTP_403_FORBIDDEN,
            )

        refresh_difficulty_calibrations.delay(subject_room.pk)
        return Response(
            {"detail": "Difficulty calibration refresh queued."},
            status=status.HTTP_202_ACCEPTED,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Auto-Drafted Assignments
# ─────────────────────────────────────────────────────────────────────────────


class AssignmentDraftViewSet(ReadOnlyModelViewSet):
    """
    AI-assembled draft assignments targeting class weaknesses — teacher-only.

    list:     GET  /api/v1/ai/assignment-drafts/                    — drafts for teacher's rooms
              GET  /api/v1/ai/assignment-drafts/?subject_room=<id>  — filter by room
              GET  /api/v1/ai/assignment-drafts/?status=ready       — filter by status
    retrieve: GET  /api/v1/ai/assignment-drafts/{id}/
    generate: POST /api/v1/ai/assignment-drafts/generate/           — queue draft generation
                  body: {subject_room_id, size?, target_difficulty?}
    approve:  POST /api/v1/ai/assignment-drafts/{id}/approve/        — materialise into an Assignment
                  body: {due_at, title?}
    dismiss:  POST /api/v1/ai/assignment-drafts/{id}/dismiss/        — discard the draft

    A teacher only ever sees and acts on drafts for SubjectRooms they teach.
    Generating a draft creates a `pending` row immediately and returns it; the
    selection + rationale are filled in asynchronously (poll until status=ready).
    """

    serializer_class = AssignmentDraftSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != UserRole.TEACHER:
            return AssignmentDraft.objects.none()

        qs = AssignmentDraft.objects.select_related(
            "subject_room__subject",
            "subject_room__classroom__standard",
            "subject_room__classroom__school",
        ).filter(subject_room__teacher=user)

        if subject_room_id := self.request.query_params.get("subject_room"):
            qs = qs.filter(subject_room_id=subject_room_id)
        if status_filter := self.request.query_params.get("status"):
            qs = qs.filter(status=status_filter)

        return qs

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Create a pending draft and queue its async assembly."""
        if request.user.role != UserRole.TEACHER:
            return Response(
                {"detail": "Only teachers can generate assignment drafts."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = GenerateAssignmentDraftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_room = get_object_or_404(SubjectRoom, pk=serializer.validated_data["subject_room_id"])
        if subject_room.teacher_id != request.user.pk:
            return Response(
                {"detail": "You do not teach this subject room."},
                status=status.HTTP_403_FORBIDDEN,
            )

        draft = AssignmentDraft.objects.create(
            subject_room=subject_room,
            requested_by=request.user,
            status=AssignmentDraftStatus.PENDING,
            requested_size=serializer.validated_data.get("size", 8),
            target_difficulty=serializer.validated_data.get("target_difficulty", 2),
        )
        build_assignment_draft.delay(draft.pk)

        return Response(
            self.get_serializer(draft).data,
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Materialise a ready draft into a real ProblemSet + Assignment."""
        draft = self.get_object()  # already scoped to the teacher's rooms

        if draft.status != AssignmentDraftStatus.READY:
            return Response(
                {"detail": f"Only a draft that is ready for review can be approved (status={draft.status})."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = ApproveAssignmentDraftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question_ids = [q["question_id"] for q in draft.selected_questions]
        questions = list(Question.objects.filter(id__in=question_ids, is_active=True))
        if not questions:
            return Response(
                {"detail": "None of the draft's questions are still active. Regenerate the draft."},
                status=status.HTTP_409_CONFLICT,
            )

        subject_room = draft.subject_room
        classroom = subject_room.classroom
        # Anchor the ProblemSet on the weakest targeted chapter; questions may span
        # several chapters but ProblemSet carries a single chapter for categorisation.
        primary_chapter_id = (
            draft.target_chapters[0]["chapter_id"] if draft.target_chapters else questions[0].chapter_id
        )
        primary_chapter = get_object_or_404(Chapter, pk=primary_chapter_id)

        title = serializer.validated_data.get("title") or draft.title or f"Practice: {primary_chapter.name}"

        with transaction.atomic():
            next_number = (
                ProblemSet.objects.filter(
                    school=classroom.school,
                    standard=classroom.standard,
                    subject=subject_room.subject,
                    chapter=primary_chapter,
                ).aggregate(m=Max("number"))["m"]
                or 0
            ) + 1

            problem_set = ProblemSet.objects.create(
                school=classroom.school,
                standard=classroom.standard,
                subject=subject_room.subject,
                chapter=primary_chapter,
                title=title,
                description=draft.rationale_text,
                number=next_number,
                estimated_minutes=draft.estimated_minutes or None,
                created_by=request.user,
            )
            problem_set.questions.set(questions)

            assignment_number = (
                Assignment.objects.filter(
                    subject_room=subject_room,
                    problem_set=problem_set,
                ).aggregate(
                    m=Max("number")
                )["m"]
                or 0
            ) + 1
            assignment = Assignment.objects.create(
                subject_room=subject_room,
                problem_set=problem_set,
                assigned_by=request.user,
                due_at=serializer.validated_data["due_at"],
                number=assignment_number,
            )

            draft.status = AssignmentDraftStatus.APPROVED
            draft.approved_problem_set = problem_set
            draft.approved_assignment = assignment
            draft.title = title
            draft.save(
                update_fields=[
                    "status",
                    "approved_problem_set",
                    "approved_assignment",
                    "title",
                    "updated_at",
                ]
            )

        return Response(self.get_serializer(draft).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def dismiss(self, request, pk=None):
        """Discard a draft the teacher does not want to use."""
        draft = self.get_object()

        if draft.status == AssignmentDraftStatus.APPROVED:
            return Response(
                {"detail": "An approved draft cannot be dismissed."},
                status=status.HTTP_409_CONFLICT,
            )

        draft.status = AssignmentDraftStatus.DISMISSED
        draft.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(draft).data)


class OpenResponseRubricViewSet(ModelViewSet):
    """
    Grading rubrics for short-answer subparts — teacher-only CRUD.

    list:     GET    /api/v1/ai/open-rubrics/                  — rubrics the teacher authored
              GET    /api/v1/ai/open-rubrics/?subpart=<id>     — filter by subpart
    create:   POST   /api/v1/ai/open-rubrics/                  — {subpart, max_marks, model_answer, criteria}
    update:   PATCH  /api/v1/ai/open-rubrics/{id}/
    destroy:  DELETE /api/v1/ai/open-rubrics/{id}/

    A teacher may only attach a rubric to a subpart of a SHORT_ANSWER question.
    """

    serializer_class = OpenResponseRubricSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != UserRole.TEACHER:
            return OpenResponseRubric.objects.none()
        qs = OpenResponseRubric.objects.select_related("subpart__question").filter(created_by=user)
        if subpart_id := self.request.query_params.get("subpart"):
            qs = qs.filter(subpart_id=subpart_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        if request.user.role != UserRole.TEACHER:
            return Response(
                {"detail": "Only teachers can author grading rubrics."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)


class OpenResponseGradeViewSet(ReadOnlyModelViewSet):
    """
    AI-assisted grading of students' free-text answers — teacher-only.

    list:     GET  /api/v1/ai/open-grades/                       — grades for the teacher's rooms
              GET  /api/v1/ai/open-grades/?subject_room=<id>      — filter by room
              GET  /api/v1/ai/open-grades/?status=ai_graded       — filter by status
              GET  /api/v1/ai/open-grades/?student=<id>           — filter by student
    retrieve: GET  /api/v1/ai/open-grades/{id}/
    submit:   POST /api/v1/ai/open-grades/submit/                 — record a response + queue AI grading
                  body: {subpart_id, student_id, subject_room_id, response_text, assignment_id?}
    regrade:  POST /api/v1/ai/open-grades/{id}/regrade/           — re-run the AI grader
    review:   POST /api/v1/ai/open-grades/{id}/review/            — set final_score and finalise
                  body: {final_score, teacher_comment?}

    The teacher always has the final say: ``review`` writes ``final_score`` and
    flips the row to ``reviewed``. Until then ``effective_score`` reflects the
    AI's suggestion so dashboards have a number to show.
    """

    serializer_class = OpenResponseGradeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != UserRole.TEACHER:
            return OpenResponseGrade.objects.none()

        qs = OpenResponseGrade.objects.select_related(
            "subpart__question",
            "student",
            "subject_room__subject",
        ).filter(subject_room__teacher=user)

        if subject_room_id := self.request.query_params.get("subject_room"):
            qs = qs.filter(subject_room_id=subject_room_id)
        if status_filter := self.request.query_params.get("status"):
            qs = qs.filter(status=status_filter)
        if student_id := self.request.query_params.get("student"):
            qs = qs.filter(student_id=student_id)
        return qs

    @action(detail=False, methods=["post"])
    def submit(self, request):
        """Record a student's free-text answer and queue AI grading."""
        if request.user.role != UserRole.TEACHER:
            return Response(
                {"detail": "Only teachers can submit responses for AI grading."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SubmitOpenResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        subject_room = get_object_or_404(SubjectRoom, pk=data["subject_room_id"])
        if subject_room.teacher_id != request.user.pk:
            return Response(
                {"detail": "You do not teach this subject room."},
                status=status.HTTP_403_FORBIDDEN,
            )

        subpart = get_object_or_404(QuestionSubpart, pk=data["subpart_id"])
        student = get_object_or_404(User, pk=data["student_id"])

        rubric = getattr(subpart, "open_response_rubric", None)
        max_marks = rubric.max_marks if rubric else 5

        assignment = None
        if data.get("assignment_id"):
            assignment = get_object_or_404(Assignment, pk=data["assignment_id"])

        grade = OpenResponseGrade.objects.create(
            subpart=subpart,
            student=student,
            subject_room=subject_room,
            assignment=assignment,
            response_text=data["response_text"],
            max_marks=max_marks,
            status=OpenResponseGradeStatus.PENDING,
        )
        grade_open_response.delay(grade.pk)

        return Response(self.get_serializer(grade).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"])
    def regrade(self, request, pk=None):
        """Re-run the AI grader for a response (e.g. after editing its rubric)."""
        grade = self.get_object()  # scoped to the teacher's rooms
        if grade.status == OpenResponseGradeStatus.REVIEWED:
            return Response(
                {"detail": "A reviewed grade cannot be re-graded. It has been finalised."},
                status=status.HTTP_409_CONFLICT,
            )
        grade.status = OpenResponseGradeStatus.PENDING
        grade.error_detail = ""
        grade.save(update_fields=["status", "error_detail", "updated_at"])
        grade_open_response.delay(grade.pk)
        return Response(self.get_serializer(grade).data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        """Teacher finalises the grade, accepting or overriding the AI's score."""
        grade = self.get_object()

        serializer = ReviewOpenResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        final_score = serializer.validated_data["final_score"]

        if final_score > grade.max_marks:
            return Response(
                {"detail": f"final_score cannot exceed the maximum of {grade.max_marks} marks."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        grade.final_score = final_score
        grade.teacher_comment = serializer.validated_data.get("teacher_comment", "")
        grade.reviewed_by = request.user
        grade.reviewed_at = timezone.now()
        grade.status = OpenResponseGradeStatus.REVIEWED
        grade.save(
            update_fields=[
                "final_score",
                "teacher_comment",
                "reviewed_by",
                "reviewed_at",
                "status",
                "updated_at",
            ]
        )
        return Response(self.get_serializer(grade).data)


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Intervention Suggestions
# ─────────────────────────────────────────────────────────────────────────────


class InterventionSuggestionViewSet(ReadOnlyModelViewSet):
    """
    AI intervention strategies for struggling students — teacher-only.

    list:        GET  /api/v1/ai/interventions/                    — for teacher's rooms
                 GET  /api/v1/ai/interventions/?subject_room=<id>  — filter by room
                 GET  /api/v1/ai/interventions/?status=open        — filter by status
    retrieve:    GET  /api/v1/ai/interventions/{id}/
    generate:    POST /api/v1/ai/interventions/generate/           — queue generation
                     body: {subject_room_id}
    set_status:  POST /api/v1/ai/interventions/{id}/set-status/    — acknowledge/dismiss/resolve
                     body: {status: "acknowledged"|"dismissed"|"resolved"}

    A teacher only ever sees and acts on suggestions for rooms they teach.
    """

    serializer_class = InterventionSuggestionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != UserRole.TEACHER:
            return InterventionSuggestion.objects.none()

        qs = InterventionSuggestion.objects.select_related(
            "student",
            "subject_room__subject",
            "subject_room__classroom__standard",
            "subject_room__classroom__school",
        ).filter(subject_room__teacher=user)

        if subject_room_id := self.request.query_params.get("subject_room"):
            qs = qs.filter(subject_room_id=subject_room_id)
        if status_filter := self.request.query_params.get("status"):
            qs = qs.filter(status=status_filter)

        return qs

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Queue async generation of intervention suggestions for a room the teacher owns."""
        if request.user.role != UserRole.TEACHER:
            return Response(
                {"detail": "Only teachers can generate intervention suggestions."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TriggerInterventionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_room = get_object_or_404(SubjectRoom, pk=serializer.validated_data["subject_room_id"])
        if subject_room.teacher_id != request.user.pk:
            return Response(
                {"detail": "You do not teach this subject room."},
                status=status.HTTP_403_FORBIDDEN,
            )

        generate_interventions_for_subject_room.delay(subject_room.pk)
        return Response(
            {"detail": "Intervention generation queued."},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["post"], url_path="set-status")
    def set_status(self, request, pk=None):
        """Teacher acknowledges, dismisses, or resolves a suggestion."""
        suggestion = self.get_object()  # already scoped to the teacher's rooms

        serializer = UpdateInterventionStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        suggestion.status = new_status
        if new_status == InterventionStatus.ACKNOWLEDGED:
            suggestion.acknowledged_by = request.user
            suggestion.acknowledged_at = timezone.now()
            suggestion.save(update_fields=["status", "acknowledged_by", "acknowledged_at", "generated_at"])
        else:
            suggestion.save(update_fields=["status", "generated_at"])

        return Response(self.get_serializer(suggestion).data)


class TutorConversationViewSet(ModelViewSet):
    """
    Student-facing AI Tutor — multi-turn Socratic chat.

    list:     GET    /api/v1/ai/tutor/                — the student's own conversations
                     GET /api/v1/ai/tutor/?subpart=<id>
    retrieve: GET    /api/v1/ai/tutor/{id}/           — one conversation with all messages
    create:   POST   /api/v1/ai/tutor/                — start a conversation
                     body: {subpart_id?, message?, grade_level?, language?}
    message:  POST   /api/v1/ai/tutor/{id}/message/   — post a follow-up message
                     body: {message}

    Each create/message call appends the student's turn, generates a tutor reply
    synchronously via the LLM cascade, stores both, and returns the full
    conversation. The tutor is prompted to guide Socratically and never reveal the
    answer — the anchored subpart's correct answer is passed to the model only as
    a guard-rail and is never serialised back to the student.

    Only students (and open_students) may access this; each student sees only
    their own conversations.
    """

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def _student_only(self, user):
        return user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT)

    def get_queryset(self):
        user = self.request.user
        if not self._student_only(user):
            return TutorConversation.objects.none()
        qs = TutorConversation.objects.filter(student=user).prefetch_related("messages")
        if subpart_id := self.request.query_params.get("subpart"):
            qs = qs.filter(question_subpart_id=subpart_id)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return TutorConversationListSerializer
        return TutorConversationSerializer

    @staticmethod
    def _subpart_context(subpart):
        """Build the optional anchor context passed to the LLM."""
        if subpart is None:
            return {"question_text": "", "options": None, "correct_answer": None}
        return {
            "question_text": subpart.question_text or "",
            "options": subpart.options,
            "correct_answer": subpart.correct_answer or {},
        }

    def _generate_reply(self, conversation, student_message):
        """Append the student turn, generate + store the tutor reply.

        Returns the created tutor TutorMessage. Raises on LLM failure so the
        caller can surface a 503 (the student turn is committed regardless so the
        conversation isn't lost).
        """
        history = [{"role": m.role, "content": m.content} for m in conversation.messages.all()]
        TutorMessage.objects.create(
            conversation=conversation,
            role=TutorMessageRole.STUDENT,
            content=student_message,
        )

        ctx = self._subpart_context(conversation.question_subpart)
        result = generate_tutor_reply(
            student_message=student_message,
            history=history,
            grade_level=conversation.grade_level,
            language=conversation.language,
            **ctx,
        )
        tutor_msg = TutorMessage.objects.create(
            conversation=conversation,
            role=TutorMessageRole.TUTOR,
            content=result["text"],
            model_used=result["model"],
            input_tokens=result["input_tokens"],
            output_tokens=result["output_tokens"],
        )
        # Touch updated_at so the history list re-sorts to the top.
        conversation.save(update_fields=["updated_at"])
        return tutor_msg

    def create(self, request, *args, **kwargs):
        user = request.user
        if not self._student_only(user):
            return Response(
                {"detail": "Only students can use the tutor."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StartTutorConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        d = serializer.validated_data

        subpart = None
        if subpart_id := d.get("subpart_id"):
            try:
                subpart = QuestionSubpart.objects.select_related("question").get(pk=subpart_id)
            except QuestionSubpart.DoesNotExist:
                return Response({"detail": "Subpart not found."}, status=status.HTTP_404_NOT_FOUND)

        grade_level = d.get("grade_level") or user.grade or 8
        first_message = (d.get("message") or "").strip()

        conversation = TutorConversation.objects.create(
            student=user,
            question_subpart=subpart,
            grade_level=grade_level,
            language=d.get("language", "en"),
            title=first_message[:120],
        )

        if first_message:
            try:
                self._generate_reply(conversation, first_message)
            except Exception:
                import logging

                logging.getLogger(__name__).exception("generate_tutor_reply: unexpected error")
                # Keep the conversation + the student's message; signal degraded reply.
                return Response(
                    {
                        "detail": "The tutor is unavailable right now. Your message was saved — please try again.",
                        "conversation": TutorConversationSerializer(conversation).data,
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        conversation.refresh_from_db()
        return Response(
            TutorConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="message")
    def message(self, request, pk=None):
        """Post a follow-up message to an existing conversation."""
        conversation = self.get_object()  # already scoped to this student

        serializer = PostTutorMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student_message = serializer.validated_data["message"].strip()
        if not student_message:
            return Response(
                {"detail": "Message cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Backfill a title if the conversation was started empty.
        if not conversation.title:
            conversation.title = student_message[:120]
            conversation.save(update_fields=["title"])

        try:
            self._generate_reply(conversation, student_message)
        except Exception:
            import logging

            logging.getLogger(__name__).exception("generate_tutor_reply: unexpected error")
            return Response(
                {"detail": "The tutor is unavailable right now. Your message was saved — please try again."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        conversation.refresh_from_db()
        return Response(TutorConversationSerializer(conversation).data)
