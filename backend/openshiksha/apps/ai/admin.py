from django.contrib import admin

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
    TutorConversation,
    TutorMessage,
    WeeklyClassReport,
)


@admin.register(LearningGap)
class LearningGapAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "chapter",
        "subject_room",
        "severity",
        "avg_score",
        "tick_count",
        "is_resolved",
        "refreshed_at",
    ]
    list_filter = ["severity", "is_resolved", "subject_room__subject"]
    search_fields = ["student__username", "student__email", "chapter__name"]
    readonly_fields = ["detected_at", "refreshed_at"]
    list_select_related = ["student", "chapter__subject", "subject_room__subject"]


@admin.register(ClassInsight)
class ClassInsightAdmin(admin.ModelAdmin):
    list_display = [
        "subject_room",
        "chapter",
        "insight_type",
        "class_avg_score",
        "students_assessed",
        "students_struggling",
        "pct_struggling",
        "generated_at",
    ]
    list_filter = ["insight_type", "subject_room__subject"]
    search_fields = ["chapter__name", "subject_room__subject__name"]
    readonly_fields = ["generated_at"]
    list_select_related = ["subject_room__subject", "chapter"]


@admin.register(PerformancePrediction)
class PerformancePredictionAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "subject_room",
        "readiness_level",
        "predicted_score",
        "confidence",
        "tick_count",
        "generated_at",
    ]
    list_filter = ["readiness_level", "subject_room__subject"]
    search_fields = ["student__username", "student__email"]
    readonly_fields = ["generated_at"]
    list_select_related = ["student", "subject_room__subject"]


@admin.register(ContentRecommendation)
class ContentRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "chapter",
        "subject_room",
        "reason",
        "priority",
        "score_snapshot",
        "is_active",
        "is_actioned",
        "generated_at",
    ]
    list_filter = ["reason", "priority", "is_active", "is_actioned", "subject_room__subject"]
    search_fields = ["student__username", "student__email", "chapter__name"]
    readonly_fields = ["generated_at", "actioned_at"]
    list_select_related = ["student", "chapter__subject", "subject_room__subject"]


@admin.register(PracticePlan)
class PracticePlanAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "subject_room",
        "plan_date",
        "estimated_minutes",
        "is_completed",
        "generated_at",
    ]
    list_filter = ["is_completed", "plan_date", "subject_room__subject"]
    search_fields = ["student__username", "student__email"]
    readonly_fields = ["generated_at"]
    filter_horizontal = ["recommendations"]
    list_select_related = ["student", "subject_room__subject"]


# ─────────────────────────────────────────────────────────────────────────────
# Adaptive Learning Engine Admin
# ─────────────────────────────────────────────────────────────────────────────


class LearningPathStepInline(admin.TabularInline):
    model = LearningPathStep
    extra = 0
    readonly_fields = [
        "position",
        "knowledge_node",
        "problem_set",
        "status",
        "is_review",
        "score_when_completed",
        "completed_at",
    ]
    can_delete = False


@admin.register(KnowledgeNode)
class KnowledgeNodeAdmin(admin.ModelAdmin):
    list_display = ["subject", "chapter", "difficulty_weight", "is_active", "updated_at"]
    list_filter = ["subject", "is_active"]
    search_fields = ["chapter__name", "subject__name"]
    filter_horizontal = ["prerequisites"]
    list_select_related = ["subject", "chapter"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(StudentMastery)
class StudentMasteryAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "knowledge_node",
        "mastery_level",
        "mastery_score",
        "attempt_count",
        "last_attempted_at",
        "updated_at",
    ]
    list_filter = ["mastery_level", "knowledge_node__subject"]
    search_fields = ["student__username", "student__email", "knowledge_node__chapter__name"]
    readonly_fields = ["first_attempted_at", "updated_at"]
    list_select_related = ["student", "knowledge_node__chapter", "knowledge_node__subject"]


@admin.register(SpacedRepetitionEntry)
class SpacedRepetitionEntryAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "knowledge_node",
        "next_review_date",
        "interval_days",
        "easiness_factor",
        "repetitions",
        "last_reviewed_at",
    ]
    list_filter = ["knowledge_node__subject", "next_review_date"]
    search_fields = ["student__username", "student__email", "knowledge_node__chapter__name"]
    readonly_fields = ["updated_at"]
    list_select_related = ["student", "knowledge_node__chapter"]


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "subject_room",
        "status",
        "total_steps",
        "completed_steps",
        "generated_at",
    ]
    list_filter = ["status", "subject_room__subject"]
    search_fields = ["student__username", "student__email"]
    readonly_fields = ["generated_at", "updated_at"]
    inlines = [LearningPathStepInline]
    list_select_related = ["student", "subject_room__subject"]


