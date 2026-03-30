from django.contrib import admin

from .models import ClassInsight, ContentRecommendation, LearningGap, PerformancePrediction, PracticePlan


@admin.register(LearningGap)
class LearningGapAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'chapter', 'subject_room', 'severity',
        'avg_score', 'tick_count', 'is_resolved', 'refreshed_at',
    ]
    list_filter = ['severity', 'is_resolved', 'subject_room__subject']
    search_fields = ['student__username', 'student__email', 'chapter__name']
    readonly_fields = ['detected_at', 'refreshed_at']
    list_select_related = ['student', 'chapter__subject', 'subject_room__subject']


@admin.register(ClassInsight)
class ClassInsightAdmin(admin.ModelAdmin):
    list_display = [
        'subject_room', 'chapter', 'insight_type',
        'class_avg_score', 'students_assessed', 'students_struggling',
        'pct_struggling', 'generated_at',
    ]
    list_filter = ['insight_type', 'subject_room__subject']
    search_fields = ['chapter__name', 'subject_room__subject__name']
    readonly_fields = ['generated_at']
    list_select_related = ['subject_room__subject', 'chapter']


@admin.register(PerformancePrediction)
class PerformancePredictionAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'subject_room', 'readiness_level',
        'predicted_score', 'confidence', 'tick_count', 'generated_at',
    ]
    list_filter = ['readiness_level', 'subject_room__subject']
    search_fields = ['student__username', 'student__email']
    readonly_fields = ['generated_at']
    list_select_related = ['student', 'subject_room__subject']


@admin.register(ContentRecommendation)
class ContentRecommendationAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'chapter', 'subject_room', 'reason',
        'priority', 'score_snapshot', 'is_active', 'is_actioned', 'generated_at',
    ]
    list_filter = ['reason', 'priority', 'is_active', 'is_actioned', 'subject_room__subject']
    search_fields = ['student__username', 'student__email', 'chapter__name']
    readonly_fields = ['generated_at', 'actioned_at']
    list_select_related = ['student', 'chapter__subject', 'subject_room__subject']


@admin.register(PracticePlan)
class PracticePlanAdmin(admin.ModelAdmin):
    list_display = [
        'student', 'subject_room', 'plan_date',
        'estimated_minutes', 'is_completed', 'generated_at',
    ]
    list_filter = ['is_completed', 'plan_date', 'subject_room__subject']
    search_fields = ['student__username', 'student__email']
    readonly_fields = ['generated_at']
    filter_horizontal = ['recommendations']
    list_select_related = ['student', 'subject_room__subject']
