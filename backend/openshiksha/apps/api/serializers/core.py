"""
Core serializers for OpenShiksha API

Covers Question Bank, SubjectRoom, Assignment Pipeline, and Submission.
"""

from rest_framework import serializers

from openshiksha.apps.core.models import (
    Assignment,
    Chapter,
    ClassRoom,
    ClassroomInviteCode,
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
from openshiksha.apps.edge.models import StudentProficiency, StudentProficiencySnapshot, SubjectRoomQuestionMistake


class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for the current user profile."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "grade",
            "phone_number",
            "email_reminders_opt_out",
        ]
        read_only_fields = ["id", "username", "role", "grade"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Writeable serializer for profile fields the user may update themselves."""

    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "email_reminders_opt_out"]

    def validate_email(self, value):
        if not value:
            return value
        qs = User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk if self.instance else None)
        if qs.exists():
            raise serializers.ValidationError("This email address is already in use.")
        return value


class ClassroomInviteCodeSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source="classroom.__str__", read_only=True)
    classroom_id = serializers.IntegerField(source="classroom.id", read_only=True)

    class Meta:
        model = ClassroomInviteCode
        fields = ["id", "code", "classroom_id", "classroom_name", "is_active", "expires_at", "created_at"]
        read_only_fields = fields


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
        fields = [
            "id",
            "index",
            "subpart_type",
            "tags",
            "question_text",
            "options",
            "correct_answer",
            "variable_constraints",
            "image_url",
            "solution_text",
            "hint_text",
            "widget_kind",
            "widget_config",
        ]


def _substitute_in_json(node, sampled_values: dict):
    """Walk a JSON tree and substitute ``{{var}}`` tokens in every string leaf.

    Reuses the existing ``substitute_variables`` helper so widget configs share
    the croupier's per-student token semantics — same tokens, same evaluator,
    same fallback behaviour on bad expressions. Non-string leaves
    (numbers, bools, None) pass through unchanged; nested dicts and lists are
    recursed into.
    """
    from openshiksha.apps.api.croupier import substitute_variables

    if isinstance(node, str):
        return substitute_variables(node, sampled_values)
    if isinstance(node, dict):
        return {k: _substitute_in_json(v, sampled_values) for k, v in node.items()}
    if isinstance(node, list):
        return [_substitute_in_json(v, sampled_values) for v in node]
    return node


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
        fields = [
            "id",
            "index",
            "subpart_type",
            "tags",
            "question_text",
            "options",
            "image_url",
            "solution_text",
            "hint_text",
            "is_interactive",
            "interactive_html",
            "widget_kind",
            "widget_config",
        ]

    def to_representation(self, instance):
        from openshiksha.apps.api.croupier import (
            shuffle_options_for_student,
            substitute_variables,
            substitute_variables_for_student,
        )

        data = super().to_representation(instance)

        # Worked solution is anti-cheat gated: only included once the student's
        # submission has been graded (set by AssignmentViewSet context). Hints
        # are allowed during practice, so they always pass through.
        if not self.context.get("include_solutions"):
            data.pop("solution_text", None)

        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            return data

        # Phase 2: Variable substitution (numeric/fill_blank with {{var}} tokens)
        if instance.variable_constraints:
            subst_text, subst_options, sampled_values = substitute_variables_for_student(
                data["question_text"],
                data.get("options"),
                instance.variable_constraints,
                request.user.id,
                instance.id,
            )
            data["question_text"] = subst_text
            if subst_options is not None:
                data["options"] = subst_options

            # M7-11: substitute the same per-student values into the interactive
            # widget HTML so the sandboxed iframe shows this student's numbers.
            if data.get("interactive_html"):
                data["interactive_html"] = substitute_variables(data["interactive_html"], sampled_values)

            # Solutions & hints share the body's per-student sampled values so
            # the worked-out steps reference the same numbers the student sees
            # in the question. ``solution_text`` is only present in the payload
            # when ``include_solutions`` is set above; guard accordingly.
            if "solution_text" in data:
                data["solution_text"] = substitute_variables(data["solution_text"], sampled_values)
            if "hint_text" in data:
                data["hint_text"] = substitute_variables(data["hint_text"], sampled_values)

            # IW-3b: substitute the same per-student values into widget_config so
            # the framework runtime receives already-resolved numbers in its
            # init payload. We walk the JSON tree and only touch string leaves,
            # leaving numbers/bools/None untouched.
            if data.get("widget_config"):
                data["widget_config"] = _substitute_in_json(data["widget_config"], sampled_values)

        # Phase 1: MCQ option shuffling (applied after variable substitution)
        options = data.get("options")
        if options:
            data["options"] = shuffle_options_for_student(options, request.user.id, instance.id)

        return data


class QuestionWithSubpartsStudentSerializer(serializers.ModelSerializer):
    """Question serializer using the student-safe subpart serializer.

    Substitutes ``{{var}}`` tokens in ``stem_text`` for authenticated students
    using the first subpart's per-student seeded values. This keeps stem
    numbers consistent with the body of the question the student is solving,
    and is a no-op for stems that don't reference variables (the dominant
    case in cabinet content).
    """

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
            "stem_text",
            "tags",
            "subparts",
            "is_active",
            "created_at",
        ]

    def to_representation(self, instance):
        from openshiksha.apps.api.croupier import sample_variable_values, substitute_variables

        data = super().to_representation(instance)
        stem = data.get("stem_text")
        if not stem or "{{" not in stem:
            return data

        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            return data

        # Stems can reference variables shared with their subparts (e.g. a
        # cabinet container whose prompt mentions a quantity that subparts then
        # ask about). We seed off the first subpart so the stem's numbers
        # match the first subpart the student sees — deterministic per
        # (student_id, subpart_id) and zero-cost when no variables are set.
        first = instance.subparts.order_by("index").first()
        if first and first.variable_constraints:
            values = sample_variable_values(first.variable_constraints, request.user.id, first.id)
            data["stem_text"] = substitute_variables(stem, values)
        return data


class QuestionSerializer(serializers.ModelSerializer):
    subparts = QuestionSubpartSerializer(many=True, read_only=True)
    tags = QuestionTagSerializer(many=True, read_only=True)
    question_type_display = serializers.CharField(source="get_question_type_display", read_only=True)
    chapter_name = serializers.CharField(source="chapter.name", read_only=True)
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    standard_number = serializers.IntegerField(source="standard.number", read_only=True)
    # AIV-3a — see ProblemSetSerializer for rationale. "In use" here means a
    # problem set that contains this question is referenced by an Assignment.
    assigned_count = serializers.SerializerMethodField()
    has_graded_submissions = serializers.SerializerMethodField()

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
            "stem_text",
            "tags",
            "subparts",
            "assigned_count",
            "has_graded_submissions",
            "is_active",
            "created_at",
        ]

    def get_assigned_count(self, obj) -> int:
        anno = getattr(obj, "assigned_count_anno", None)
        if anno is not None:
            return int(anno)
        return Assignment.objects.filter(problem_set__questions=obj).count()

    def get_has_graded_submissions(self, obj) -> bool:
        anno = getattr(obj, "has_graded_submissions_anno", None)
        if anno is not None:
            return bool(anno)
        return Submission.objects.filter(assignment__problem_set__questions=obj, score__isnull=False).exists()


class QuestionSubpartWriteSerializer(serializers.ModelSerializer):
    """Writable serializer for creating/updating question subparts."""

    class Meta:
        model = QuestionSubpart
        fields = [
            "index",
            "subpart_type",
            "question_text",
            "options",
            "correct_answer",
            "variable_constraints",
            "solution_text",
            "hint_text",
            "widget_kind",
            "widget_config",
        ]
        extra_kwargs = {
            "subpart_type": {"required": False},
            "solution_text": {"required": False},
            "hint_text": {"required": False},
            "widget_kind": {"required": False},
            "widget_config": {"required": False},
        }

    def validate(self, attrs):
        from openshiksha.apps.core.widgets import validate_widget_config

        kind = (
            attrs.get("widget_kind", "")
            if "widget_kind" in attrs
            else (self.instance.widget_kind if self.instance else "")
        )
        config = (
            attrs.get("widget_config")
            if "widget_config" in attrs
            else (self.instance.widget_config if self.instance else {})
        )
        if kind:
            validate_widget_config(kind, config if config is not None else {})
        return super().validate(attrs)


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


class SubjectRoomAdminSerializer(serializers.ModelSerializer):
    """Admin write/read serializer for subject rooms with school-scoped validation."""

    subject_name = serializers.CharField(source="subject.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.full_name", read_only=True)
    classroom_display = serializers.StringRelatedField(source="classroom", read_only=True)
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
        read_only_fields = ["id", "is_active", "created_at"]

    def get_student_count(self, obj) -> int:
        return obj.students.count()

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_admin:
            return attrs
        if user.school_id is None:
            raise serializers.ValidationError("Your account is not linked to a school.")
        classroom = attrs.get("classroom") or getattr(self.instance, "classroom", None)
        if classroom is not None and classroom.school_id != user.school_id:
            raise serializers.ValidationError({"classroom": "Classroom must belong to your school."})
        teacher = attrs.get("teacher") or getattr(self.instance, "teacher", None)
        if teacher is not None and teacher.school_id != user.school_id:
            raise serializers.ValidationError({"teacher": "Teacher must belong to your school."})
        return attrs


class ClassRoomSerializer(serializers.ModelSerializer):
    """School admin serializer for classroom CRUD. School is forced server-side."""

    standard_number = serializers.IntegerField(source="standard.number", read_only=True)
    class_teacher_name = serializers.CharField(source="class_teacher.full_name", read_only=True, default=None)
    student_count = serializers.SerializerMethodField()
    school = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ClassRoom
        fields = [
            "id",
            "school",
            "standard",
            "standard_number",
            "division",
            "class_teacher",
            "class_teacher_name",
            "academic_year",
            "is_active",
            "student_count",
            "created_at",
        ]
        read_only_fields = ["id", "school", "is_active", "created_at"]

    def get_student_count(self, obj) -> int:
        annotated = getattr(obj, "num_students", None)
        return annotated if annotated is not None else obj.students.count()

    def validate_class_teacher(self, value):
        if value is None:
            return value
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is not None and value.school_id != user.school_id:
            raise serializers.ValidationError("Class teacher must belong to your school.")
        if value.role != UserRole.TEACHER:
            raise serializers.ValidationError("Assigned user must be a teacher.")
        return value


class ProblemSetSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    chapter_name = serializers.CharField(source="chapter.name", read_only=True)
    # AIV-3a: edit-safety read flags. Integrity is already guaranteed by AIV-1/2
    # (snapshots); these flags exist only to drive teacher UX so the editor can
    # say "this is in use" and mean it. Backed by queryset annotations on
    # ProblemSetViewSet.get_queryset to avoid N+1 on list endpoints; falls back
    # to a single per-row query when the annotation isn't present (e.g. POST
    # response on freshly created rows).
    assigned_count = serializers.SerializerMethodField()
    has_graded_submissions = serializers.SerializerMethodField()

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
            "is_remedial",
            "source_assignment",
            "assigned_count",
            "has_graded_submissions",
            "created_at",
        ]

    def get_question_count(self, obj) -> int:
        return obj.questions.count()

    def get_assigned_count(self, obj) -> int:
        anno = getattr(obj, "assigned_count_anno", None)
        if anno is not None:
            return int(anno)
        return obj.assignments.count()

    def get_has_graded_submissions(self, obj) -> bool:
        anno = getattr(obj, "has_graded_submissions_anno", None)
        if anno is not None:
            return bool(anno)
        return Submission.objects.filter(assignment__problem_set=obj, score__isnull=False).exists()


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
    child_submission_status = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    # ``my_submission`` is the student's own submission row, surfaced on
    # *every* assignment payload (list + detail) so the dashboard can group
    # rows into Due Soon / Overdue / Completed without an extra round-trip
    # per assignment. Used to be on AssignmentDetailSerializer only, which
    # meant the list view never knew whether a row was already submitted —
    # the StudentDashboard couldn't tell the two apart and showed every
    # assignment as "Start" + "Due in N days", even after grading.
    my_submission = serializers.SerializerMethodField()

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
            "child_submission_status",
            "target_student",
            "my_submission",
            "closed_at",
            "status",
        ]
        read_only_fields = ["assigned_by", "assigned_at", "average_score", "completion_rate", "closed_at", "status"]

    def get_my_submission(self, obj) -> dict | None:
        """Return the current student's own Submission (if any).

        Returns ``None`` for unauthenticated requests and for non-student
        roles (teachers and admins don't have a "my" submission against
        another teacher's assignment). Uses the prefetch cache populated
        by ``AssignmentViewSet.get_queryset`` so listing N assignments
        does not fan out into N submission queries.
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        user = request.user
        if getattr(user, "role", None) not in (UserRole.STUDENT, UserRole.OPEN_STUDENT):
            return None
        # When the viewset prefetched with a Prefetch(..., to_attr="my_submissions")
        # filtered to the current user, read it directly to avoid N+1.
        prefetched = getattr(obj, "my_submissions", None)
        if prefetched is not None:
            submission = prefetched[0] if prefetched else None
        else:
            submission = obj.submissions.filter(student=user).first()
        if submission is None:
            return None
        return SubmissionSerializer(submission, context=self.context).data

    def get_submission_count(self, obj) -> int:
        return obj.submissions.count()

    def get_student_count(self, obj) -> int:
        return obj.subject_room.students.count()

    def get_child_submission_status(self, obj) -> str | None:
        """
        For parent role with ?student=<id>: returns 'submitted' or 'not_submitted'.
        Returns None for all other roles — field is ignored on student/teacher responses.
        Uses prefetched submissions when available to avoid N+1.
        """
        request = self.context.get("request")
        if not request:
            return None
        user = request.user
        if user.role != UserRole.PARENT:
            return None
        child_id = request.query_params.get("student")
        if not child_id:
            return None
        try:
            child_pk = int(child_id)
        except (ValueError, TypeError):
            return None
        # Use prefetch cache if present, else fall back to query
        if "submissions" in getattr(obj, "_prefetched_objects_cache", {}):
            submitted = any(s.student_id == child_pk for s in obj.submissions.all())
        else:
            submitted = obj.submissions.filter(student_id=child_pk).exists()
        return "submitted" if submitted else "not_submitted"

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.user.role != UserRole.TEACHER:
            raise serializers.ValidationError("Only teachers can create assignments.")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["assigned_by"] = request.user
        # AIV-1: freeze the problem set's questions at assign time so the
        # grader and student renderer can never be affected by later edits.
        from openshiksha.apps.core.snapshots import build_assignment_snapshot

        validated_data["assigned_content"] = build_assignment_snapshot(validated_data["problem_set"])
        return super().create(validated_data)


class AssignmentDetailSerializer(AssignmentSerializer):
    """
    Extended assignment serializer with full problem set questions
    and the current user's submission (for student views).

    Uses ProblemSetStudentDetailSerializer so correct_answer is never exposed
    to students via the assignment detail endpoint.

    AIV-2b: when ``Assignment.assigned_content`` is populated, the embedded
    problem-set's ``questions`` array is built from the snapshot — so a student
    always sees exactly what they were assigned, even after the live set
    drifts. Response shape is preserved 1:1 with the live path.
    """

    # ``my_submission`` is inherited from AssignmentSerializer now — the
    # detail serializer only swaps the problem-set serializer for the
    # student-safe variant that hides ``correct_answer``.
    problem_set = ProblemSetStudentDetailSerializer(read_only=True)

    class Meta(AssignmentSerializer.Meta):
        fields = AssignmentSerializer.Meta.fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        snapshot = getattr(instance, "assigned_content", None)
        if not (snapshot and snapshot.get("questions")):
            return data

        from openshiksha.apps.core.snapshots import render_snapshot_for_student

        request = self.context.get("request")
        student_id = request.user.id if (request and request.user.is_authenticated) else None
        include_solutions = bool(self.context.get("include_solutions"))

        if isinstance(data.get("problem_set"), dict):
            data["problem_set"]["questions"] = render_snapshot_for_student(
                snapshot,
                student_id=student_id,
                include_solutions=include_solutions,
            )
        return data


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

        # Block writes (create or update) when the target assignment is closed.
        # Reads remain unaffected — students should still see closed assignments.
        assignment = attrs.get("assignment") or (self.instance and self.instance.assignment)
        if assignment is not None and assignment.is_closed:
            raise serializers.ValidationError(
                {"detail": "This assignment is closed and no longer accepts submissions."}
            )

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
    question_tag (integer FK) is included so the frontend can query history.
    """

    tag_name = serializers.CharField(source="question_tag.name", read_only=True)
    tag_type = serializers.CharField(source="question_tag.tag_type", read_only=True)
    subject_name = serializers.CharField(source="subject_room.subject.name", read_only=True)
    classroom_display = serializers.SerializerMethodField()

    class Meta:
        model = StudentProficiency
        fields = [
            "id",
            "question_tag",
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


class StudentProficiencySnapshotSerializer(serializers.ModelSerializer):
    """Read-only snapshot serializer — minimal payload for sparkline trend data."""

    class Meta:
        model = StudentProficiencySnapshot
        fields = ["id", "score", "recorded_at"]
        read_only_fields = fields


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
