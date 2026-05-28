from django.contrib import admin

from .models import Enquirer


@admin.register(Enquirer)
class EnquirerAdmin(admin.ModelAdmin):
    list_display = ["name", "school", "email", "phone", "created_at"]
    search_fields = ["name", "school", "email"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at"]
