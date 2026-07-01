from rest_framework import serializers

from openshiksha.apps.core.models import QuestionType

from .models import (
    AssignmentDraft,
    ClassInsight,
    ClassMisconceptionCluster,
    ContentRecommendation,
    HintSequence,
    InterventionSuggestion,
    KnowledgeNode,
    LearningGap,
    LearningPath,
    LearningPathStep,
    OpenResponseGrade,
    OpenResponseRubric,
    ParentProgressSummary,
    PerformancePrediction,
    PracticePlan,
    QuestionDifficultyCalibration,
    SpacedRepetitionEntry,
    StudentMastery,
    StudentMisconception,
    SubpartExplanation,
    WeeklyClassReport,
)


class LearningGapSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source="chapter.name", read_only=True)
    subject_name = serializers.CharField(source="chapter.subject.name", read_only=True)

    class Meta:
        model = LearningGap
        fields = [
            "id",
            "chapter",
            "chapter_name",
            "subject_name",
            "subject_room",
            "avg_score",
            "severity",
            "tick_count",
            "is_resolved",
            "detected_at",
            "refreshed_at",
        ]
        read_only_fields = fields


class ClassInsightSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source="chapter.name", read_only=True)

    class Meta:
        model = ClassInsight
        fields = [
            "id",
            "chapter",
            "chapter_name",
            "insight_type",
            "class_avg_score",
            "students_assessed",
            "students_struggling",
            "pct_struggling",
            "generated_at",
        ]
        read_only_fields = fields


class PerformancePredictionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject_room.subject.name", read_only=True)

    class Meta:
        model = PerformancePrediction
        fields = [
            "id",
            "subject_room",
            "subject_name",
            "predicted_score",
            "confidence",
            "readiness_level",
            "tick_count",
            "factors",
            "generated_at",
        ]
        read_only_fields = fields


class TriggerAnalysisSerializer(serializers.Serializer):
    subject_room_id = serializers.IntegerField()


class ContentRecommendationSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source="chapter.name", read_only=True)
    subject_name = serializers.CharField(source="chapter.subject.name", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)

    class Meta:
        model = ContentRecommendation
        fields = [
            "id",
            "chapter",
            "chapter_name",
            "subject_name",
            "subject_room",
            "problem_set",
            "reason",
            "reason_display",
            "priority",
            "priority_display",
            "score_snapshot",
            "is_actioned",
            "is_active",
            "generated_at",
            "actioned_at",
        ]
        read_only_fields = fields


class PracticePlanSerializer(serializers.ModelSerializer):
    recommendations = ContentRecommendationSerializer(many=True, read_only=True)

    class Meta:
        model = PracticePlan
        fields = [
            "id",
            "subject_room",
            "plan_date",
            "estimated_minutes",
            "is_completed",
            "recommendations",
            "generated_at",
        ]
        read_only_fields = fields


class TriggerRecommendationsSerializer(serializers.Serializer):
    subject_room_id = serializers.IntegerField()


# ─────────────────────────────────────────────────────────────────────────────
# Adaptive Learning Engine Serializers
# ─────────────────────────────────────────────────────────────────────────────


class KnowledgeNodeSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source="chapter.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    prerequisite_ids = serializers.PrimaryKeyRelatedField(source="prerequisites", many=True, read_only=True)

    class Meta:
        model = KnowledgeNode
        fields = [
            "id",
            "subject",
            "subject_name",
            "chapter",
            "chapter_name",
            "difficulty_weight",
            "prerequisite_ids",
            "is_active",
        ]
        read_only_fields = fields


class StudentMasterySerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source="knowledge_node.chapter.name", read_only=True)
    subject_name = serializers.CharField(source="knowledge_node.subject.name", read_only=True)
    mastery_level_display = serializers.CharField(source="get_mastery_level_display", read_only=True)

    class Meta:
        model = StudentMastery
        fields = [
            "id",
            "knowledge_node",
            "chapter_name",
            "subject_name",
            "mastery_score",
            "mastery_level",
            "mastery_level_display",
            "attempt_count",
            "last_attempted_at",
            "first_attempted_at",
            "updated_at",
        ]
        read_only_fields = fields


class SpacedRepetitionEntrySerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source="knowledge_node.chapter.name", read_only=True)

    class Meta:
        model = SpacedRepetitionEntry
        fields = [
            "id",
            "knowledge_node",
            "chapter_name",
            "interval_days",
            "easiness_factor",
            "repetitions",
            "next_review_date",
            "last_reviewed_at",
        ]
        read_only_fields = fields


class LearningPathStepSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source="knowledge_node.chapter.name", read_only=True)
    subject_name = serializers.CharField(source="knowledge_node.subject.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = LearningPathStep
        fields = [
            "id",
            "position",
            "knowledge_node",
            "chapter_name",
            "subject_name",
            "problem_set",
            "status",
            "status_display",
            "is_review",
            "score_when_completed",
            "completed_at",
        ]
        read_only_fields = fields


class LearningPathSerializer(serializers.ModelSerializer):
    steps = LearningPathStepSerializer(many=True, read_only=True)
    progress_pct = serializers.FloatField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = LearningPath
        fields = [
            "id",
            "subject_room",
            "status",
            "status_display",
            "total_steps",
            "completed_steps",
            "progress_pct",
            "steps",
            "generated_at",
            "updated_at",
        ]
        read_only_fields = fields


class TriggerAdaptiveSerializer(serializers.Serializer):
    subject_room_id = serializers.IntegerField()


class CompleteStepSerializer(serializers.Serializer):
    score = serializers.FloatField(min_value=0.0, max_value=1.0)


class SubpartExplanationSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question_subpart.question_text", read_only=True)
    subpart_index = serializers.IntegerField(source="question_subpart.index", read_only=True)

    class Meta:
        model = SubpartExplanation
        fields = [
            "id",
            "question_subpart",
            "question_text",
            "subpart_index",
            "submission",
            "student_answer",
            "is_correct",
            "explanation_text",
            "language",
            "grade_level",
            "model_used",
            "generated_at",
        ]
        read_only_fields = fields


class GenerateExplanationSerializer(serializers.Serializer):
    """Request body for on-demand single-subpart explanation."""

    subpart_id = serializers.IntegerField()
    student_answer = serializers.JSONField()
    is_correct = serializers.BooleanField()
    grade_level = serializers.IntegerField(min_value=1, max_value=12, required=False, default=8)
    language = serializers.ChoiceField(choices=["en", "hi"], required=False, default="en")


class GenerateQuestionsRequestSerializer(serializers.Serializer):
    """Request body for AI question generation."""

    topic = serializers.CharField(max_length=300)
    chapter_id = serializers.IntegerField()
    question_type = serializers.ChoiceField(choices=[qt[0] for qt in QuestionType.choices])
    difficulty = serializers.IntegerField(min_value=1, max_value=5, default=2)
    count = serializers.IntegerField(min_value=1, max_value=5, default=3)


class WidgetAuthoringRequestSerializer(serializers.Serializer):
    """Request body for Describe-to-Build AI widget authoring (DTB-2)."""

    description = serializers.CharField(max_length=500, trim_whitespace=True)
    # Optional teacher hint; validated against the authorable set in the view so
    # the choice list stays single-sourced in apps.core.widgets.
    kind_hint = serializers.CharField(max_length=40, required=False, allow_blank=True)
    # DTB-5: opt in to per-student randomisation. When set, the AI may bind
    # numeric fields to croupier ``{{var}}`` tokens and the response carries the
    # validated ``variable_constraints`` to attach alongside the config.
    allow_variables = serializers.BooleanField(required=False, default=False)


class PracticeProblemRequestSerializer(serializers.Serializer):
    """Request body for the propose-and-verify practice-problem proposer (PV-2).

    A plain-English topic → the AI proposes a number-line ``widget_config`` +
    ``correct_answer``, which PV-1's ``verify_widget_problem`` gates (and, if the
    answer is off-grid, deterministically snaps onto the widget's grid) before it
    is ever returned. Correctness is never AI-decided — the engine disposes.
    """

    topic = serializers.CharField(max_length=500, trim_whitespace=True)


class StepHintRequestSerializer(serializers.Serializer):
    """Request body for the Guided step-validator AI wrong-step explainer (GSV-3).

    The two lines a student wrote one after another. Correctness is decided
    server-side by the deterministic ``apps.core.algebra`` engine — never by the
    client and never by AI; the AI hint is produced only when that engine has
    already ruled ``current`` a wrong step from ``previous``.
    """

    previous = serializers.CharField(max_length=300, trim_whitespace=True)
    current = serializers.CharField(max_length=300, trim_whitespace=True)


class WeeklyClassReportSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject_room.subject.name", read_only=True)
    classroom_label = serializers.CharField(source="subject_room.classroom.__str__", read_only=True)
    participation_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = WeeklyClassReport
        fields = [
            "id",
            "subject_room",
            "subject_name",
            "classroom_label",
            "week_start",
            "week_end",
            "summary_text",
            "total_students",
            "active_students",
            "participation_rate",
            "ticks_recorded",
            "class_avg_score",
            "struggling_chapters",
            "strong_chapters",
            "model_used",
            "generated_at",
        ]
        read_only_fields = fields


class TriggerWeeklyReportSerializer(serializers.Serializer):
    subject_room_id = serializers.IntegerField()
    week_start = serializers.DateField(required=False, allow_null=True)


class MCQOptionDraftSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=4)
    text = serializers.CharField()


