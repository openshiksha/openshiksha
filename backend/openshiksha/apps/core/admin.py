"""
Django admin configuration for Core app
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Assignment,
    Board,
    Chapter,
    ClassRoom,
    ProblemSet,
    Question,
    QuestionSubpart,
    QuestionTag,
    School,
    Standard,
    Subject,
    SubjectRoom,
    Submission,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model with role support
    """

    list_display = ["username", "email", "first_name", "last_name", "role", "school", "is_staff", "is_active"]
    list_filter = ["is_staff", "is_superuser", "is_active", "role", "school"]
    search_fields = ["username", "first_name", "last_name", "email"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Profile Information", {"fields": ("role", "school", "grade", "phone_number", "date_of_birth")}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (("Profile Information", {"fields": ("role", "school", "grade")}),)


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "board", "city", "is_active", "focus_enabled", "sms_enabled"]
    list_filter = ["board", "is_active", "focus_enabled", "sms_enabled", "city"]
    search_fields = ["name", "city", "email"]
    fieldsets = (
        ("Basic Information", {"fields": ("name", "board")}),
        ("Contact Details", {"fields": ("address", "city", "state", "pincode", "phone", "email")}),
        ("Features", {"fields": ("focus_enabled", "sms_enabled", "is_active")}),
    )


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ["number", "description"]
    ordering = ["number"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ["name", "subject", "standard", "order"]
    list_filter = ["subject", "standard"]
    search_fields = ["name"]
    ordering = ["subject", "standard", "order"]


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ["school", "standard", "division", "class_teacher", "academic_year", "is_active"]
    list_filter = ["school", "standard", "academic_year", "is_active"]
    search_fields = ["school__name", "division"]
    filter_horizontal = ["students"]


# ─────────────────────────────────────────────────────────────
# Question Bank Admin
# ─────────────────────────────────────────────────────────────


@admin.register(QuestionTag)
class QuestionTagAdmin(admin.ModelAdmin):
    list_display = ["name", "tag_type", "created_at"]
    list_filter = ["tag_type"]
    search_fields = ["name"]


class QuestionSubpartInline(admin.TabularInline):
    model = QuestionSubpart
    extra = 1
    fields = ["index", "correct_answer", "tags"]
    filter_horizontal = ["tags"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "question_type",
        "difficulty",
        "standard",
        "subject",
        "chapter",
        "school",
        "is_active",
        "created_at",
    ]
    list_filter = ["question_type", "difficulty", "is_active", "standard", "subject", "school"]
    search_fields = ["id", "chapter__name", "subject__name"]
    filter_horizontal = ["tags"]
    inlines = [QuestionSubpartInline]
    raw_id_fields = ["created_by"]
    fieldsets = (
        ("Classification", {"fields": ("standard", "subject", "chapter", "question_type", "difficulty", "tags")}),
        ("Ownership", {"fields": ("school", "created_by", "is_active")}),
    )


@admin.register(SubjectRoom)
class SubjectRoomAdmin(admin.ModelAdmin):
    list_display = ["classroom", "subject", "teacher", "is_active", "created_at"]
    list_filter = ["subject", "is_active", "classroom__school"]
    search_fields = ["classroom__school__name", "subject__name", "teacher__username"]
    filter_horizontal = ["students"]
    raw_id_fields = ["teacher"]


# ─────────────────────────────────────────────────────────────
# Assignment Pipeline Admin
# ─────────────────────────────────────────────────────────────


@admin.register(ProblemSet)
class ProblemSetAdmin(admin.ModelAdmin):
    list_display = ["title", "standard", "subject", "chapter", "number", "school", "is_active", "created_at"]
    list_filter = ["is_active", "standard", "subject", "school"]
    search_fields = ["title", "chapter__name", "subject__name"]
    filter_horizontal = ["questions"]
    raw_id_fields = ["created_by"]
    fieldsets = (
        ("Content", {"fields": ("title", "description", "standard", "subject", "chapter", "number", "questions")}),
        ("Metadata", {"fields": ("school", "estimated_minutes", "created_by", "is_active")}),
    )


class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0
    fields = ["student", "score", "completion", "submitted_at", "is_revised"]
    readonly_fields = ["score", "completion", "submitted_at", "created_at"]
    raw_id_fields = ["student"]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "problem_set",
        "subject_room",
        "assigned_by",
        "assigned_at",
        "due_at",
        "average_score",
        "completion_rate",
    ]
    list_filter = ["subject_room__subject", "subject_room__classroom__school"]
    search_fields = ["problem_set__title", "subject_room__classroom__school__name"]
    raw_id_fields = ["assigned_by"]
    readonly_fields = ["assigned_at", "average_score", "completion_rate"]
    inlines = [SubmissionInline]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["id", "student", "assignment", "score", "completion", "submitted_at", "is_revised"]
    list_filter = ["is_revised", "assignment__subject_room__subject"]
    search_fields = ["student__username", "student__first_name", "student__last_name"]
    raw_id_fields = ["student", "assignment"]
    readonly_fields = ["created_at", "updated_at"]
