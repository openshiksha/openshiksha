from rest_framework.routers import DefaultRouter

from .views import (
    AnalysisTriggerViewSet,
    ClassInsightViewSet,
    ContentRecommendationViewSet,
    GenerateQuestionsViewSet,
    KnowledgeNodeViewSet,
    LearningGapViewSet,
    LearningPathViewSet,
    PerformancePredictionViewSet,
    PracticePlanViewSet,
    SpacedRepetitionViewSet,
    StudentMasteryViewSet,
    SubpartExplanationViewSet,
)

router = DefaultRouter()
# Smart Analytics & Insights
router.register("learning-gaps", LearningGapViewSet, basename="learning-gap")
router.register("class-insights", ClassInsightViewSet, basename="class-insight")
router.register("predictions", PerformancePredictionViewSet, basename="performance-prediction")
# Content Recommendations
router.register("recommendations", ContentRecommendationViewSet, basename="content-recommendation")
router.register("practice-plans", PracticePlanViewSet, basename="practice-plan")
# Triggers
router.register("trigger", AnalysisTriggerViewSet, basename="analysis-trigger")
# Adaptive Learning Engine
router.register("knowledge-nodes", KnowledgeNodeViewSet, basename="knowledge-node")
router.register("mastery", StudentMasteryViewSet, basename="student-mastery")
router.register("spaced-repetition", SpacedRepetitionViewSet, basename="spaced-repetition")
router.register("learning-paths", LearningPathViewSet, basename="learning-path")
# Natural Language Explanations
router.register("explanations", SubpartExplanationViewSet, basename="explanation")
# AI Question Generation (teacher-only)
router.register("generate-questions", GenerateQuestionsViewSet, basename="generate-questions")

urlpatterns = router.urls
