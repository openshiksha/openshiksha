from django.contrib import admin

from .models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ["title", "chapter", "order", "is_active", "created_at"]
    list_filter = ["is_active", "chapter__subject", "created_at"]
    search_fields = ["title", "description", "chapter__name"]
    list_editable = ["order", "is_active"]
    readonly_fields = ["created_at"]
