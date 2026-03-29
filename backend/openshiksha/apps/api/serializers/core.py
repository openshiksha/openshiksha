"""
Core serializers for OpenShiksha API

Covers Question Bank, SubjectRoom, Assignment Pipeline, and Submission.
"""

from rest_framework import serializers

from openshiksha.apps.core.models import (
    User,
    QuestionTag,
    QuestionSubpart,
    Question,
    SubjectRoom,
    ProblemSet,
    Assignment,
    Submission,
    UserRole,
)


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for the current user profile."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]
        read_only_fields = ["id", "username", "email", "first_name", "last_name", "role"]


class QuestionTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionTag
        fields = ['id', 'name', 'tag_type']


class QuestionSubpartSerializer(serializers.ModelSerializer):
    tags = QuestionTagSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionSubpart
        fields = ['id', 'index', 'tags', 'correct_answer']


class QuestionSerializer(serializers.ModelSerializer):
    subparts = QuestionSubpartSerializer(many=True, read_only=True)
    tags = QuestionTagSerializer(many=True, read_only=True)
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'standard', 'subject', 'chapter',
            'question_type', 'question_type_display',
            'difficulty', 'tags', 'subparts', 'is_active',
            'created_at',
        ]


class SubjectRoomSerializer(serializers.ModelSerializer):
    classroom_display = serializers.StringRelatedField(source='classroom')
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.full_name', read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = SubjectRoom
        fields = [
            'id', 'classroom', 'classroom_display',
            'subject', 'subject_name',
            'teacher', 'teacher_name',
            'is_active', 'student_count', 'created_at',
        ]

    def get_student_count(self, obj) -> int:
        return obj.students.count()


class ProblemSetSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    chapter_name = serializers.CharField(source='chapter.name', read_only=True)

    class Meta:
        model = ProblemSet
        fields = [
            'id', 'title', 'description', 'number',
            'standard', 'subject', 'subject_name',
            'chapter', 'chapter_name',
            'question_count', 'estimated_minutes',
            'is_active', 'created_at',
        ]

    def get_question_count(self, obj) -> int:
        return obj.questions.count()


class ProblemSetDetailSerializer(ProblemSetSerializer):
    """Extended serializer with full question list — used on assignment detail views."""
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(ProblemSetSerializer.Meta):
        fields = ProblemSetSerializer.Meta.fields + ['questions']


class AssignmentSerializer(serializers.ModelSerializer):
    problem_set = ProblemSetSerializer(read_only=True)
    problem_set_id = serializers.PrimaryKeyRelatedField(
        queryset=ProblemSet.objects.filter(is_active=True),
        source='problem_set',
        write_only=True,
    )
    subject_room_display = serializers.StringRelatedField(source='subject_room')

    class Meta:
        model = Assignment
        fields = [
            'id', 'subject_room', 'subject_room_display',
            'problem_set', 'problem_set_id',
            'assigned_by', 'assigned_at', 'due_at', 'number',
            'average_score', 'completion_rate',
        ]
        read_only_fields = ['assigned_by', 'assigned_at', 'average_score', 'completion_rate']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user.role != UserRole.TEACHER:
            raise serializers.ValidationError("Only teachers can create assignments.")
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['assigned_by'] = request.user
        return super().create(validated_data)


class AssignmentDetailSerializer(AssignmentSerializer):
    """
    Extended assignment serializer with full problem set questions
    and the current user's submission (for student views).
    """
    problem_set = ProblemSetDetailSerializer(read_only=True)
    my_submission = serializers.SerializerMethodField()

    class Meta(AssignmentSerializer.Meta):
        fields = AssignmentSerializer.Meta.fields + ['my_submission']

    def get_my_submission(self, obj) -> dict | None:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        try:
            submission = obj.submissions.get(student=request.user)
            return SubmissionSerializer(submission, context=self.context).data
        except Submission.DoesNotExist:
            return None


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = [
            'id', 'assignment', 'student',
            'score', 'completion', 'answers',
            'submitted_at', 'is_revised',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['student', 'score', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        if not request:
            return attrs

        user = request.user
        if user.role not in [UserRole.STUDENT, UserRole.OPEN_STUDENT]:
            raise serializers.ValidationError("Only students can submit answers.")

        # On create: check no existing submission
        if self.instance is None:
            assignment = attrs.get('assignment')
            if assignment and Submission.objects.filter(assignment=assignment, student=user).exists():
                raise serializers.ValidationError("You have already submitted this assignment.")

        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['student'] = request.user
        return super().create(validated_data)
