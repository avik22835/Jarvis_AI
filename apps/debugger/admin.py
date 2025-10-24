# Register your models here.
# apps/debugger/admin.py
from django.contrib import admin
from .models import DebugSession, DebugQuery


@admin.register(DebugSession)
class DebugSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'created_at', 'updated_at']
    list_filter = ['created_at', 'user']
    search_fields = ['title', 'user__username']


@admin.register(DebugQuery)
class DebugQueryAdmin(admin.ModelAdmin):
    list_display = ['error_type', 'user', 'has_image', 'created_at']
    list_filter = ['has_image', 'created_at', 'error_type']
    search_fields = ['query_text', 'error_message']
