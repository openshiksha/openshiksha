"""
AI Analytics API views.

Permission rules:
- LearningGaps: student sees their own; teacher sees gaps for students in their rooms.
- ClassInsights: teacher sees insights for their subject_rooms.
- PerformancePredictions: student sees their own; teacher sees their students'.
- TriggerAnalysis: any authenticated user can trigger for a room they're associated with.
"""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from openshiksha.apps.core.models import SubjectRoom, UserRole

from .models import ClassInsight, LearningGap, PerformancePrediction
from .serializers import (
    ClassInsightSerializer,
    LearningGapSerializer,
    PerformancePredictionSerializer,
    TriggerAnalysisSerializer,
)
from .tasks import analyze_student_subject_room, generate_class_insights_for_subject_room


class LearningGapViewSet(ReadOnlyModelViewSet):
    """
    list:   GET /api/v1/ai/learning-gaps/          — student's own active gaps
    retrieve: GET /api/v1/ai/learning-gaps/{id}/   — single gap detail

    Query params:
      ?include_resolved=true  — include resolved gaps (default: only active)
    """
    serializer_class = LearningGapSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        include_resolved = self.request.query_params.get('include_resolved', '').lower() == 'true'

        qs = LearningGap.objects.select_related('chapter__subject').order_by('severity', 'avg_score')

        if user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            qs = qs.filter(student=user)
        elif user.role == UserRole.TEACHER:
            # Teachers see gaps for students in their subject rooms
            their_rooms = SubjectRoom.objects.filter(teacher=user)
            qs = qs.filter(subject_room__in=their_rooms)
        else:
            return LearningGap.objects.none()

        if not include_resolved:
            qs = qs.filter(is_resolved=False)

        return qs


class ClassInsightViewSet(ReadOnlyModelViewSet):
    """
    list:     GET /api/v1/ai/class-insights/           — all insights for teacher's rooms
    retrieve: GET /api/v1/ai/class-insights/{id}/      — single insight
    by_room:  GET /api/v1/ai/class-insights/by-room/{subject_room_id}/
    """
    serializer_class = ClassInsightSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = ClassInsight.objects.select_related('chapter').order_by('-pct_struggling')

        if user.role == UserRole.TEACHER:
            their_rooms = SubjectRoom.objects.filter(teacher=user)
            return qs.filter(subject_room__in=their_rooms)

        # Students can also see class context for rooms they're enrolled in
        if user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            enrolled_rooms = SubjectRoom.objects.filter(
                classroom__students=user
            )
            return qs.filter(subject_room__in=enrolled_rooms)

        return ClassInsight.objects.none()

    @action(detail=False, url_path=r'by-room/(?P<subject_room_id>\d+)')
    def by_room(self, request, subject_room_id=None):
        subject_room = get_object_or_404(SubjectRoom, pk=subject_room_id)
        qs = self.get_queryset().filter(subject_room=subject_room)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class PerformancePredictionViewSet(ReadOnlyModelViewSet):
    """
    list:     GET /api/v1/ai/predictions/       — student's own predictions
    retrieve: GET /api/v1/ai/predictions/{id}/  — single prediction
    """
    serializer_class = PerformancePredictionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = PerformancePrediction.objects.select_related(
            'subject_room__subject'
        ).order_by('readiness_level')

        if user.role in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return qs.filter(student=user)

        if user.role == UserRole.TEACHER:
            their_rooms = SubjectRoom.objects.filter(teacher=user)
            return qs.filter(subject_room__in=their_rooms)

        return PerformancePrediction.objects.none()


class AnalysisTriggerViewSet(ViewSet):
    """
    POST /api/v1/ai/trigger/student/   — trigger gap+prediction analysis for current student
    POST /api/v1/ai/trigger/class/     — trigger class insight analysis for a subject room
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='student')
    def trigger_student(self, request):
        serializer = TriggerAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_room_id = serializer.validated_data['subject_room_id']
        user = request.user

        if user.role not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return Response(
                {'detail': 'Only students can trigger personal analysis.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        subject_room = get_object_or_404(SubjectRoom, pk=subject_room_id)

        # Verify student is enrolled in this room (directly or via classroom)
        enrolled = (
            subject_room.students.filter(pk=user.pk).exists()
            or subject_room.classroom.students.filter(pk=user.pk).exists()
        )
        if not enrolled:
            return Response(
                {'detail': 'You are not enrolled in this subject room.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        analyze_student_subject_room.delay(user.pk, subject_room.pk)
        return Response({'detail': 'Analysis queued.'}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'], url_path='class')
    def trigger_class(self, request):
        serializer = TriggerAnalysisSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_room_id = serializer.validated_data['subject_room_id']
        user = request.user

        if user.role != UserRole.TEACHER:
            return Response(
                {'detail': 'Only teachers can trigger class analysis.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        subject_room = get_object_or_404(SubjectRoom, pk=subject_room_id)

        # Verify teacher owns this room
        is_teacher = (subject_room.teacher_id == user.pk)
        if not is_teacher:
            return Response(
                {'detail': 'You do not teach this subject room.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        generate_class_insights_for_subject_room.delay(subject_room.pk)
        return Response({'detail': 'Class analysis queued.'}, status=status.HTTP_202_ACCEPTED)
