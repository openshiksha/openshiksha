"""
Core models for OpenShiksha

Modern implementation of core business models.
Will be populated based on legacy models with improvements.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

# Validator for fraction values (0.0 to 1.0)
FRACTION_VALIDATOR = [MinValueValidator(0.0), MaxValueValidator(1.0)]


# User Groups and Roles
class UserRole(models.TextChoices):
    """User role choices based on legacy Group model"""
    STUDENT = 'student', 'Student'
    TEACHER = 'teacher', 'Teacher'
    PARENT = 'parent', 'Parent'
    ADMIN = 'admin', 'School Admin'
    OPEN_STUDENT = 'open_student', 'Open Student'  # Legacy: students without school


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
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        help_text='The type of user account'
    )

    school = models.ForeignKey(
        'School',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text='The school this user belongs to (null for open students)'
    )

    # Student-specific fields
    grade = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text='Grade/Standard for students (1-12)'
    )

    # Parent-specific fields
    children = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='parents',
        help_text='Children managed by this parent'
    )

    # Additional profile fields
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        help_text='Contact phone number'
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text='Date of birth'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['role', 'school']),
            models.Index(fields=['email']),
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
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text='Name of the educational board (e.g., CBSE, ICSE)'
    )

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'boards'
        ordering = ['name']

    def __str__(self):
        return self.name


class School(models.Model):
    """
    School model
    Based on legacy School model
    """
    name = models.CharField(
        max_length=255,
        help_text='Full name of the school'
    )

    board = models.ForeignKey(
        Board,
        on_delete=models.PROTECT,
        related_name='schools',
        help_text='The educational board/curriculum this school follows'
    )

    # Contact information
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)

    # Features (from legacy SchoolProfile)
    focus_enabled = models.BooleanField(
        default=False,
        help_text='Whether the focus rooms feature is enabled'
    )

    sms_enabled = models.BooleanField(
        default=False,
        help_text='Whether SMS notifications are enabled'
    )

    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'schools'
        ordering = ['name']
        indexes = [
            models.Index(fields=['board', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.board.name})"


class Standard(models.Model):
    """
    Grade/Standard level (1-12)
    Based on legacy Standard model
    """
    number = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text='Grade number (1-12)'
    )

    description = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'standards'
        ordering = ['number']

    def __str__(self):
        return f"Standard {self.number}"


class Subject(models.Model):
    """
    Subject model (e.g., Mathematics, Science)
    Based on legacy Subject model
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text='Name of the subject'
    )

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subjects'
        ordering = ['name']

    def __str__(self):
        return self.name


class Chapter(models.Model):
    """
    Chapter/Topic model
    Based on legacy Chapter model
    """
    name = models.CharField(
        max_length=255,
        help_text='Name of the chapter/topic'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='chapters',
        help_text='The subject this chapter belongs to'
    )

    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='chapters',
        help_text='The grade/standard this chapter is for'
    )

    order = models.PositiveIntegerField(
        default=0,
        help_text='Display order within subject'
    )

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chapters'
        ordering = ['subject', 'standard', 'order']
        unique_together = [['subject', 'standard', 'name']]

    def __str__(self):
        return f"{self.subject.name} - Std {self.standard.number} - {self.name}"


class ClassRoom(models.Model):
    """
    Classroom model - a group of students in same grade/division
    Based on legacy ClassRoom model
    """
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='classrooms',
        help_text='The school this classroom belongs to'
    )

    standard = models.ForeignKey(
        Standard,
        on_delete=models.PROTECT,
        related_name='classrooms',
        help_text='The grade/standard of this classroom'
    )

    division = models.CharField(
        max_length=50,
        help_text='Division name (e.g., A, B, C)'
    )

    class_teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes_managed',
        limit_choices_to={'role': UserRole.TEACHER},
        help_text='The teacher managing this classroom'
    )

    students = models.ManyToManyField(
        User,
        related_name='classes_enrolled',
        limit_choices_to={'role__in': [UserRole.STUDENT, UserRole.OPEN_STUDENT]},
        blank=True,
        help_text='Students enrolled in this classroom'
    )

    academic_year = models.CharField(
        max_length=20,
        help_text='Academic year (e.g., 2024-25)'
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'classrooms'
        ordering = ['school', 'standard', 'division']
        unique_together = [['school', 'standard', 'division', 'academic_year']]
        indexes = [
            models.Index(fields=['school', 'academic_year', 'is_active']),
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
            ('concept', 'Concept'),
            ('skill', 'Skill'),
            ('difficulty', 'Difficulty'),
            ('special', 'Special'),
        ],
        default='concept',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'question_tags'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.tag_type})"


