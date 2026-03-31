from rest_framework import serializers

from .models import (
    ClassInsight,
    ContentRecommendation,
    KnowledgeNode,
    LearningGap,
    LearningPath,
    LearningPathStep,
    PerformancePrediction,
    PracticePlan,
    SpacedRepetitionEntry,
    StudentMastery,
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
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    prerequisite_ids = serializers.PrimaryKeyRelatedField(
        source='prerequisites', many=True, read_only=True
    )

    class Meta:
        model = KnowledgeNode
        fields = [
            'id',
            'subject',
            'subject_name',
            'chapter',
            'chapter_name',
            'difficulty_weight',
            'prerequisite_ids',
            'is_active',
        ]
        read_only_fields = fields


class StudentMasterySerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source='knowledge_node.chapter.name', read_only=True)
    subject_name = serializers.CharField(source='knowledge_node.subject.name', read_only=True)
    mastery_level_display = serializers.CharField(source='get_mastery_level_display', read_only=True)

    class Meta:
        model = StudentMastery
        fields = [
            'id',
            'knowledge_node',
            'chapter_name',
            'subject_name',
            'mastery_score',
            'mastery_level',
            'mastery_level_display',
            'attempt_count',
            'last_attempted_at',
            'first_attempted_at',
            'updated_at',
        ]
        read_only_fields = fields


class SpacedRepetitionEntrySerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source='knowledge_node.chapter.name', read_only=True)

    class Meta:
        model = SpacedRepetitionEntry
        fields = [
            'id',
            'knowledge_node',
            'chapter_name',
            'interval_days',
            'easiness_factor',
            'repetitions',
            'next_review_date',
            'last_reviewed_at',
        ]
        read_only_fields = fields


class LearningPathStepSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(
        source='knowledge_node.chapter.name', read_only=True
    )
    subject_name = serializers.CharField(
        source='knowledge_node.subject.name', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LearningPathStep
        fields = [
            'id',
            'position',
            'knowledge_node',
            'chapter_name',
            'subject_name',
            'problem_set',
            'status',
            'status_display',
            'is_review',
            'score_when_completed',
            'completed_at',
        ]
        read_only_fields = fields


class LearningPathSerializer(serializers.ModelSerializer):
    steps = LearningPathStepSerializer(many=True, read_only=True)
    progress_pct = serializers.FloatField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = LearningPath
        fields = [
            'id',
            'subject_room',
            'status',
            'status_display',
            'total_steps',
            'completed_steps',
            'progress_pct',
            'steps',
            'generated_at',
            'updated_at',
        ]
        read_only_fields = fields


class TriggerAdaptiveSerializer(serializers.Serializer):
    subject_room_id = serializers.IntegerField()


class CompleteStepSerializer(serializers.Serializer):
    score = serializers.FloatField(min_value=0.0, max_value=1.0)
