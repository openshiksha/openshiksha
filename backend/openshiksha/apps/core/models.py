"""
Core models for OpenShiksha

Modern implementation of core business models.
Will be populated based on legacy models with improvements.
"""

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Validator for fraction values (0.0 to 1.0)
FRACTION_VALIDATOR = [MinValueValidator(0.0), MaxValueValidator(1.0)]


# User Groups and Roles
class UserRole(models.TextChoices):
    """User role choices based on legacy Group model"""

    STUDENT = "student", "Student"
    TEACHER = "teacher", "Teacher"
    PARENT = "parent", "Parent"
    ADMIN = "admin", "School Admin"
    OPEN_STUDENT = "open_student", "Open Student"  # Legacy: students without school


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser

    Combines legacy User + UserInfo models for better performance.

    Supports multiple user types:
    - Student: Regular school students
    - Teacher: School teachers
    - Parent: Parents monitoring their children
    - School Admin: School administrators
    - Open Student: Students not enrolled in a school
    """

    # Core role and associations
    role = models.CharField(max_length=20, choices=UserRole.choices, help_text="The type of user account")

    school = models.ForeignKey(
        "School",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        help_text="The school this user belongs to (null for open students)",
    )

    # Student-specific fields
    grade = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Grade/Standard for students (1-12)",
    )

    # Parent-specific fields
    children = models.ManyToManyField(
        "self", symmetrical=False, blank=True, related_name="parents", help_text="Children managed by this parent"
    )

    # Additional profile fields
    phone_number = models.CharField(max_length=15, blank=True, help_text="Contact phone number")

    date_of_birth = models.DateField(null=True, blank=True, help_text="Date of birth")

    # Notification preferences
    email_reminders_opt_out = models.BooleanField(
        default=False,
        help_text="If True, the student will not receive assignment due-date reminder emails.",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["role", "school"]),
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} ({self.get_role_display()})"
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role in [UserRole.STUDENT, UserRole.OPEN_STUDENT]

    @property
    def is_teacher(self):
        return self.role == UserRole.TEACHER

    @property
    def is_parent(self):
        return self.role == UserRole.PARENT

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


# Educational Structure Models


class Board(models.Model):
    """
    Educational board/curriculum (e.g., CBSE, ICSE, State Board)
    Based on legacy Board model
    """

    name = models.CharField(max_length=255, unique=True, help_text="Name of the educational board (e.g., CBSE, ICSE)")

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "boards"
        ordering = ["name"]

    def __str__(self):
        return self.name


class School(models.Model):
    """
    School model
    Based on legacy School model
    """

    name = models.CharField(max_length=255, help_text="Full name of the school")

    board = models.ForeignKey(
        Board,
        on_delete=models.PROTECT,
        related_name="schools",
        help_text="The educational board/curriculum this school follows",
    )

    # Contact information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)

    # Features (from legacy SchoolProfile)
    focus_enabled = models.BooleanField(default=False, help_text="Whether the focus rooms feature is enabled")

    sms_enabled = models.BooleanField(default=False, help_text="Whether SMS notifications are enabled")

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "schools"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["board", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.board.name})"


class Standard(models.Model):
    """
    Grade/Standard level (1-12)
    Based on legacy Standard model
    """

    number = models.PositiveIntegerField(
        unique=True, validators=[MinValueValidator(1), MaxValueValidator(12)], help_text="Grade number (1-12)"
    )

    description = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "standards"
        ordering = ["number"]

    def __str__(self):
        return f"Standard {self.number}"


class Subject(models.Model):
    """
    Subject model (e.g., Mathematics, Science)
    Based on legacy Subject model
    """

    name = models.CharField(max_length=255, unique=True, help_text="Name of the subject")

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subjects"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Chapter(models.Model):
    """
    Chapter/Topic model
    Based on legacy Chapter model
    """

    name = models.CharField(max_length=255, help_text="Name of the chapter/topic")

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name="chapters", help_text="The subject this chapter belongs to"
    )

    standard = models.ForeignKey(
        Standard, on_delete=models.CASCADE, related_name="chapters", help_text="The grade/standard this chapter is for"
    )

    order = models.PositiveIntegerField(default=0, help_text="Display order within subject")

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chapters"
        ordering = ["subject", "standard", "order"]
        unique_together = [["subject", "standard", "name"]]

    def __str__(self):
        return f"{self.subject.name} - Std {self.standard.number} - {self.name}"


class ClassRoom(models.Model):
    """
    Classroom model - a group of students in same grade/division
    Based on legacy ClassRoom model
    """

    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="classrooms", help_text="The school this classroom belongs to"
    )

    standard = models.ForeignKey(
        Standard, on_delete=models.PROTECT, related_name="classrooms", help_text="The grade/standard of this classroom"
    )

    division = models.CharField(max_length=50, help_text="Division name (e.g., A, B, C)")

    class_teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="classes_managed",
        limit_choices_to={"role": UserRole.TEACHER},
        help_text="The teacher managing this classroom",
    )

    students = models.ManyToManyField(
        User,
        related_name="classes_enrolled",
        limit_choices_to={"role__in": [UserRole.STUDENT, UserRole.OPEN_STUDENT]},
        blank=True,
        help_text="Students enrolled in this classroom",
    )

    academic_year = models.CharField(max_length=20, help_text="Academic year (e.g., 2024-25)")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "classrooms"
        ordering = ["school", "standard", "division"]
        unique_together = [["school", "standard", "division", "academic_year"]]
        indexes = [
            models.Index(fields=["school", "academic_year", "is_active"]),
        ]

    def __str__(self):
        return f"{self.school.name} - Std {self.standard.number} - Div {self.division}"


# ─────────────────────────────────────────────────────────────
# Question Bank Models
# ─────────────────────────────────────────────────────────────


class QuestionTag(models.Model):
    """
    Tag for classifying questions.

    Improvement over legacy: legacy tags had no type categorization, making
    it impossible to distinguish concept tags from difficulty markers programmatically.
    """

    name = models.CharField(max_length=255, unique=True)
    tag_type = models.CharField(
        max_length=50,
        choices=[
            ("concept", "Concept"),
            ("skill", "Skill"),
            ("difficulty", "Difficulty"),
            ("special", "Special"),
        ],
        default="concept",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "question_tags"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.tag_type})"


class QuestionType(models.TextChoices):
    MCQ = "mcq", "Multiple Choice"
    FILL_BLANK = "fill_blank", "Fill in the Blank"
    MATCHING = "matching", "Matching"
    MULTI_SELECT = "multi_select", "Multi Select"
    NUMERIC = "numeric", "Numeric Answer"
    SHORT_ANSWER = "short_answer", "Short Answer"
    # M7-03: summary type for a Question whose subparts have heterogeneous types.
    # Only ever set on Question.question_type — never on a single subpart.
    COMPOUND = "compound", "Compound (mixed subpart types)"


class Question(models.Model):
    """
    A question in the question bank.

    Improvement over legacy:
    - question_type enum (legacy only had MCQ via Cabinet)
    - explicit difficulty 1-5 (legacy derived this from tags)
    - is_active for soft delete
    - created_by for audit trail
    - null school = shared OpenShiksha bank (preserved from legacy)
    """

    school = models.ForeignKey(
        "School",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="questions",
        help_text="null = OpenShiksha shared question bank",
    )
    standard = models.ForeignKey(
        "Standard",
        on_delete=models.PROTECT,
        related_name="questions",
    )
    subject = models.ForeignKey(
        "Subject",
        on_delete=models.PROTECT,
        related_name="questions",
    )
    chapter = models.ForeignKey(
        "Chapter",
        on_delete=models.PROTECT,
        related_name="questions",
    )
    tags = models.ManyToManyField(QuestionTag, blank=True, related_name="questions")
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MCQ,
    )
    difficulty = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Difficulty level: 1=easiest, 5=hardest",
    )
    is_active = models.BooleanField(default=True)
    stem_text = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Optional shared stem rendered once above the subpart list. "
            "Cabinet compound questions share a leading paragraph; the importer "
            "lifts it here so each subpart's question_text holds only the per-part "
            "prompt. Hand-authored questions leave this blank."
        ),
    )
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions"
        indexes = [
            models.Index(fields=["chapter", "is_active"]),
            models.Index(fields=["school", "standard", "subject"]),
        ]

    def __str__(self):
        return f"Q{self.pk} ({self.get_question_type_display()}, Std {self.standard.number}, {self.subject.name})"


class QuestionSubpart(models.Model):
    """
    A subpart of a question (most questions have one; some have multiple).

    Improvement over legacy: correct_answer stored as JSONField for fast grading
    fallback. Legacy stored answers only in Cabinet (external service).
    """

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="subparts",
    )
    index = models.PositiveIntegerField(help_text="Order within question (0-indexed)")
    subpart_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        blank=True,
        default="",
        help_text=(
            "Per-subpart answer type (mcq / numeric / fill_blank / …). Cabinet "
            "stored type per subpart; the modern flat Question.question_type lost "
            "it. The grader and the student widget dispatch on this, falling back "
            "to the parent Question.question_type when blank (hand-authored rows)."
        ),
    )
    tags = models.ManyToManyField(QuestionTag, blank=True, related_name="subparts")
    question_text = models.TextField(
        blank=True,
        default="",
        help_text="LaTeX or plain text for the question prompt. Use $...$ for inline math.",
    )
    options = models.JSONField(
        null=True,
        blank=True,
        help_text='MCQ choices: [{"key": "A", "text": "..."}, ...]. Null for non-MCQ types.',
    )
    correct_answer = models.JSONField(
        default=dict,
        help_text='Answer data: e.g. {"type": "mcq", "answer": 2} or {"type": "fill_blank", "answer": "42"}',
    )
    variable_constraints = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Variable definitions for token substitution. "
            'e.g. {"a": {"min": 1, "max": 9, "integer": true}}. '
            "Tokens {{a}} in question_text/options are replaced per student."
        ),
    )
    image_url = models.URLField(
        max_length=2000,
        blank=True,
        default="",
        help_text="Optional image shown above the question text (teacher-provided URL)",
    )
    solution_text = models.TextField(
        blank=True,
        default="",
        help_text=(
            "Step-by-step worked solution (plain text or KaTeX). " "Populated by Cabinet import or LLM generation."
        ),
    )
    hint_text = models.TextField(
        blank=True,
        default="",
        help_text=("Progressive hint shown to struggling students. " "Populated by Cabinet import or teacher."),
    )
    is_interactive = models.BooleanField(
        default=False,
        help_text=(
            "DEPRECATED (IW-7) — paired with interactive_html below. The going-"
            "forward signal that a subpart carries a widget is widget_kind being "
            "non-blank; this flag is kept only so the legacy thermo question "
            "keeps rendering until the migration command stamps it with "
            "widget_kind='custom-html'. Do not set on new rows."
        ),
    )
    interactive_html = models.TextField(
        blank=True,
        default="",
        help_text=(
            "DEPRECATED (IW-7) — raw authored widget HTML, kept as a read-only "
            "legacy surface until the migration command moves its content into "
            "widget_kind='custom-html' + widget_config={'html': <this>}. New "
            "authoring MUST use widget_kind + widget_config; this column will be "
            "dropped once the legacy thermo row has been migrated. SECURITY "
            "invariants unchanged while present: stored raw, NEVER rendered into "
            "the app DOM, delivered ONLY to a sandboxed "
            '<iframe sandbox="allow-scripts"> (no allow-same-origin).'
        ),
    )
    widget_kind = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text=(
            "Registry key of an interactive widget (e.g. 'thermo-piston', "
            "'custom-html'). Blank = no widget. The kind-based path is the "
            "ONE going-forward Widgets Framework contract — the legacy "
            "interactive_html escape hatch above is deprecated in favour of "
            "widget_kind='custom-html' + widget_config={'html': ...} (IW-7)."
        ),
    )
    widget_config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Per-widget config validated against the kind's params schema. "
            "May contain {{var}} tokens substituted per student by the "
            "serializer (IW-3b)."
        ),
    )

    class Meta:
        db_table = "question_subparts"
        ordering = ["index"]
        unique_together = [["question", "index"]]

    def __str__(self):
        return f"Q{self.question_id} subpart {self.index}"


class SubjectRoom(models.Model):
    """
    A subject-specific grouping within a classroom — one per subject per class.

    Improvement over legacy:
    - is_active for year-end archiving without deletion
    - unique_together enforces one SubjectRoom per subject per classroom
    """

    classroom = models.ForeignKey(
        "ClassRoom",
        on_delete=models.CASCADE,
        related_name="subject_rooms",
    )
    subject = models.ForeignKey(
        "Subject",
        on_delete=models.PROTECT,
        related_name="subject_rooms",
    )
    teacher = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="subject_rooms_taught",
        limit_choices_to={"role": UserRole.TEACHER},
    )
    students: models.ManyToManyField = models.ManyToManyField(
        "User",
        related_name="subject_rooms_enrolled",
        blank=True,
        limit_choices_to={"role__in": [UserRole.STUDENT, UserRole.OPEN_STUDENT]},
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "subject_rooms"
        unique_together = [["classroom", "subject"]]
        indexes = [
            models.Index(fields=["classroom", "is_active"]),
        ]

    def __str__(self):
        return f"{self.classroom} — {self.subject.name}"


# ─────────────────────────────────────────────────────────────
# Assignment Pipeline Models
# ─────────────────────────────────────────────────────────────


class ProblemSet(models.Model):
    """
    A curated list of questions that can be assigned to a SubjectRoom.

    Replaces legacy AssignmentQuestionsList.

    Improvement over legacy:
    - title as explicit field (legacy computed it from chapter+number)
    - estimated_minutes (new — teachers can set time expectations)
    - is_active soft delete
    - created_by audit trail
    - null school = shared OpenShiksha problem set
    """

    school = models.ForeignKey(
        "School",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="problem_sets",
        help_text="null = shared OpenShiksha problem set",
    )
    standard = models.ForeignKey(
        "Standard",
        on_delete=models.PROTECT,
        related_name="problem_sets",
    )
    subject = models.ForeignKey(
        "Subject",
        on_delete=models.PROTECT,
        related_name="problem_sets",
    )
    chapter = models.ForeignKey(
        "Chapter",
        on_delete=models.PROTECT,
        related_name="problem_sets",
    )
    questions = models.ManyToManyField(
        Question,
        related_name="problem_sets",
        blank=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    number = models.PositiveIntegerField(
        default=1,
        help_text="Series number within same chapter (disambiguates multiple problem sets per chapter)",
    )
    estimated_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Estimated completion time in minutes",
    )
    is_active = models.BooleanField(default=True)
    is_remedial = models.BooleanField(
        default=False,
        help_text="Auto-created by grader for students scoring below the remedial threshold",
    )
    source_assignment = models.ForeignKey(
        "Assignment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="remedial_problem_sets",
        help_text="The original assignment this remedial was created from",
    )
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="problem_sets_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "problem_sets"
        unique_together = [["school", "standard", "subject", "chapter", "number"]]
        indexes = [
            models.Index(fields=["chapter", "is_active"]),
        ]

    def __str__(self):
        return f"{self.title} (Std {self.standard.number}, {self.subject.name}, Ch {self.chapter.name} #{self.number})"


class ProblemSetVersion(models.Model):
    """
    AIV-7: immutable, deduplicated content version for a ``ProblemSet``.

    Every assignment created (or re-synced) points at one of these rows via
    ``Assignment.problem_set_version``. Identical content under the same set
    is stored once — ``unique_together = [problem_set, content_hash]`` plus
    ``get_or_create_version_for(problem_set)`` enforces dedup.

    Rows are **never mutated** after creation. The grader, the student
    serializer, the drift check, and the diff/re-sync flow all read
    ``self.content`` here in preference to the per-assignment
    ``Assignment.assigned_content`` snapshot kept for backward compatibility.
    """

    problem_set = models.ForeignKey(
        "ProblemSet",
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField(
        help_text="1-based ordinal within the parent set, assigned at creation time.",
    )
    content_hash = models.CharField(
        max_length=64,
        help_text="sha256 over the canonical (sort_keys) JSON of the questions block. Drives dedup.",
    )
    content = models.JSONField(
        help_text="Frozen snapshot dict — the same shape build_assignment_snapshot() returns.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="problem_set_versions_created",
        help_text=(
            "Teacher whose action minted this version (assigned the set, or re-synced "
            "an assignment). Null for backfilled rows."
        ),
    )

    class Meta:
        db_table = "problem_set_versions"
        unique_together = [["problem_set", "content_hash"]]
        ordering = ["problem_set_id", "version_number"]
        indexes = [
            models.Index(fields=["problem_set", "-version_number"]),
        ]

    def __str__(self):
        return f"{self.problem_set_id}@v{self.version_number}"


class Assignment(models.Model):
    """
    An assignment of a ProblemSet to a SubjectRoom.

    Improvement over legacy:
    - Direct subject_room FK instead of GenericFK (legacy used GenericFK which
      caused N+1 queries and made filtering impossible)
    - assigned_by for accountability
    - assigned_at auto_now_add instead of manual timestamp
    - Cached aggregates (average_score, completion_rate) for fast dashboard queries
    """

    subject_room = models.ForeignKey(
        SubjectRoom,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    problem_set = models.ForeignKey(
        ProblemSet,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    assigned_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="assignments_created",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField()
    number = models.PositiveIntegerField(
        default=1,
        help_text="Disambiguates if same problem set is assigned twice to same room",
    )
    target_student = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="targeted_assignments",
        limit_choices_to={"role__in": ["student", "open_student"]},
        help_text="If set, only this student sees this assignment (used for per-student remedials). Null = class-wide.",
    )

    # Cached aggregates — updated after grading runs
    average_score = models.FloatField(
        null=True,
        blank=True,
        validators=FRACTION_VALIDATOR,
        help_text="Average submission score (0.0–1.0), cached after grading",
    )
    completion_rate = models.FloatField(
        null=True,
        blank=True,
        validators=FRACTION_VALIDATOR,
        help_text="Fraction of students who have submitted (0.0–1.0)",
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When set, the assignment no longer accepts submissions.",
    )
    assigned_content = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Frozen copy of the problem set's questions at assign time. Source "
            "of truth for grading and rendering this assignment — editing the "
            "live ProblemSet/Question/Subpart afterwards leaves this snapshot "
            "untouched. See apps.core.snapshots.build_assignment_snapshot. "
            "AIV-7: kept for backward compatibility; the canonical content "
            "source is now ``problem_set_version`` below. New writers populate "
            "both fields so readers can still fall back when the FK is null."
        ),
    )
    problem_set_version = models.ForeignKey(
        "ProblemSetVersion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="assignments",
        help_text=(
            "AIV-7: the deduplicated, immutable content version this assignment "
            "pins. Preferred source of truth; falls back to ``assigned_content`` "
            "when null (legacy rows the backfill couldn't reach)."
        ),
    )

    class Meta:
        db_table = "assignments"
        indexes = [
            models.Index(fields=["subject_room", "due_at"]),
            models.Index(fields=["assigned_at"]),
        ]

    def __str__(self):
        return f"Assignment: {self.problem_set.title} → {self.subject_room} (due {self.due_at.date()})"

    @property
    def is_closed(self) -> bool:
        return self.closed_at is not None

    @property
    def status(self) -> str:
        if self.closed_at is not None:
            return "closed"
        from django.utils import timezone

        if self.due_at < timezone.now():
            return "overdue"
        return "active"


class Submission(models.Model):
    """
    A student's submission for an assignment.

    Improvement over legacy:
    - answers JSONField stores student answers locally (legacy stored only in Cabinet)
      enables re-grading without Cabinet and offline review
    - submitted_at nullable — student can save in-progress work before final submit
    - created_at/updated_at tracks when student started and last edited
    - score renamed from marks (clearer it's a fraction 0–1, not a point count)
    """

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="submissions",
        limit_choices_to={"role__in": [UserRole.STUDENT, UserRole.OPEN_STUDENT]},
    )
    score = models.FloatField(
        null=True,
        blank=True,
        validators=FRACTION_VALIDATOR,
        help_text="Fraction of marks obtained (0.0–1.0). Null until graded.",
    )
    completion = models.FloatField(
        default=0.0,
        validators=FRACTION_VALIDATOR,
        help_text="Fraction of questions attempted (0.0–1.0)",
    )
    answers = models.JSONField(
        default=dict,
        help_text='Student answers keyed by subpart ID: {"42": 3, "43": "photosynthesis"}',
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When student clicked Submit. Null = still in progress.",
    )
    is_revised = models.BooleanField(
        default=False,
        help_text="Whether this is a revised attempt",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "submissions"
        unique_together = [["assignment", "student"]]
        indexes = [
            models.Index(fields=["student", "submitted_at"]),
        ]

    def __str__(self):
        return f"Submission: {self.student} → {self.assignment}"


class AssignmentSnapshotHistory(models.Model):
    """
    AIV-6: one row per superseded snapshot for an assignment.

    Re-sync ("Update this assignment to the latest content") replaces
    ``Assignment.assigned_content`` with a fresh snapshot of the live
    ``ProblemSet``. We record the *prior* snapshot here before swapping so the
    action is reversible — Undo restores the most recent history row.

    Sorted by ``replaced_at`` descending. The newest row is the "undo target";
    older rows are kept for audit. Nothing reads from history except the undo
    path; grading and rendering always go through ``Assignment.assigned_content``.
    """

    assignment = models.ForeignKey(
        "Assignment",
        on_delete=models.CASCADE,
        related_name="snapshot_history",
    )
    content = models.JSONField(help_text="The snapshot that was replaced (immutable).")
    replaced_at = models.DateTimeField(auto_now_add=True)
    replaced_by = models.ForeignKey(
        "User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignment_resyncs",
        help_text="Teacher who triggered the re-sync that displaced this snapshot.",
    )

    class Meta:
        db_table = "assignment_snapshot_history"
        ordering = ["-replaced_at"]
        indexes = [
            models.Index(fields=["assignment", "-replaced_at"]),
        ]

    def __str__(self):
        return f"Snapshot history for assignment {self.assignment_id} @ {self.replaced_at:%Y-%m-%d %H:%M}"


class AssignmentReminder(models.Model):
    """
    Log of due-date reminder emails sent for an assignment to a student.

    Exists purely for idempotency: the periodic reminder task creates one row per
    (assignment, student) before sending, so re-runs never email the same student
    twice for the same assignment.
    """

    assignment = models.ForeignKey(
        "Assignment",
        on_delete=models.CASCADE,
        related_name="reminders",
    )
    student = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="assignment_reminders",
        limit_choices_to={"role__in": [UserRole.STUDENT, UserRole.OPEN_STUDENT]},
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assignment_reminders"
        unique_together = [["assignment", "student"]]
        indexes = [
            models.Index(fields=["assignment", "student"]),
        ]

    def __str__(self):
        return f"Reminder: {self.assignment_id} → {self.student_id}"


class ClassroomInviteCode(models.Model):
    """
    A short join code generated by a teacher for their classroom.
    Students use it at registration to enroll automatically.
    """

    classroom = models.ForeignKey(
        "ClassRoom",
        on_delete=models.CASCADE,
        related_name="invite_codes",
    )
    code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        help_text="6-character uppercase alphanumeric code (e.g. 'ABC123')",
    )
    created_by = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="created_invite_codes",
        limit_choices_to={"role": UserRole.TEACHER},
    )
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "classroom_invite_codes"

    def __str__(self):
        return f"{self.code} → {self.classroom}"

    @classmethod
    def generate_code(cls) -> str:
        """Generate a unique 6-char uppercase alphanumeric code."""
        import secrets

        while True:
            candidate = secrets.token_urlsafe(5).upper().replace("-", "").replace("_", "")[:6]
            if len(candidate) == 6 and not cls.objects.filter(code=candidate).exists():
                return candidate


class StudentStreak(models.Model):
    """
    Daily activity streak for a student.

    One row per student — updated in-place by record_activity().
    Incremented when a student submits an assignment (via post_save signal).
    """

    student = models.OneToOneField(
        "User",
        on_delete=models.CASCADE,
        related_name="streak",
        limit_choices_to={"role__in": ["student", "open_student"]},
    )
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    streak_grace_used = models.BooleanField(
        default=False,
        help_text="True if the student has already used their grace day for the current streak run.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_streaks"

    def __str__(self):
        return f"Streak({self.student_id}): {self.current_streak}d"

    @property
    def milestone_tier(self) -> str:
        """Returns current milestone tier based on current_streak."""
        if self.current_streak >= 60:
            return "champion"
        elif self.current_streak >= 30:
            return "month"
        elif self.current_streak >= 7:
            return "week"
        elif self.current_streak >= 3:
            return "starter"
        return "none"

    def record_activity(self, activity_date):
        """
        Record activity for a given date and update streak counters.

        Rules:
        - Same day as last_activity_date → no-op
        - Next consecutive day → current_streak += 1, grace resets
        - Gap of exactly 1 day with grace available → streak continues (grace consumed)
        - Gap of 2+ days, or grace already used → current_streak resets to 1
        """
        from datetime import timedelta

        if self.last_activity_date is None:
            self.current_streak = 1
            self.streak_grace_used = False
        elif activity_date == self.last_activity_date:
            return
        elif activity_date == self.last_activity_date + timedelta(days=1):
            self.current_streak += 1
            self.streak_grace_used = False
        elif activity_date == self.last_activity_date + timedelta(days=2) and not self.streak_grace_used:
            # Missed exactly one day and grace is available — pause, don't break
            self.current_streak += 1
            self.streak_grace_used = True
        else:
            self.current_streak = 1
            self.streak_grace_used = False

        self.last_activity_date = activity_date
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.save(
            update_fields=[
                "current_streak",
                "longest_streak",
                "last_activity_date",
                "streak_grace_used",
                "updated_at",
            ]
        )


# ─────────────────────────────────────────────────────────────────────────────
# Interactive Widgets Framework — Tier 2 (Widget Studio) data model
# ─────────────────────────────────────────────────────────────────────────────


class TeacherWidgetVisibility(models.TextChoices):
    """Where a teacher-composed widget surfaces in the gallery (IW-9).

    Default ``personal`` keeps a draft author-only; ``school`` shares with the
    teacher's school once they're happy with it; ``pending_review`` is the
    queue state the Studio uses when an admin opt-in is required to cross
    schools (cross-school sharing itself ships later, gated on this state).
    """

    PERSONAL = "personal", "Personal"
    SCHOOL = "school", "School"
    PENDING_REVIEW = "pending_review", "Pending review"


class TeacherWidget(models.Model):
    """A teacher-composed Tier-2 widget (the **Widget Studio** output).

    Model-only slice of IW-9 — DRF endpoints, the serializer, and the scene
    schema validator land in IW-9 proper (after IW-1 + IW-2). Shipping the
    table now is a cheap, low-risk migration that unblocks the Studio later
    without adding a schema change to that PR's diff.

    ``scene`` is the pure-data Studio composition: a list of primitive
    instances + bindings + simple formula expressions. The runtime
    *interprets* the scene inside the same sandbox every other widget uses —
    no ``eval``, no ``Function``, no script string evaluation. ``scene_version``
    lets a future Studio runtime migrate older scenes without breaking
    content.
    """

    name = models.CharField(max_length=200, help_text="Display name of the widget in the teacher gallery.")
    description = models.TextField(
        blank=True, default="", help_text="Optional one-paragraph blurb for the gallery card."
    )
    school = models.ForeignKey(
        "School",
        on_delete=models.CASCADE,
        related_name="teacher_widgets",
        null=True,
        blank=True,
        help_text="Owning school (null for personal widgets authored by an open / unaffiliated teacher).",
    )
    created_by = models.ForeignKey(
        "User",
        on_delete=models.PROTECT,
        related_name="teacher_widgets_authored",
        limit_choices_to={"role": UserRole.TEACHER},
        help_text="Teacher who composed this widget.",
    )
    visibility = models.CharField(
        max_length=20,
        choices=TeacherWidgetVisibility.choices,
        default=TeacherWidgetVisibility.PERSONAL,
        help_text="Gallery visibility — see TeacherWidgetVisibility for the state machine.",
    )
    scene_version = models.PositiveIntegerField(
        default=1,
        help_text=(
            "Scene-schema version this widget was authored against. A future Studio "
            "runtime uses this to migrate older scenes on read."
        ),
    )
    scene = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Pure-data Studio composition: {primitives: [...], bindings: [...], formulas: [...]}. "
            "Interpreted by the runtime — never eval'd."
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "teacher_widgets"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["school", "visibility"]),
            models.Index(fields=["created_by", "updated_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.visibility})"
