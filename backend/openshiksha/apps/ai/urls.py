from rest_framework.routers import DefaultRouter

from .views import (
    AnalysisTriggerViewSet,
    AssignmentDraftViewSet,
    ClassInsightViewSet,
    ClassMisconceptionClusterViewSet,
    ContentRecommendationViewSet,
    GenerateQuestionsViewSet,
    HintSequenceViewSet,
    InterventionSuggestionViewSet,
    KnowledgeNodeViewSet,
    LearningGapViewSet,
    LearningPathViewSet,
    OpenResponseGradeViewSet,
    OpenResponseRubricViewSet,
    ParentProgressSummaryViewSet,
    PerformancePredictionViewSet,
    PracticePlanViewSet,
    QuestionDifficultyCalibrationViewSet,
    SpacedRepetitionViewSet,
    StudentMasteryViewSet,
    StudentMisconceptionViewSet,
    SubpartExplanationViewSet,
    WeeklyClassReportViewSet,
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
# Teacher AI Assistant — Weekly Class Reports (teacher-only)
router.register("weekly-reports", WeeklyClassReportViewSet, basename="weekly-report")
# Intelligent Hint System
router.register("hints", HintSequenceViewSet, basename="hint-sequence")
router.register("misconceptions", StudentMisconceptionViewSet, basename="misconception")
router.register("misconception-clusters", ClassMisconceptionClusterViewSet, basename="misconception-cluster")
# Parent Intelligence Dashboard (parent-only)
router.register("parent-summaries", ParentProgressSummaryViewSet, basename="parent-summary")
# Teacher AI Assistant — Auto-Drafted Assignments (teacher-only)
router.register("assignment-drafts", AssignmentDraftViewSet, basename="assignment-draft")
# Teacher AI Assistant — Open-Ended Response Grading (teacher-only)
router.register("open-rubrics", OpenResponseRubricViewSet, basename="open-response-rubric")
router.register("open-grades", OpenResponseGradeViewSet, basename="open-response-grade")
# Teacher AI Assistant — Intervention Suggestions (teacher-only)
router.register("interventions", InterventionSuggestionViewSet, basename="intervention-suggestion")
# Empirical Question Difficulty Calibration (teacher-only)
router.register(
    "difficulty-calibrations",
    QuestionDifficultyCalibrationViewSet,
    basename="difficulty-calibration",
)

urlpatterns = router.urls
