"""
API URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from openshiksha.apps.api.views.core import (
    QuestionTagViewSet,
    QuestionViewSet,
    SubjectRoomViewSet,
    ProblemSetViewSet,
    AssignmentViewSet,
    SubmissionViewSet,
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'question-tags', QuestionTagViewSet, basename='questiontag')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'subject-rooms', SubjectRoomViewSet, basename='subjectroom')
router.register(r'problem-sets', ProblemSetViewSet, basename='problemset')
router.register(r'assignments', AssignmentViewSet, basename='assignment')
router.register(r'submissions', SubmissionViewSet, basename='submission')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Health check endpoint
    path('health/', include('openshiksha.apps.api.views.health')),

    # Router URLs (all ViewSets)
    path('', include(router.urls)),
]
