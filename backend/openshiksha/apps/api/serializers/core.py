"""
Core serializers for OpenShiksha API

Covers Question Bank, SubjectRoom, Assignment Pipeline, and Submission.
"""

from rest_framework import serializers

from openshiksha.apps.core.models import (
    Assignment,
    Chapter,
    ProblemSet,
    Question,
    QuestionSubpart,
    QuestionTag,
    Standard,
    Subject,
    SubjectRoom,
    Submission,
    User,
    UserRole,
)
from openshiksha.apps.edge.models import StudentProficiency, SubjectRoomQuestionMistake


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for the current user profile."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "grade"]
        read_only_fields = ["id", "username", "email", "first_name", "last_name", "role", "grade"]


class StandardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Standard
        fields = ["id", "number", "description"]


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["id", "name", "description"]


class ChapterSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    standard_number = serializers.IntegerField(source="standard.number", read_only=True)

    class Meta:
        model = Chapter
        fields = ["id", "name", "subject", "subject_name", "standard", "standard_number", "order"]


class QuestionTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionTag
        fields = ["id", "name", "tag_type"]


class QuestionSubpartSerializer(serializers.ModelSerializer):
    """Full subpart serializer — for admin/teacher use only (exposes correct_answer)."""

    tags = QuestionTagSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionSubpart
        fields = ["id", "index", "tags", "question_text", "options", "correct_answer", "variable_constraints"]


class QuestionSubpartStudentSerializer(serializers.ModelSerializer):
    """
    Student-safe subpart serializer — omits correct_answer.

    For MCQ/multi_select subparts, options are shuffled deterministically
    by (student_id, subpart_id) so each student sees a unique ordering.
    Keys are re-assigned by display position after shuffling.

    For numeric/fill_blank subparts with variable_constraints, {{var}} tokens
    in question_text and options are substituted with per-student values (Phase 2).
    """

    tags = QuestionTagSerializer(many=True, read_only=True)

    class Meta:
        model = QuestionSubpart
        fields = ["id", "index", "tags", "question_text", "options"]

    def to_representation(self, instance):
        from openshiksha.apps.api.croupier import shuffle_options_for_student, substitute_variables_for_student

        data = super().to_representation(instance)
        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            return data

        # Phase 2: Variable substitution (numeric/fill_blank with {{var}} tokens)
        if instance.variable_constraints:
            subst_text, subst_options, _ = substitute_variables_for_student(
                data["question_text"],
                data.get("options"),
                instance.variable_constraints,
                request.user.id,
                instance.id,
            )
            data["question_text"] = subst_text
            if subst_options is not None:
                data["options"] = subst_options

        # Phase 1: MCQ option shuffling (applied after variable substitution)
        options = data.get("options")
        if options:
            data["options"] = shuffle_options_for_student(options, request.user.id, instance.id)

        return data


class QuestionWithSubpartsStudentSerializer(serializers.ModelSerializer):
    """Question serializer using the student-safe subpart serializer."""

    subparts = QuestionSubpartStudentSerializer(many=True, read_only=True)
    tags = QuestionTagSerializer(many=True, read_only=True)
    question_type_display = serializers.CharField(source="get_question_type_display", read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "standard",
            "subject",
            "chapter",
            "question_type",
            "question_type_display",
            "difficulty",
            "tags",
            "subparts",
            "is_active",
            "created_at",
        ]


class QuestionSerializer(serializers.ModelSerializer):
    subparts = QuestionSubpartSerializer(many=True, read_only=True)
    tags = QuestionTagSerializer(many=True, read_only=True)
    question_type_display = serializers.CharField(source="get_question_type_display", read_only=True)
    chapter_name = serializers.CharField(source="chapter.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    standard_number = serializers.IntegerField(source="standard.number", read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "standard",
            "standard_number",
            "subject",
            "subject_name",
            "chapter",
            "chapter_name",
            "question_type",
            "question_type_display",
            "difficulty",
            "tags",
            "subparts",
            "is_active",
            "created_at",
        ]