class GeneratedQuestionDraftSerializer(serializers.Serializer):
    """One draft question returned by the AI generation endpoint."""

    question_text = serializers.CharField()
    options = MCQOptionDraftSerializer(many=True, allow_null=True, required=False)
    correct_answer = serializers.CharField()
    variable_constraints = serializers.DictField(
        child=serializers.DictField(), allow_null=True, required=False, default=None
    )
    suggested_tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False, default=list)
    solution = serializers.CharField(required=False, allow_blank=True, default="")


# ─────────────────────────────────────────────────────────────────────────────
# Intelligent Hint System Serializers
# ─────────────────────────────────────────────────────────────────────────────


class HintSequenceSerializer(serializers.ModelSerializer):
    """Student-safe hint payload — never exposes the correct answer."""

    hint_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = HintSequence
        fields = [
            "id",
            "question_subpart",
            "hints",
            "hint_count",
            "grade_level",
            "generated_at",
        ]
        read_only_fields = fields


class GenerateHintsSerializer(serializers.Serializer):
    """Request body for on-demand hint generation."""

    subpart_id = serializers.IntegerField()
    num_hints = serializers.IntegerField(min_value=1, max_value=5, required=False, default=3)
    grade_level = serializers.IntegerField(min_value=1, max_value=12, required=False, allow_null=True)


class StudentMisconceptionSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question_subpart.question_text", read_only=True)
    subpart_index = serializers.IntegerField(source="question_subpart.index", read_only=True)
    student_username = serializers.CharField(source="student.username", read_only=True)

    class Meta:
        model = StudentMisconception
        fields = [
            "id",
            "student",
            "student_username",
            "question_subpart",
            "question_text",
            "subpart_index",
            "submission",
            "student_answer",
            "misconception_label",
            "diagnosis_text",
            "remediation_tip",
            "grade_level",
            "detected_at",
        ]
        read_only_fields = fields


class DiagnoseMisconceptionSerializer(serializers.Serializer):
    """Request body for on-demand misconception diagnosis (incorrect answers only)."""

    subpart_id = serializers.IntegerField()
    student_answer = serializers.JSONField()
    submission_id = serializers.IntegerField(required=False, allow_null=True)
    grade_level = serializers.IntegerField(min_value=1, max_value=12, required=False, allow_null=True)


# ─────────────────────────────────────────────────────────────────────────────
# Parent Intelligence Dashboard Serializers
# ─────────────────────────────────────────────────────────────────────────────


