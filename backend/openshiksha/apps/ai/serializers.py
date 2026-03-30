from rest_framework import serializers

from .models import ClassInsight, ContentRecommendation, LearningGap, PerformancePrediction, PracticePlan


class LearningGapSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)
    subject_name = serializers.CharField(source='chapter.subject.name', read_only=True)

    class Meta:
        model = LearningGap
        fields = [
            'id',
            'chapter',
            'chapter_name',
            'subject_name',
            'subject_room',
            'avg_score',
            'severity',
            'tick_count',
            'is_resolved',
            'detected_at',
            'refreshed_at',
        ]
        read_only_fields = fields


class ClassInsightSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)

    class Meta:
        model = ClassInsight
        fields = [
            'id',
            'chapter',
            'chapter_name',
            'insight_type',
            'class_avg_score',
            'students_assessed',
            'students_struggling',
            'pct_struggling',
            'generated_at',
        ]
        read_only_fields = fields


class PerformancePredictionSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject_room.subject.name', read_only=True)

    class Meta:
        model = PerformancePrediction
        fields = [
            'id',
            'subject_room',
            'subject_name',
            'predicted_score',
            'confidence',
            'readiness_level',
            'tick_count',
            'factors',
            'generated_at',
        ]
        read_only_fields = fields


class TriggerAnalysisSerializer(serializers.Serializer):
    subject_room_id = serializers.IntegerField()


class ContentRecommendationSerializer(serializers.ModelSerializer):
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)
    subject_name = serializers.CharField(source='chapter.subject.name', read_only=True)
    reason_display = serializers.CharField(source='get_reason_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = ContentRecommendation
        fields = [
            'id',
            'chapter',
            'chapter_name',
            'subject_name',
            'subject_room',
            'problem_set',
            'reason',
            'reason_display',
            'priority',
            'priority_display',
            'score_snapshot',
            'is_actioned',
            'is_active',
            'generated_at',
            'actioned_at',
        ]
        read_only_fields = fields


class PracticePlanSerializer(serializers.ModelSerializer):
    recommendations = ContentRecommendationSerializer(many=True, read_only=True)

    class Meta:
        model = PracticePlan
        fields = [
            'id',
            'subject_room',
            'plan_date',
            'estimated_minutes',
            'is_completed',
            'recommendations',
            'generated_at',
        ]
        read_only_fields = fields


class TriggerRecommendationsSerializer(serializers.Serializer):
    subject_room_id = serializers.IntegerField()