# ─────────────────────────────────────────────────────────────────────────────
# Natural Language Explanations Admin
# ─────────────────────────────────────────────────────────────────────────────


@admin.register(SubpartExplanation)
class SubpartExplanationAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "question_subpart",
        "submission",
        "is_correct",
        "language",
        "grade_level",
        "model_used",
        "input_tokens",
        "output_tokens",
        "generated_at",
    ]
    list_filter = ["is_correct", "language", "grade_level", "model_used"]
    search_fields = ["student__username", "student__email"]
    readonly_fields = ["generated_at", "input_tokens", "output_tokens", "model_used"]
    list_select_related = ["student", "question_subpart", "submission"]


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Weekly Class Reports Admin
# ─────────────────────────────────────────────────────────────────────────────


@admin.register(WeeklyClassReport)
class WeeklyClassReportAdmin(admin.ModelAdmin):
    list_display = [
        "subject_room",
        "week_start",
        "week_end",
        "active_students",
        "total_students",
        "class_avg_score",
        "ticks_recorded",
        "model_used",
        "generated_at",
    ]
    list_filter = ["week_start", "model_used", "subject_room__subject"]
    search_fields = ["subject_room__subject__name", "summary_text"]
    readonly_fields = ["generated_at", "input_tokens", "output_tokens", "model_used"]
    list_select_related = ["subject_room__subject", "subject_room__classroom"]


# ─────────────────────────────────────────────────────────────────────────────
# Intelligent Hint System Admin
# ─────────────────────────────────────────────────────────────────────────────


@admin.register(HintSequence)
class HintSequenceAdmin(admin.ModelAdmin):
    list_display = [
        "question_subpart",
        "hint_count",
        "grade_level",
        "model_used",
        "input_tokens",
        "output_tokens",
        "generated_at",
    ]
    list_filter = ["grade_level", "model_used"]
    search_fields = ["question_subpart__question_text"]
    readonly_fields = ["generated_at", "input_tokens", "output_tokens", "model_used"]
    list_select_related = ["question_subpart"]


@admin.register(StudentMisconception)
class StudentMisconceptionAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "question_subpart",
        "submission",
        "misconception_label",
        "grade_level",
        "model_used",
        "detected_at",
    ]
    list_filter = ["grade_level", "model_used"]
    search_fields = ["student__username", "student__email", "misconception_label", "diagnosis_text"]
    readonly_fields = ["detected_at", "input_tokens", "output_tokens", "model_used"]
    list_select_related = ["student", "question_subpart", "submission"]


# ─────────────────────────────────────────────────────────────────────────────
# Parent Intelligence Dashboard Admin
# ─────────────────────────────────────────────────────────────────────────────


@admin.register(ParentProgressSummary)
class ParentProgressSummaryAdmin(admin.ModelAdmin):
    list_display = [
        "parent",
        "child",
        "week_start",
        "week_end",
        "ticks_recorded",
        "active_days",
        "avg_score",
        "score_delta",
        "model_used",
        "generated_at",
    ]
    list_filter = ["week_start", "language", "model_used"]
    search_fields = [
        "parent__username",
        "parent__email",
        "child__username",
        "child__email",
        "summary_text",
    ]
    readonly_fields = ["generated_at", "input_tokens", "output_tokens", "model_used"]
    list_select_related = ["parent", "child"]


@admin.register(ClassMisconceptionCluster)
class ClassMisconceptionClusterAdmin(admin.ModelAdmin):
    list_display = [
        "subject_room",
        "misconception_label",
        "student_count",
        "occurrence_count",
        "last_seen",
        "refreshed_at",
    ]
    list_filter = ["subject_room__subject"]
    search_fields = ["misconception_label", "subject_room__subject__name"]
    readonly_fields = ["refreshed_at", "window_start", "last_seen"]
    list_select_related = ["subject_room__subject"]


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Assignment Draft Admin
# ─────────────────────────────────────────────────────────────────────────────


