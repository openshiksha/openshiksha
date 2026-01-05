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

# Create router for ViewSets
router = DefaultRouter()

# ViewSets will be registered here as they're created
# Example: router.register(r'assignments', AssignmentViewSet, basename='assignment')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # Health check endpoint
    path('health/', include('apps.api.views.health')),

    # Router URLs (will include all ViewSets)
    path('', include(router.urls)),
]