class QuestionType(models.TextChoices):
    MCQ = 'mcq', 'Multiple Choice'
    FILL_BLANK = 'fill_blank', 'Fill in the Blank'
    MATCHING = 'matching', 'Matching'
    MULTI_SELECT = 'multi_select', 'Multi Select'
    NUMERIC = 'numeric', 'Numeric Answer'


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
        'School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='questions',
        help_text='null = OpenShiksha shared question bank',
    )
    standard = models.ForeignKey(
        'Standard',
        on_delete=models.PROTECT,
        related_name='questions',
    )
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.PROTECT,
        related_name='questions',
    )
    chapter = models.ForeignKey(
        'Chapter',
        on_delete=models.PROTECT,
        related_name='questions',
    )
    tags = models.ManyToManyField(QuestionTag, blank=True, related_name='questions')
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MCQ,
    )
    difficulty = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Difficulty level: 1=easiest, 5=hardest',
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'questions'
        indexes = [
            models.Index(fields=['chapter', 'is_active']),
            models.Index(fields=['school', 'standard', 'subject']),
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
        related_name='subparts',
    )
    index = models.PositiveIntegerField(help_text='Order within question (0-indexed)')
    tags = models.ManyToManyField(QuestionTag, blank=True, related_name='subparts')
    correct_answer = models.JSONField(
        default=dict,
        help_text='Answer data: e.g. {"type": "mcq", "answer": 2} or {"type": "fill_blank", "answer": "42"}',
    )

    class Meta:
        db_table = 'question_subparts'
        ordering = ['index']
        unique_together = [['question', 'index']]

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
        'ClassRoom',
        on_delete=models.CASCADE,
        related_name='subject_rooms',
    )
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.PROTECT,
        related_name='subject_rooms',
    )
    teacher = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        related_name='subject_rooms_taught',
        limit_choices_to={'role': UserRole.TEACHER},
    )
    students = models.ManyToManyField(
        'User',
        related_name='subject_rooms_enrolled',
        blank=True,
        limit_choices_to={'role__in': [UserRole.STUDENT, UserRole.OPEN_STUDENT]},
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subject_rooms'
        unique_together = [['classroom', 'subject']]
        indexes = [
            models.Index(fields=['classroom', 'is_active']),
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
        'School',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='problem_sets',
        help_text='null = shared OpenShiksha problem set',
    )
    standard = models.ForeignKey(
        'Standard',
        on_delete=models.PROTECT,
        related_name='problem_sets',
    )
    subject = models.ForeignKey(
        'Subject',
        on_delete=models.PROTECT,
        related_name='problem_sets',
    )
    chapter = models.ForeignKey(
        'Chapter',
        on_delete=models.PROTECT,
        related_name='problem_sets',
    )
    questions = models.ManyToManyField(
        Question,
        related_name='problem_sets',
        blank=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    number = models.PositiveIntegerField(
        default=1,
        help_text='Series number within same chapter (disambiguates multiple problem sets per chapter)',
    )
    estimated_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Estimated completion time in minutes',
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='problem_sets_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'problem_sets'
        unique_together = [['school', 'standard', 'subject', 'chapter', 'number']]
        indexes = [
            models.Index(fields=['chapter', 'is_active']),
        ]

    def __str__(self):
        return f"{self.title} (Std {self.standard.number}, {self.subject.name}, Ch {self.chapter.name} #{self.number})"


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
        related_name='assignments',
    )
    problem_set = models.ForeignKey(
        ProblemSet,
        on_delete=models.PROTECT,
        related_name='assignments',
    )
    assigned_by = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        related_name='assignments_created',
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField()
    number = models.PositiveIntegerField(
        default=1,
        help_text='Disambiguates if same problem set is assigned twice to same room',
    )
    # Cached aggregates — updated after grading runs
    average_score = models.FloatField(
        null=True,
        blank=True,
        validators=FRACTION_VALIDATOR,
        help_text='Average submission score (0.0–1.0), cached after grading',
    )
    completion_rate = models.FloatField(
        null=True,
        blank=True,
        validators=FRACTION_VALIDATOR,
        help_text='Fraction of students who have submitted (0.0–1.0)',
    )

    class Meta:
        db_table = 'assignments'
        indexes = [
            models.Index(fields=['subject_room', 'due_at']),
            models.Index(fields=['assigned_at']),
        ]

    def __str__(self):
        return f"Assignment: {self.problem_set.title} → {self.subject_room} (due {self.due_at.date()})"


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
        related_name='submissions',
    )
    student = models.ForeignKey(
        'User',
        on_delete=models.PROTECT,
        related_name='submissions',
        limit_choices_to={'role__in': [UserRole.STUDENT, UserRole.OPEN_STUDENT]},
    )
    score = models.FloatField(
        null=True,
        blank=True,
        validators=FRACTION_VALIDATOR,
        help_text='Fraction of marks obtained (0.0–1.0). Null until graded.',
    )
    completion = models.FloatField(
        default=0.0,
        validators=FRACTION_VALIDATOR,
        help_text='Fraction of questions attempted (0.0–1.0)',
    )
    answers = models.JSONField(
        default=dict,
        help_text='Student answers keyed by subpart ID: {"42": 3, "43": "photosynthesis"}',
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When student clicked Submit. Null = still in progress.',
    )
    is_revised = models.BooleanField(
        default=False,
        help_text='Whether this is a revised attempt',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'submissions'
        unique_together = [['assignment', 'student']]
        indexes = [
            models.Index(fields=['student', 'submitted_at']),
        ]

    def __str__(self):
        return f"Submission: {self.student} → {self.assignment}"