class ParentProgressSummarySerializer(serializers.ModelSerializer):
    """Parent-facing weekly progress narrative + alerts + suggested activities."""

    child_username = serializers.CharField(source="child.username", read_only=True)
    child_name = serializers.SerializerMethodField()
    has_urgent_alert = serializers.BooleanField(read_only=True)

    class Meta:
        model = ParentProgressSummary
        fields = [
            "id",
            "parent",
            "child",
            "child_username",
            "child_name",
            "week_start",
            "week_end",
            "summary_text",
            "language",
            "ticks_recorded",
            "active_days",
            "avg_score",
            "score_delta",
            "weak_chapters",
            "strong_chapters",
            "home_activities",
            "alerts",
            "has_urgent_alert",
            "model_used",
            "generated_at",
        ]
        read_only_fields = fields

    def get_child_name(self, obj):
        return obj.child.full_name if hasattr(obj.child, "full_name") else obj.child.username


class GenerateParentSummarySerializer(serializers.Serializer):
    """Request body for queuing a parent progress summary generation."""

    child_id = serializers.IntegerField()
    week_start = serializers.DateField(required=False, allow_null=True)
    language = serializers.ChoiceField(choices=["en", "hi"], required=False, default="en")


class ClassMisconceptionClusterSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject_room.subject.name", read_only=True)

    class Meta:
        model = ClassMisconceptionCluster
        fields = [
            "id",
            "subject_room",
            "subject_name",
            "misconception_label",
            "student_count",
            "occurrence_count",
            "sample_diagnosis",
            "sample_remediation_tip",
            "window_start",
            "last_seen",
            "refreshed_at",
        ]
        read_only_fields = fields


class TriggerMisconceptionClusterSerializer(serializers.Serializer):
    """Request body for queuing a class misconception cluster refresh."""

    subject_room_id = serializers.IntegerField()
    lookback_days = serializers.IntegerField(required=False, min_value=1, max_value=365)


class QuestionDifficultyCalibrationSerializer(serializers.ModelSerializer):
    """Read serializer for an item-analysis calibration row (teacher-facing)."""

    flag_display = serializers.CharField(source="get_flag_display", read_only=True)
    difficulty_delta = serializers.IntegerField(read_only=True)
    needs_review = serializers.BooleanField(read_only=True)
    subject_name = serializers.CharField(source="subject_room.subject.name", read_only=True)
    question_id = serializers.IntegerField(source="question_subpart.question_id", read_only=True)
    subpart_index = serializers.IntegerField(source="question_subpart.index", read_only=True)
    chapter_name = serializers.CharField(source="question_subpart.question.chapter.name", read_only=True)
    question_preview = serializers.SerializerMethodField()

    class Meta:
        model = QuestionDifficultyCalibration
        fields = [
            "id",
            "subject_room",
            "subject_name",
            "question_subpart",
            "question_id",
            "subpart_index",
            "chapter_name",
            "question_preview",
            "sample_size",
            "attempt_count",
            "facility_index",
            "discrimination_index",
            "empirical_difficulty",
            "declared_difficulty",
            "difficulty_delta",
            "flag",
            "flag_display",
            "needs_review",
            "computed_at",
        ]
        read_only_fields = fields

    def get_question_preview(self, obj) -> str:
        """First ~120 chars of the subpart text, for at-a-glance identification."""
        text = (obj.question_subpart.question_text or "").strip()
        return text[:120] + ("…" if len(text) > 120 else "")


class TriggerDifficultyCalibrationSerializer(serializers.Serializer):
    """Request body for queuing a difficulty-calibration refresh for a room."""

    subject_room_id = serializers.IntegerField()


class AssignmentDraftSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject_room.subject.name", read_only=True)
    classroom_label = serializers.CharField(source="subject_room.classroom.__str__", read_only=True)
    question_count = serializers.IntegerField(read_only=True)
    is_actionable = serializers.BooleanField(read_only=True)

    class Meta:
        model = AssignmentDraft
        fields = [
            "id",
            "subject_room",
            "subject_name",
            "classroom_label",
            "status",
            "title",
            "rationale_text",
            "target_difficulty",
            "requested_size",
            "target_chapters",
            "selected_questions",
            "question_count",
            "estimated_minutes",
            "is_actionable",
            "approved_problem_set",
            "approved_assignment",
            "model_used",
            "error_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class GenerateAssignmentDraftSerializer(serializers.Serializer):
    """Request body for queuing an AI assignment draft."""

    subject_room_id = serializers.IntegerField()
    size = serializers.IntegerField(required=False, min_value=1, max_value=20)
    target_difficulty = serializers.IntegerField(required=False, min_value=1, max_value=5)


class ApproveAssignmentDraftSerializer(serializers.Serializer):
    """Request body for approving a draft into a real Assignment."""

    due_at = serializers.DateTimeField()
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Open-Ended Response Grading
# ─────────────────────────────────────────────────────────────────────────────


class OpenResponseRubricSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="subpart.question_text", read_only=True)

    class Meta:
        model = OpenResponseRubric
        fields = [
            "id",
            "subpart",
            "question_text",
            "max_marks",
            "model_answer",
            "criteria",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class OpenResponseGradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.get_full_name", read_only=True)
    student_username = serializers.CharField(source="student.username", read_only=True)
    question_text = serializers.CharField(source="subpart.question_text", read_only=True)
    subject_name = serializers.CharField(source="subject_room.subject.name", read_only=True)
    effective_score = serializers.FloatField(read_only=True)
    is_reviewed = serializers.BooleanField(read_only=True)

    class Meta:
        model = OpenResponseGrade
        fields = [
            "id",
            "subpart",
            "question_text",
            "student",
            "student_name",
            "student_username",
            "subject_room",
            "subject_name",
            "assignment",
            "response_text",
            "status",
            "max_marks",
            "suggested_score",
            "feedback",
            "criterion_scores",
            "confidence",
            "final_score",
            "teacher_comment",
            "reviewed_by",
            "reviewed_at",
            "effective_score",
            "is_reviewed",
            "model_used",
            "error_detail",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class SubmitOpenResponseSerializer(serializers.Serializer):
    """Request body for recording a student's free-text answer for AI grading."""

    subpart_id = serializers.IntegerField()
    student_id = serializers.IntegerField()
    subject_room_id = serializers.IntegerField()
    assignment_id = serializers.IntegerField(required=False, allow_null=True)
    response_text = serializers.CharField()


class ReviewOpenResponseSerializer(serializers.Serializer):
    """Request body for a teacher finalising an AI-suggested grade."""

    final_score = serializers.FloatField(min_value=0)
    teacher_comment = serializers.CharField(required=False, allow_blank=True)


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Intervention Suggestions
# ─────────────────────────────────────────────────────────────────────────────


class InterventionSuggestionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    student_username = serializers.CharField(source="student.username", read_only=True)
    subject_name = serializers.CharField(source="subject_room.subject.name", read_only=True)
    classroom_label = serializers.CharField(source="subject_room.classroom.__str__", read_only=True)

    class Meta:
        model = InterventionSuggestion
        fields = [
            "id",
            "subject_room",
            "subject_name",
            "classroom_label",
            "student",
            "student_name",
            "student_username",
            "status",
            "priority",
            "severity",
            "strategy_text",
            "avg_score",
            "gap_count",
            "focus_chapters",
            "misconception_labels",
            "acknowledged_by",
            "acknowledged_at",
            "model_used",
            "generated_at",
        ]
        read_only_fields = fields


class TriggerInterventionsSerializer(serializers.Serializer):
    """Request body for queuing intervention generation for a SubjectRoom."""

    subject_room_id = serializers.IntegerField()


class UpdateInterventionStatusSerializer(serializers.Serializer):
    """Request body for a teacher changing an intervention's status."""

    status = serializers.ChoiceField(
        choices=["acknowledged", "dismissed", "resolved"],
    )
