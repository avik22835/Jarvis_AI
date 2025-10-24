# apps/repo_ingest/processing.py
"""
Main processing orchestrator - handles complete ingestion pipeline
"""
from .models import Repository, CodeChunk
from .file_utils import (
    scan_repository, 
    extract_project_context,
    cleanup_temp_directory,
    get_repository_stats
)
from .tree_sitter_parser import parse_repository
from .chunk_summarizer import add_summaries_to_chunks
from .chunk_embedder import ChunkEmbedder
from .github_utils import clone_github_repo
import os
import shutil
import zipfile
from django.utils import timezone


class RepositoryProcessor:
    """Process repository ingestion from start to finish"""
    
    def __init__(self, repository: Repository):
        self.repository = repository
        self.temp_dir = None
        self.extracted_path = None
    
    def process_zip_upload(self, zip_file_path: str):
        """
        Process uploaded ZIP file
        
        Args:
            zip_file_path: Path to uploaded ZIP file
        """
        try:
            # Create temp directory
            self.temp_dir = f"/tmp/jarvis_repo_{self.repository.id}"
            os.makedirs(self.temp_dir, exist_ok=True)
            
            self.repository.update_progress('processing', 'Extracting ZIP file', 5)
            
            # Extract ZIP
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            
            # Find extracted directory
            items = os.listdir(self.temp_dir)
            if len(items) == 1 and os.path.isdir(os.path.join(self.temp_dir, items[0])):
                self.extracted_path = os.path.join(self.temp_dir, items[0])
            else:
                self.extracted_path = self.temp_dir
            
            self.repository.local_path = self.extracted_path
            self.repository.save()
            
            # Continue with processing
            self._process_repository()

            self._generate_prompts()
            
        except Exception as e:
            self.repository.mark_as_failed(e)
            raise
        finally:
            self._cleanup()
    
    def process_github_url(self, github_url: str, branch: str = "main"):
        """
        Process GitHub repository URL
        
        Args:
            github_url: GitHub repository URL
            branch: Branch name to clone
        """
        try:
            # Create temp directory
            self.temp_dir = f"/tmp/jarvis_repo_{self.repository.id}"
            os.makedirs(self.temp_dir, exist_ok=True)
            
            self.repository.update_progress('processing', 'Downloading from GitHub', 5)
            
            # Clone repository
            self.extracted_path, commit_sha = clone_github_repo(
                github_url, 
                self.temp_dir,
                branch
            )
            
            # Save GitHub info
            self.repository.github_url = github_url
            self.repository.github_branch = branch
            self.repository.last_commit_sha = commit_sha
            self.repository.local_path = self.extracted_path
            self.repository.save()
            
            # Continue with processing
            self._process_repository()
            
            self._generate_prompts()

        except Exception as e:
            self.repository.mark_as_failed(e)
            raise
        finally:
            self._cleanup()
    
    def _process_repository(self):
        """Main processing pipeline"""
        try:
            # Step 1: Extract project context
            self.repository.update_progress('processing', 'Reading project context', 10)
            project_context = extract_project_context(self.extracted_path)
            self.repository.project_context = project_context
            self.repository.save()
            
            # Step 2: Scan for code files
            self.repository.update_progress('processing', 'Scanning code files', 20)
            code_files = scan_repository(self.extracted_path)
            stats = get_repository_stats(code_files)
            
            self.repository.total_files = stats['total_files']
            self.repository.save()
            
            print(f"📊 Found {len(code_files)} code files")
            print(f"   Languages: {stats['by_language']}")
            
            if len(code_files) == 0:
                raise ValueError("No supported code files found in repository")
            
            # Step 3: Parse with Tree-sitter
            self.repository.update_progress('parsing', 'Parsing code with Tree-sitter', 30)
            chunks = parse_repository(self.extracted_path, code_files, project_context)
            
            print(f"🔍 Extracted {len(chunks)} code chunks")
            
            if len(chunks) == 0:
                raise ValueError("No code chunks extracted from repository")
            
            self.repository.total_chunks = len(chunks)
            self.repository.save()
            
            # Step 4: Generate summaries
            self.repository.update_progress('embedding', 'Generating summaries', 50)
            chunks = add_summaries_to_chunks(chunks, project_context)
            
            # Step 5: Generate embeddings and index
            self.repository.update_progress('indexing', 'Indexing to Elasticsearch', 70)
            embedder = ChunkEmbedder()
            success_count, failed_count = embedder.embed_and_index_chunks(
                chunks=chunks,
                repository_id=str(self.repository.id),
                repository_name=self.repository.name,
                user_id=self.repository.user.id
            )
            
            # Step 6: Save chunks to database
            self.repository.update_progress('indexing', 'Saving to database', 90)
            self._save_chunks_to_db(chunks)
            
            # Mark as completed
            self.repository.update_progress('completed', 'Processing complete', 100)
            self.repository.last_synced_at = timezone.now()
            self.repository.save()
            
            print(f"✅ Repository processing complete!")
            print(f"   Total chunks: {len(chunks)}")
            print(f"   Indexed: {success_count}, Failed: {failed_count}")
            
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            self.repository.mark_as_failed(e)
            raise
    
    def _save_chunks_to_db(self, chunks: list):
        """Save chunks to Django database"""
        chunk_objects = []
        
        for chunk in chunks:
            chunk_obj = CodeChunk(
                repository=self.repository,
                file_path=chunk.get('file_path', ''),
                file_name=chunk.get('file_name', ''),
                language=chunk.get('language', 'text'),
                chunk_type=chunk.get('chunk_type', 'function'),
                chunk_name=chunk.get('chunk_name', 'anonymous'),
                code=chunk.get('code', ''),
                summary=chunk.get('summary', ''),
                start_line=chunk.get('start_line', 0),
                end_line=chunk.get('end_line', 0)
            )
            chunk_objects.append(chunk_obj)
        
        # Bulk create
        CodeChunk.objects.bulk_create(chunk_objects, batch_size=500)
        print(f"✅ Saved {len(chunk_objects)} chunks to database")
    
    def _cleanup(self):
        """Cleanup temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            cleanup_temp_directory(self.temp_dir)


    def _generate_prompts(self):
        """Generate suggested prompts for the repository"""
        try:
            from .prompt_generator import PromptGenerator
            
            print(f"🎯 Generating suggested prompts...")
            generator = PromptGenerator()
            prompts = generator.generate_prompts(self.repository)
            
            self.repository.suggested_prompts = prompts
            self.repository.save()
            
            print(f"✅ Saved {len(prompts)} suggested prompts")
        except Exception as e:
            print(f"⚠️ Prompt generation failed (non-fatal): {e}")
            import traceback
            traceback.print_exc()
