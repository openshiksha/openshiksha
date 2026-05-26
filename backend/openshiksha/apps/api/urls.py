"""
API URL Configuration
"""

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from openshiksha.apps.api.views.auth import RegisterOpenView, RegisterSchoolView
from openshiksha.apps.api.views.core import (
    AssignmentViewSet,
    ChapterViewSet,
    ProblemSetViewSet,
    QuestionMistakeViewSet,
    QuestionTagViewSet,
    QuestionViewSet,
    StudentProficiencyViewSet,
    SubjectRoomViewSet,
    SubjectViewSet,
    SubmissionViewSet,
    UserViewSet,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"question-tags", QuestionTagViewSet, basename="questiontag")
router.register(r"questions", QuestionViewSet, basename="question")
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"chapters", ChapterViewSet, basename="chapter")
router.register(r"subject-rooms", SubjectRoomViewSet, basename="subjectroom")
router.register(r"problem-sets", ProblemSetViewSet, basename="problemset")
router.register(r"assignments", AssignmentViewSet, basename="assignment")
router.register(r"submissions", SubmissionViewSet, basename="submission")
router.register(r"proficiency", StudentProficiencyViewSet, basename="proficiency")
router.register(r"question-mistakes", QuestionMistakeViewSet, basename="question-mistake")

urlpatterns = [
    # Authentication endpoints
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("auth/register/open/", RegisterOpenView.as_view(), name="register_open"),
    path("auth/register/school/", RegisterSchoolView.as_view(), name="register_school"),
    # Health check endpoint
    path("health/", include("openshiksha.apps.api.views.health")),
    # Router URLs (all ViewSets)
    path("", include(router.urls)),
    # AI Analytics endpoints
    path("ai/", include("openshiksha.apps.ai.urls")),
]
