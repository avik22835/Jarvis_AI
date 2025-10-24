# Create your models here.
# apps/debugger/models.py
from django.db import models
from django.contrib.auth.models import User
import uuid


class DebugSession(models.Model):
    """Track debug sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='debug_sessions')
    title = models.CharField(max_length=200, default="Debug Session")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"


class DebugQuery(models.Model):
    """Individual debug queries"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(DebugSession, on_delete=models.CASCADE, related_name='queries')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Query input
    query_text = models.TextField()
    has_image = models.BooleanField(default=False)
    image_path = models.CharField(max_length=500, blank=True)
    
    # Extracted error info
    error_type = models.CharField(max_length=200, blank=True)
    error_message = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True)
    
    # Response
    response = models.TextField()
    
    # Sources used
    stackoverflow_results = models.JSONField(default=list)
    web_results = models.JSONField(default=list)
    code_results = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Debug Query: {self.error_type or 'Unknown'}"
