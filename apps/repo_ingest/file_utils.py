# apps/repo_ingest/file_utils.py
import os
import shutil
from typing import List, Dict, Set

# Supported file extensions (from your desktop code)
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".jsx", ".tsx",
    ".go", ".rs", ".cpp", ".c", ".html", ".css", 
    ".scss", ".php", ".json", ".xml", ".vue", 
    ".h", ".hpp"
}

# Language mapping (from your desktop code)
LANGUAGES = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".html": "html",
    ".css": "css",
    ".scss": "css",
    ".php": "php",
    ".json": "json",
    ".xml": "xml",
    ".vue": "vue",
    ".h": "c",
    ".hpp": "cpp",
}

# Folders to ignore (from your desktop code)
IGNORE_FOLDERS = {
    ".git", "__pycache__", ".venv", "venv", "node_modules",
    "dist", "build", ".mypy_cache", ".idea", ".vscode",
    ".next", "coverage", ".pytest_cache", "target",
    "out", "bin", "obj", ".gradle", "vendor"
}

MAX_DEPTH = 2  # Maximum directory depth


def is_supported_file(file_path: str) -> bool:
    """Check if file has a supported extension"""
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_EXTENSIONS


def get_language(file_path: str) -> str:
    """Get programming language from file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    return LANGUAGES.get(ext, "text")


def should_ignore_folder(folder_name: str) -> bool:
    """Check if folder should be ignored"""
    return folder_name in IGNORE_FOLDERS or folder_name.startswith('.')


def get_depth(root: str, path: str) -> int:
    """Calculate depth of path relative to root"""
    return os.path.relpath(path, root).count(os.sep)


def scan_repository(repo_path: str) -> List[Dict]:
    """
    Scan repository and return list of supported code files
    
    Returns:
        List of dicts with file info: {
            'absolute_path': str,
            'relative_path': str,
            'extension': str,
            'language': str,
            'size': int
        }
    """
    code_files = []
    
    for subdir, dirs, files in os.walk(repo_path):
        # Check depth limit
        if get_depth(repo_path, subdir) > MAX_DEPTH:
            continue
        
        # Filter out ignored directories (in-place modification)
        dirs[:] = [d for d in dirs if not should_ignore_folder(d)]
        
        # Process files
        for file_name in files:
            file_path = os.path.join(subdir, file_name)
            
            if is_supported_file(file_path):
                rel_path = os.path.relpath(file_path, repo_path)
                ext = os.path.splitext(file_name)[1]
                
                code_files.append({
                    'absolute_path': file_path,
                    'relative_path': rel_path,
                    'file_name': file_name,
                    'extension': ext,
                    'language': get_language(file_path),
                    'size': os.path.getsize(file_path)
                })
    
    return code_files


def get_repository_stats(code_files: List[Dict]) -> Dict:
    """Get statistics about scanned repository"""
    stats = {
        'total_files': len(code_files),
        'total_size': sum(f['size'] for f in code_files),
        'by_language': {}
    }
    
    for file_info in code_files:
        lang = file_info['language']
        if lang not in stats['by_language']:
            stats['by_language'][lang] = 0
        stats['by_language'][lang] += 1
    
    return stats


def cleanup_temp_directory(path: str):
    """Safely delete temporary directory"""
    try:
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"✅ Cleaned up: {path}")
    except Exception as e:
        print(f"⚠️ Cleanup failed for {path}: {e}")


def read_file_content(file_path: str) -> str:
    """Read file content with encoding fallback"""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                return f.read()
        except Exception as e:
            continue
    
    return ""


def extract_project_context(repo_path: str) -> str:
    """Extract project context from README.md"""
    readme_files = ['README.md', 'readme.md', 'README.MD', 'ReadMe.md']
    
    for readme_name in readme_files:
        readme_path = os.path.join(repo_path, readme_name)
        if os.path.exists(readme_path):
            try:
                content = read_file_content(readme_path)
                if content:
                    # Return first 1000 characters
                    return content[:1000]
            except Exception as e:
                print(f"⚠️ Could not read {readme_name}: {e}")
                continue
    
    return "No project description available."