class QuestionSubpartWriteSerializer(serializers.ModelSerializer):
    """Writable serializer for creating/updating question subparts."""

    class Meta:
        model = QuestionSubpart
        fields = ["index", "question_text", "options", "correct_answer", "variable_constraints"]


class QuestionWriteSerializer(serializers.ModelSerializer):
    """
    Writable serializer for teacher question authoring.

    Accepts nested subparts on create. Tags are set via IDs.
    Correct answers are stored per-subpart — never exposed to students
    via the read serializer.
    """

    subparts = QuestionSubpartWriteSerializer(many=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=QuestionTag.objects.all(),
        many=True,
        required=False,
        source="tags",
        write_only=True,
    )
    # Read-back fields after create
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "standard",
            "subject",
            "chapter",
            "question_type",
            "difficulty",
            "tag_ids",
            "subparts",
            "created_at",
        ]

    def validate_subparts(self, value):
        if not value:
            raise serializers.ValidationError("At least one subpart is required.")
        return value

    def create(self, validated_data):
        subparts_data = validated_data.pop("subparts")
        tags = validated_data.pop("tags", [])
        question = Question.objects.create(**validated_data)
        if tags:
            question.tags.set(tags)
        for subpart_data in subparts_data:
            QuestionSubpart.objects.create(question=question, **subpart_data)
        return question


class SubjectRoomSerializer(serializers.ModelSerializer):
    classroom_display = serializers.StringRelatedField(source="classroom")
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = SubjectRoom
        fields = [
            "id",
            "classroom",
            "classroom_display",
            "subject",
            "subject_name",
            "teacher",
            "teacher_name",
            "is_active",
            "student_count",
            "created_at",
        ]

    def get_student_count(self, obj) -> int:
        return obj.students.count()


class ProblemSetSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    chapter_name = serializers.CharField(source="chapter.name", read_only=True)

    class Meta:
        model = ProblemSet
        fields = [
            "id",
            "title",
            "description",
            "number",
            "standard",
            "subject",
            "subject_name",
            "chapter",
            "chapter_name",
            "question_count",
            "estimated_minutes",
            "is_active",
            "created_at",
        ]

    def get_question_count(self, obj) -> int:
        return obj.questions.count()


