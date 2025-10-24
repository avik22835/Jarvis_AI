# apps/repo_ingest/sync_views.py
"""
GitHub Smart Sync - Incremental updates
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Repository, CodeChunk
from .github_utils import GitHubHandler
from .tree_sitter_parser import TreeSitterParser
from .chunk_summarizer import ChunkSummarizer
from .chunk_embedder import ChunkEmbedder
from .file_utils import is_supported_file, get_language, read_file_content
from apps.rag_search.es_ops import ElasticsearchManager
import threading
import os


@login_required
@require_http_methods(["POST"])
def repository_sync(request, repo_id):
    """
    Sync GitHub repository - detect changes and update only changed files
    """
    repository = get_object_or_404(Repository, id=repo_id, user=request.user)
    
    # Check if repository is from GitHub
    if repository.upload_type != 'github' or not repository.github_url:
        return JsonResponse({'error': 'Repository is not from GitHub'}, status=400)
    
    # Check if not already syncing
    if repository.status == 'processing':
        return JsonResponse({'error': 'Repository is already being processed'}, status=400)
    
    # Start sync in background
    syncer = GitHubSyncer(repository)
    thread = threading.Thread(target=syncer.sync)
    thread.daemon = True
    thread.start()
    
    return JsonResponse({
        'success': True,
        'message': 'Sync started'
    })


class GitHubSyncer:
    """Handle GitHub smart sync operations"""
    
    def __init__(self, repository: Repository):
        self.repository = repository
        self.github_handler = GitHubHandler(
            repository.github_url,
            repository.github_branch
        )
        self.es_manager = ElasticsearchManager()
        self.temp_dir = None
    
    def sync(self):
        """Main sync method"""
        try:
            self.repository.update_progress('processing', 'Checking for changes', 5)
            
            # Get current commit SHA
            new_commit_sha = self.github_handler.get_latest_commit_sha()
            
            if not new_commit_sha:
                raise Exception("Could not fetch latest commit from GitHub")
            
            # Check if anything changed
            old_commit_sha = self.repository.last_commit_sha
            
            if old_commit_sha == new_commit_sha:
                self.repository.update_progress(
                    'completed', 
                    'No changes detected', 
                    100
                )
                return
            
            print(f"🔄 Syncing from {old_commit_sha[:7]} to {new_commit_sha[:7]}")
            
            # Get list of changed files
            if old_commit_sha:
                changed_files = self.github_handler.get_changed_files(
                    old_commit_sha, 
                    new_commit_sha
                )
            else:
                # First sync - treat everything as changed
                changed_files = self._get_all_files()
            
            print(f"📝 Found {len(changed_files)} changed files")
            
            # Filter to only supported files
            supported_changed = [
                f for f in changed_files 
                if is_supported_file(f['filename'])
            ]
            
            print(f"✅ Processing {len(supported_changed)} supported files")
            
            if len(supported_changed) == 0:
                self.repository.last_commit_sha = new_commit_sha
                self.repository.update_progress('completed', 'No code changes', 100)
                return
            
            # Process each changed file
            self._process_changed_files(supported_changed)
            
            # Update commit SHA
            self.repository.last_commit_sha = new_commit_sha
            self.repository.update_progress('completed', 'Sync complete', 100)
            
            print(f"✅ Sync complete!")
            
        except Exception as e:
            print(f"❌ Sync failed: {e}")
            self.repository.mark_as_failed(e)


    def _update_repository_stats(self):
        """Update repository file and chunk counts"""
        from apps.repo_ingest.models import CodeChunk
    
        # Count total unique files
        unique_files = CodeChunk.objects.filter(
        repository=self.repository
        ).values('file_path').distinct().count()
    
        # Count total chunks
        total_chunks = CodeChunk.objects.filter(
        repository=self.repository
        ).count()
    
        # Update repository
        self.repository.total_files = unique_files
        self.repository.total_chunks = total_chunks
        self.repository.save()        
        print(f"📊 Updated stats: {unique_files} files, {total_chunks} chunks")
        
    def _process_changed_files(self, changed_files: list):
        """Process each changed file"""
        total = len(changed_files)
        
        for i, file_info in enumerate(changed_files, 1):
            filename = file_info['filename']
            status = file_info['status']
            
            progress = 10 + (i * 80 // total)
            self.repository.update_progress(
                'processing',
                f'Processing {filename} ({i}/{total})',
                progress
            )
            
            try:
                if status == 'removed':
                    # Delete chunks for removed file
                    self._delete_file_chunks(filename)
                    print(f"❌ Deleted chunks for {filename}")
                
                elif status in ['added', 'modified']:
                    # Re-process file
                    self._reprocess_file(filename)
                    print(f"✅ Updated chunks for {filename}")
                
            except Exception as e:
                print(f"⚠️ Failed to process {filename}: {e}")
                continue

        # ✅ ADD THIS: Update repository stats after sync
        self._update_repository_stats()

    def _delete_file_chunks(self, file_path: str):
        """Delete all chunks for a file from both ES and Django"""
        # Delete from Elasticsearch
        try:
            self.es_manager.client.delete_by_query(
                index="jarvis_repo_chunks",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"user_id": self.repository.user.id}},
                                {"term": {"repo_id": str(self.repository.id)}},
                                {"term": {"file_path.keyword": file_path}}
                            ]
                        }
                    }
                }
            )
        except Exception as e:
            print(f"⚠️ ES delete failed: {e}")
        
        # Delete from Django
        CodeChunk.objects.filter(
            repository=self.repository,
            file_path=file_path
        ).delete()
    
    def _reprocess_file(self, file_path: str):
        """Re-parse, re-embed, and re-index a single file"""
        # Step 1: Delete old chunks
        self._delete_file_chunks(file_path)
        
        # Step 2: Download file content
        self.temp_dir = f"/tmp/jarvis_sync_{self.repository.id}"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        local_file_path = os.path.join(self.temp_dir, os.path.basename(file_path))
        
        success = self.github_handler.download_single_file(file_path, local_file_path)
        
        if not success:
            print(f"⚠️ Could not download {file_path}")
            return
        
        # Step 3: Parse with Tree-sitter
        content = read_file_content(local_file_path)
        
        parser = TreeSitterParser(self.repository.project_context)
        chunks = parser.parse_file(file_path, content)
        
        if not chunks:
            print(f"⚠️ No chunks extracted from {file_path}")
            return
        
        # Step 4: Generate summaries
        summarizer = ChunkSummarizer()
        for chunk in chunks:
            chunk['summary'] = summarizer.summarize_chunk(
                chunk, 
                self.repository.project_context
            )
        
        # Step 5: Embed and index
        embedder = ChunkEmbedder()
        embedder.embed_and_index_chunks(
            chunks,
            str(self.repository.id),
            self.repository.name,
            self.repository.user.id
        )
        
        # Step 6: Save to Django
        chunk_objects = []
        for chunk in chunks:
            chunk_obj = CodeChunk(
                repository=self.repository,
                file_path=chunk['file_path'],
                file_name=chunk['file_name'],
                language=chunk['language'],
                chunk_type=chunk['chunk_type'],
                chunk_name=chunk['chunk_name'],
                code=chunk['code'],
                summary=chunk['summary'],
                start_line=chunk['start_line'],
                end_line=chunk['end_line']
            )
            chunk_objects.append(chunk_obj)
        
        CodeChunk.objects.bulk_create(chunk_objects)
        
        # Cleanup
        if os.path.exists(local_file_path):
            os.remove(local_file_path)
    
    def _get_all_files(self):
        """Get all files in repository (for first sync)"""
        # This is a simplified version - in production you'd use GitHub Tree API
        return []

