"""
Core models for OpenShiksha

Modern implementation of core business models.
Will be populated based on legacy models with improvements.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator


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


# TODO: Additional models to implement in next tasks:
# - Question, QuestionTag, QuestionSubpart
# - Assignment, Submission
# - SubjectRoom (subject-specific grouping within classroom)
# - Announcement
# - Proficiency (analytics)
