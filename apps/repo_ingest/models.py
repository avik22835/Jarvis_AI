# Create your models here.
# apps/repo_ingest/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Repository(models.Model):
    """Repository uploaded by user"""
    
    UPLOAD_TYPE_CHOICES = [
        ('zip', 'ZIP File'),
        ('github', 'GitHub URL'),
    ]
    
    STATUS_CHOICES = [
        ('uploading', 'Uploading'),
        ('processing', 'Processing'),
        ('parsing', 'Parsing Code'),
        ('embedding', 'Generating Embeddings'),
        ('indexing', 'Indexing to Elasticsearch'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='repositories')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Upload type
    upload_type = models.CharField(max_length=20, choices=UPLOAD_TYPE_CHOICES)
    github_url = models.URLField(blank=True, null=True)
    github_branch = models.CharField(max_length=100, default='main', blank=True)
    zip_file = models.FileField(upload_to='uploads/', blank=True)
    last_commit_sha = models.CharField(max_length=40, blank=True, null=True)  # For smart sync
    
    # Storage
    storage_path = models.CharField(max_length=500, blank=True)  # Cloud Storage path
    local_path = models.CharField(max_length=500, blank=True)  # Temp /tmp/ path
    
    # Processing status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading')
    current_step = models.CharField(max_length=200, blank=True)
    progress_percentage = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    # Statistics
    total_files = models.IntegerField(default=0)
    total_chunks = models.IntegerField(default=0)
    total_lines = models.IntegerField(default=0)
    
    # Project context
    project_context = models.TextField(blank=True)  # README or user input
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    
    suggested_prompts = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Repositories'
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    def mark_as_failed(self, error):
        """Mark repository as failed with error message"""
        self.status = 'failed'
        self.error_message = str(error)
        self.save()
    
    def update_progress(self, status, step, percentage):
        """Update processing progress"""
        self.status = status
        self.current_step = step
        self.progress_percentage = percentage
        self.updated_at = timezone.now()
        self.save()


class CodeChunk(models.Model):
    """Individual code chunk from repository"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE, related_name='chunks')
    
    # File info
    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=200)
    language = models.CharField(max_length=50)
    
    # Chunk info
    chunk_type = models.CharField(max_length=50)  # function, class, method, etc.
    chunk_name = models.CharField(max_length=200)
    code = models.TextField()
    summary = models.TextField()
    
    # Position in file
    start_line = models.IntegerField()
    end_line = models.IntegerField()
    
    # Elasticsearch ID
    es_doc_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['file_path', 'start_line']
    
    def __str__(self):
        return f"{self.chunk_name} ({self.file_name})"