class ProblemSetDetailSerializer(ProblemSetSerializer):
    """Extended serializer with full question list — used on assignment detail views."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(ProblemSetSerializer.Meta):
        fields = ProblemSetSerializer.Meta.fields + ["questions"]


class ProblemSetStudentDetailSerializer(ProblemSetSerializer):
    """Student-facing problem set detail — uses student-safe question serializer (no correct_answer)."""

    questions = QuestionWithSubpartsStudentSerializer(many=True, read_only=True)

    class Meta(ProblemSetSerializer.Meta):
        fields = ProblemSetSerializer.Meta.fields + ["questions"]


class AssignmentSerializer(serializers.ModelSerializer):
    problem_set = ProblemSetSerializer(read_only=True)
    problem_set_id = serializers.PrimaryKeyRelatedField(
        queryset=ProblemSet.objects.filter(is_active=True),
        source="problem_set",
        write_only=True,
    )
    subject_room_display = serializers.StringRelatedField(source="subject_room")
    submission_count = serializers.SerializerMethodField()
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "subject_room",
            "subject_room_display",
            "problem_set",
            "problem_set_id",
            "assigned_by",
            "assigned_at",
            "due_at",
            "number",
            "average_score",
            "completion_rate",
            "submission_count",
            "student_count",
        ]
        read_only_fields = ["assigned_by", "assigned_at", "average_score", "completion_rate"]

    def get_submission_count(self, obj) -> int:
        return obj.submissions.count()

    def get_student_count(self, obj) -> int:
        return obj.subject_room.students.count()

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.role != UserRole.TEACHER:
            raise serializers.ValidationError("Only teachers can create assignments.")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["assigned_by"] = request.user
        return super().create(validated_data)


class AssignmentDetailSerializer(AssignmentSerializer):
    """
    Extended assignment serializer with full problem set questions
    and the current user's submission (for student views).

    Uses ProblemSetStudentDetailSerializer so correct_answer is never exposed
    to students via the assignment detail endpoint.
    """

    problem_set = ProblemSetStudentDetailSerializer(read_only=True)
    my_submission = serializers.SerializerMethodField()

    class Meta(AssignmentSerializer.Meta):
        fields = AssignmentSerializer.Meta.fields + ["my_submission"]

    def get_my_submission(self, obj) -> dict | None:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        try:
            submission = obj.submissions.get(student=request.user)
            return SubmissionSerializer(submission, context=self.context).data
        except Submission.DoesNotExist:
            return None


class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id",
            "assignment",
            "student",
            "student_name",
            "score",
            "completion",
            "answers",
            "submitted_at",
            "is_revised",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["student", "score", "created_at", "updated_at"]

    def get_student_name(self, obj) -> str:
        return obj.student.get_full_name() or obj.student.username

    def validate(self, attrs):
        request = self.context.get("request")
        if not request:
            return attrs

        user = request.user
        if user.role not in [UserRole.STUDENT, UserRole.OPEN_STUDENT]:
            raise serializers.ValidationError("Only students can submit answers.")

        # On create: check no existing submission
        if self.instance is None:
            assignment = attrs.get("assignment")
            if assignment and Submission.objects.filter(assignment=assignment, student=user).exists():
                raise serializers.ValidationError("You have already submitted this assignment.")

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["student"] = request.user
        return super().create(validated_data)


class ProblemSetWriteSerializer(serializers.ModelSerializer):
    """
    Writable serializer for teacher problem set creation.

    Accepts question_ids to link existing questions to the new problem set.
    """

    question_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Question.objects.filter(is_active=True),
        source="questions",
        required=False,
    )
    id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ProblemSet
        fields = [
            "id",
            "title",
            "description",
            "standard",
            "subject",
            "chapter",
            "estimated_minutes",
            "question_ids",
            "created_at",
        ]

    def validate_question_ids(self, value):
        if not value:
            raise serializers.ValidationError("At least one question is required.")
        return value

    def create(self, validated_data):
        questions = validated_data.pop("questions", [])
        problem_set = ProblemSet.objects.create(**validated_data)
        if questions:
            problem_set.questions.set(questions)
        return problem_set


class StudentProficiencySerializer(serializers.ModelSerializer):
    """
    Exposes a student's proficiency per question tag within a subject room.

    Groups naturally by subject_room → subject for frontend display.
    Score is 0.0–1.0; multiply by 100 for percentage display.
    """

    tag_name = serializers.CharField(source="question_tag.name", read_only=True)
    tag_type = serializers.CharField(source="question_tag.tag_type", read_only=True)
    subject_name = serializers.CharField(source="subject_room.subject.name", read_only=True)
    classroom_display = serializers.SerializerMethodField()

    class Meta:
        model = StudentProficiency
        fields = [
            "id",
            "tag_name",
            "tag_type",
            "subject_name",
            "subject_room",
            "classroom_display",
            "score",
            "rate",
            "percentile",
            "tick_count",
            "updated_at",
        ]
        read_only_fields = fields

    def get_classroom_display(self, obj) -> str:
        classroom = obj.subject_room.classroom
        return f"Standard {classroom.standard.number} {classroom.division}"


class QuestionMistakeSerializer(serializers.ModelSerializer):
    """
    Exposes a subject room's question mistake data for teachers.

    Ordered by regression (highest = hardest question for that class).
    question_text and question_type are from the first subpart of each question.
    """

    question_text = serializers.SerializerMethodField()
    question_type = serializers.SerializerMethodField()
    question_id = serializers.IntegerField(source="question.id", read_only=True)

    class Meta:
        model = SubjectRoomQuestionMistake
        fields = [
            "id",
            "question_id",
            "question_text",
            "question_type",
            "regression",
            "updated_at",
        ]
        read_only_fields = fields

    def get_question_text(self, obj) -> str:
        first_subpart = obj.question.subparts.order_by("index").first()
        return first_subpart.question_text if first_subpart else ""

    def get_question_type(self, obj) -> str:
        return obj.question.question_type
