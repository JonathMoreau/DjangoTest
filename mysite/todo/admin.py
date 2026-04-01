from django.contrib import admin

from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "is_done", "created_at")
    list_filter = ("is_done", "owner")
    search_fields = ("title", "owner__username", "owner__email")
