"""
Django admin configuration for Edge app
"""

from django.contrib import admin

from .models import StudentProficiency, SubjectRoomProficiency, SubjectRoomQuestionMistake, Tick


@admin.register(Tick)
class TickAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'question_subpart', 'subject_room', 'mark', 'is_acknowledged', 'created_at']
    list_filter = ['is_acknowledged', 'subject_room', 'created_at']
    search_fields = ['student__username', 'student__email']
    readonly_fields = ['created_at']
    raw_id_fields = ['student', 'question_subpart', 'submission', 'subject_room']


@admin.register(StudentProficiency)
class StudentProficiencyAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'question_tag', 'subject_room', 'rate', 'percentile', 'score', 'tick_count', 'updated_at']
    list_filter = ['subject_room', 'question_tag']
    search_fields = ['student__username', 'student__email']
    readonly_fields = ['updated_at']
    raw_id_fields = ['student', 'question_tag', 'subject_room']
    ordering = ['-score']


@admin.register(SubjectRoomProficiency)
class SubjectRoomProficiencyAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject_room', 'question_tag', 'rate', 'percentile', 'score', 'updated_at']
    list_filter = ['subject_room', 'question_tag']
    readonly_fields = ['updated_at']
    raw_id_fields = ['question_tag', 'subject_room']
    ordering = ['-score']


@admin.register(SubjectRoomQuestionMistake)
class SubjectRoomQuestionMistakeAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject_room', 'question', 'regression', 'updated_at']
    list_filter = ['subject_room']
    readonly_fields = ['updated_at']
    raw_id_fields = ['subject_room', 'question']
    ordering = ['-regression']