@admin.register(AssignmentDraft)
class AssignmentDraftAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "subject_room",
        "requested_by",
        "status",
        "question_count",
        "target_difficulty",
        "estimated_minutes",
        "created_at",
    ]
    list_filter = ["status", "subject_room__subject"]
    search_fields = ["title", "rationale_text", "subject_room__subject__name"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "model_used",
        "input_tokens",
        "output_tokens",
        "target_chapters",
        "selected_questions",
        "approved_problem_set",
        "approved_assignment",
    ]
    list_select_related = ["subject_room__subject", "requested_by"]


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Open-Ended Response Grading Admin
# ─────────────────────────────────────────────────────────────────────────────


@admin.register(OpenResponseRubric)
class OpenResponseRubricAdmin(admin.ModelAdmin):
    list_display = ["id", "subpart", "max_marks", "created_by", "updated_at"]
    search_fields = ["subpart__question_text", "model_answer"]
    readonly_fields = ["created_at", "updated_at"]
    list_select_related = ["subpart__question", "created_by"]


@admin.register(OpenResponseGrade)
class OpenResponseGradeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "student",
        "subpart",
        "subject_room",
        "status",
        "suggested_score",
        "final_score",
        "max_marks",
        "confidence",
        "model_used",
        "created_at",
    ]
    list_filter = ["status", "model_used", "subject_room__subject"]
    search_fields = ["student__username", "student__email", "response_text", "feedback"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "reviewed_at",
        "model_used",
        "input_tokens",
        "output_tokens",
        "suggested_score",
        "feedback",
        "criterion_scores",
        "confidence",
    ]
    list_select_related = ["student", "subpart__question", "subject_room__subject"]


# ─────────────────────────────────────────────────────────────────────────────
# Teacher AI Assistant — Intervention Suggestion Admin
# ─────────────────────────────────────────────────────────────────────────────


@admin.register(InterventionSuggestion)
class InterventionSuggestionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "student",
        "subject_room",
        "status",
        "priority",
        "severity",
        "avg_score",
        "gap_count",
        "model_used",
        "generated_at",
    ]
    list_filter = ["status", "severity", "subject_room__subject"]
    search_fields = ["student__username", "student__email", "strategy_text"]
    readonly_fields = [
        "generated_at",
        "acknowledged_at",
        "model_used",
        "input_tokens",
        "output_tokens",
        "focus_chapters",
        "misconception_labels",
        "avg_score",
        "gap_count",
        "priority",
        "severity",
    ]
    list_select_related = ["student", "subject_room__subject"]


@admin.register(QuestionDifficultyCalibration)
class QuestionDifficultyCalibrationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "subject_room",
        "question_subpart",
        "flag",
        "facility_index",
        "discrimination_index",
        "empirical_difficulty",
        "declared_difficulty",
        "sample_size",
        "computed_at",
    ]
    list_filter = ["flag", "subject_room__subject"]
    search_fields = ["question_subpart__question_text", "question_subpart__question__stem_text"]
    readonly_fields = [
        "subject_room",
        "question_subpart",
        "sample_size",
        "attempt_count",
        "facility_index",
        "discrimination_index",
        "empirical_difficulty",
        "declared_difficulty",
        "flag",
        "computed_at",
    ]
    list_select_related = ["subject_room__subject", "question_subpart"]


class TutorMessageInline(admin.TabularInline):
    model = TutorMessage
    extra = 0
    fields = ["role", "content", "model_used", "created_at"]
    readonly_fields = ["role", "content", "model_used", "created_at"]
    can_delete = False


@admin.register(TutorConversation)
class TutorConversationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "student",
        "title",
        "question_subpart",
        "grade_level",
        "language",
        "message_count",
        "updated_at",
    ]
    list_filter = ["language", "grade_level"]
    search_fields = ["title", "student__username"]
    readonly_fields = ["student", "question_subpart", "created_at", "updated_at"]
    list_select_related = ["student", "question_subpart"]
    inlines = [TutorMessageInline]


@admin.register(TutorMessage)
class TutorMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "conversation", "role", "model_used", "created_at"]
    list_filter = ["role"]
    search_fields = ["content"]
    readonly_fields = ["conversation", "role", "content", "model_used", "created_at"]
    list_select_related = ["conversation"]
