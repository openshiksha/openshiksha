from rest_framework.routers import DefaultRouter

from .views import (
    AnalysisTriggerViewSet,
    ClassInsightViewSet,
    ContentRecommendationViewSet,
    LearningGapViewSet,
    PerformancePredictionViewSet,
    PracticePlanViewSet,
)

router = DefaultRouter()
router.register("learning-gaps", LearningGapViewSet, basename="learning-gap")
router.register("class-insights", ClassInsightViewSet, basename="class-insight")
router.register("predictions", PerformancePredictionViewSet, basename="performance-prediction")
router.register("recommendations", ContentRecommendationViewSet, basename="content-recommendation")
router.register("practice-plans", PracticePlanViewSet, basename="practice-plan")
router.register("trigger", AnalysisTriggerViewSet, basename="analysis-trigger")

urlpatterns = router.urls
