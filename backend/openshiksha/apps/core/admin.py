"""
Django admin configuration for Core app
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Board, School, Standard, Subject, Chapter, ClassRoom
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model with role support
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'school', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'role', 'school']
    search_fields = ['username', 'first_name', 'last_name', 'email']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('role', 'school', 'grade', 'phone_number', 'date_of_birth')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Profile Information', {
            'fields': ('role', 'school', 'grade')
        }),
    )


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'board', 'city', 'is_active', 'focus_enabled', 'sms_enabled']
    list_filter = ['board', 'is_active', 'focus_enabled', 'sms_enabled', 'city']
    search_fields = ['name', 'city', 'email']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'board')
        }),
        ('Contact Details', {
            'fields': ('address', 'city', 'state', 'pincode', 'phone', 'email')
        }),
        ('Features', {
            'fields': ('focus_enabled', 'sms_enabled', 'is_active')
        }),
    )


@admin.register(Standard)
class StandardAdmin(admin.ModelAdmin):
    list_display = ['number', 'description']
    ordering = ['number']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'standard', 'order']
    list_filter = ['subject', 'standard']
    search_fields = ['name']
    ordering = ['subject', 'standard', 'order']


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['school', 'standard', 'division', 'class_teacher', 'academic_year', 'is_active']
    list_filter = ['school', 'standard', 'academic_year', 'is_active']
    search_fields = ['school__name', 'division']
    filter_horizontal = ['students']
