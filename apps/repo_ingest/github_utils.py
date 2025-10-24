# apps/repo_ingest/github_utils.py
"""
GitHub repository operations - clone, sync, change detection
"""
import requests
import os
import zipfile
import tempfile
import shutil
from typing import Dict, List, Optional
from urllib.parse import urlparse


class GitHubHandler:
    """Handle GitHub repository operations"""
    
    def __init__(self, github_url: str, branch: str = "main"):
        self.github_url = github_url
        self.branch = branch
        self.owner, self.repo = self._parse_github_url(github_url)
    
    def _parse_github_url(self, url: str) -> tuple:
        """
        Parse GitHub URL to extract owner and repo
        Examples:
            https://github.com/owner/repo
            https://github.com/owner/repo.git
        """
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1].replace('.git', '')
            return owner, repo
        
        raise ValueError(f"Invalid GitHub URL: {url}")
    
    def get_default_branch(self) -> str:
        """Get default branch name from GitHub API"""
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('default_branch', 'main')
        except Exception as e:
            print(f"⚠️ Could not fetch default branch: {e}")
            return 'main'
    
    def get_latest_commit_sha(self, branch: Optional[str] = None) -> Optional[str]:
        """Get latest commit SHA for a branch"""
        branch = branch or self.branch
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits/{branch}"
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data['sha']
        except Exception as e:
            print(f"❌ Failed to get commit SHA: {e}")
            return None
    
    def download_as_zip(self, target_dir: str) -> str:
        """
        Download repository as ZIP and extract
        
        Args:
            target_dir: Directory to extract ZIP contents
        
        Returns:
            Path to extracted directory
        """
        # GitHub ZIP download URL
        zip_url = f"https://github.com/{self.owner}/{self.repo}/archive/refs/heads/{self.branch}.zip"
        
        print(f"📥 Downloading {self.owner}/{self.repo} from GitHub...")
        
        try:
            # Download ZIP file
            response = requests.get(zip_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_zip_path = tmp_file.name
            
            print(f"✅ Downloaded ZIP ({os.path.getsize(tmp_zip_path) / 1024 / 1024:.2f} MB)")
            
            # Extract ZIP
            with zipfile.ZipFile(tmp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(target_dir)
            
            os.remove(tmp_zip_path)
            
            # GitHub ZIP creates a subdirectory: repo-branch/
            # Find the extracted directory
            extracted_items = os.listdir(target_dir)
            if len(extracted_items) == 1 and os.path.isdir(os.path.join(target_dir, extracted_items[0])):
                extracted_path = os.path.join(target_dir, extracted_items[0])
            else:
                extracted_path = target_dir
            
            print(f"✅ Extracted to: {extracted_path}")
            return extracted_path
            
        except Exception as e:
            print(f"❌ Failed to download from GitHub: {e}")
            raise
    
    def get_changed_files(self, base_commit: str, head_commit: str) -> List[Dict]:
        """
        Get list of changed files between two commits
        
        Args:
            base_commit: Base commit SHA
            head_commit: Head commit SHA
        
        Returns:
            List of changed files with status: [{
                'filename': str,
                'status': 'added' | 'modified' | 'removed',
                'changes': int
            }]
        """
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/compare/{base_commit}...{head_commit}"
        
        try:
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            changed_files = []
            for file_data in data.get('files', []):
                changed_files.append({
                    'filename': file_data['filename'],
                    'status': file_data['status'],
                    'changes': file_data.get('changes', 0),
                    'additions': file_data.get('additions', 0),
                    'deletions': file_data.get('deletions', 0)
                })
            
            return changed_files
            
        except Exception as e:
            print(f"❌ Failed to get changed files: {e}")
            return []
    
    def download_single_file(self, file_path: str, target_path: str) -> bool:
        """
        Download a single file from repository
        
        Args:
            file_path: Path within repository
            target_path: Local path to save file
        
        Returns:
            True if successful
        """
        api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{file_path}?ref={self.branch}"
        
        try:
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Decode base64 content
            import base64
            content = base64.b64decode(data['content'])
            
            # Save to file
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'wb') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to download {file_path}: {e}")
            return False


def clone_github_repo(github_url: str, target_dir: str, branch: str = "main") -> tuple:
    """
    Clone GitHub repository to target directory
    
    Returns:
        (extracted_path, commit_sha)
    """
    handler = GitHubHandler(github_url, branch)
    
    # Get latest commit SHA
    commit_sha = handler.get_latest_commit_sha()
    
    # Download and extract
    extracted_path = handler.download_as_zip(target_dir)
    
    return extracted_path, commit_sha

