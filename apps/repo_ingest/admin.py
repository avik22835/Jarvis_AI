# Register your models here.
from django.contrib import admin
from .models import Repository, CodeChunk


@admin.register(Repository)
class RepositoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'upload_type', 'status', 'total_chunks', 'created_at']
    list_filter = ['status', 'upload_type', 'created_at']
    search_fields = ['name', 'user__username', 'github_url']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(CodeChunk)
class CodeChunkAdmin(admin.ModelAdmin):
    list_display = ['chunk_name', 'file_name', 'language', 'chunk_type', 'repository']
    list_filter = ['language', 'chunk_type']
    search_fields = ['chunk_name', 'file_name', 'code']
    readonly_fields = ['id', 'created_at']
