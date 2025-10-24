# Create your views here.
# apps/repo_ingest/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Repository
from .processing import RepositoryProcessor
from .sync_views import repository_sync
import threading
import os


@login_required
def repository_list(request):
    """List user's repositories"""
    repositories = Repository.objects.filter(user=request.user)
    return render(request, 'repo_ingest/repository_list.html', {
        'repositories': repositories
    })


@login_required
def repository_upload_page(request):
    """Upload repository page"""
    return render(request, 'repo_ingest/upload_repository.html')


@login_required
@require_http_methods(["POST"])
def repository_upload(request):
    """Handle repository upload (ZIP or GitHub URL)"""
    try:
        upload_type = request.POST.get('upload_type', 'zip')
        repo_name = request.POST.get('repo_name', '').strip()
        repo_description = request.POST.get('repo_description', '').strip()
        
        if not repo_name:
            return JsonResponse({'error': 'Repository name is required'}, status=400)
        
        # Create repository object
        repository = Repository.objects.create(
            user=request.user,
            name=repo_name,
            description=repo_description,
            upload_type=upload_type,
            status='uploading'
        )
        
        if upload_type == 'zip':
            # Handle ZIP upload
            if 'zip_file' not in request.FILES:
                repository.delete()
                return JsonResponse({'error': 'No ZIP file provided'}, status=400)
            
            zip_file = request.FILES['zip_file']
            
            # Save to temporary location
            file_path = f"/tmp/upload_{repository.id}.zip"
            with open(file_path, 'wb+') as destination:
                for chunk in zip_file.chunks():
                    destination.write(chunk)
            
            # Process in background thread
            processor = RepositoryProcessor(repository)
            thread = threading.Thread(
                target=processor.process_zip_upload,
                args=(file_path,)
            )
            thread.daemon = True
            thread.start()
            
        elif upload_type == 'github':
            # Handle GitHub URL
            github_url = request.POST.get('github_url', '').strip()
            github_branch = request.POST.get('github_branch', 'main').strip()
            
            if not github_url:
                repository.delete()
                return JsonResponse({'error': 'GitHub URL is required'}, status=400)
            
            repository.github_url = github_url
            repository.github_branch = github_branch
            repository.save()
            
            # Process in background thread
            processor = RepositoryProcessor(repository)
            thread = threading.Thread(
                target=processor.process_github_url,
                args=(github_url, github_branch)
            )
            thread.daemon = True
            thread.start()
        
        else:
            repository.delete()
            return JsonResponse({'error': 'Invalid upload type'}, status=400)
        
        return JsonResponse({
            'success': True,
            'repository_id': str(repository.id),
            'redirect_url': f'/repo/{repository.id}/status/'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def repository_status(request, repo_id):
    """Show repository processing status"""
    repository = get_object_or_404(Repository, id=repo_id, user=request.user)
    return render(request, 'repo_ingest/repository_status.html', {
        'repository': repository
    })


@login_required
def repository_status_api(request, repo_id):
    """API endpoint for polling repository status"""
    repository = get_object_or_404(Repository, id=repo_id, user=request.user)
    
    return JsonResponse({
        'status': repository.status,
        'current_step': repository.current_step,
        'progress_percentage': repository.progress_percentage,
        'error_message': repository.error_message,
        'total_files': repository.total_files,
        'total_chunks': repository.total_chunks,
        'suggested_prompts': repository.suggested_prompts 
    })


@login_required
@require_http_methods(["POST"])
def repository_delete(request, repo_id):
    """Delete repository"""
    repository = get_object_or_404(Repository, id=repo_id, user=request.user)
    repository.delete()
    return JsonResponse({'success': True})
