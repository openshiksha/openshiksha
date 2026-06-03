from django.contrib import admin

from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["subject_room", "author", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["message", "author__username", "subject_room__subject__name"]
    readonly_fields = ["created_at"]
