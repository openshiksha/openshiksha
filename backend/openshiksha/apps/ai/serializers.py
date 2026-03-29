from rest_framework import serializers

from .models import ClassInsight, LearningGap, PerformancePrediction


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
