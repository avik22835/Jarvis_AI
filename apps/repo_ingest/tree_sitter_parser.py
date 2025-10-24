# apps/repo_ingest/tree_sitter_parser.py
"""
Tree-sitter based code parser - Direct port from your desktop chunker.py
"""
from tree_sitter_language_pack import get_parser
from typing import List, Dict, Optional
import os


# Node types for chunking (from your desktop code)
METHOD_NODES = {
    "function_definition",     # Python, C
    "function_declaration",    # JS, Go
    "method_definition",       # JS, Rust
    "method_declaration",      # Java, Go
    "arrow_function",          # JS/TS
    "function_item",           # Rust
    "defn", "defnDef",         # Scala
    "generator_function_declaration",
    "function_expression",
    "constructor_declaration"
}

CLASS_NODES = {
    "class_definition",        # Python
    "class_declaration",       # Java, JS/TS, PHP
    "class_specifier",         # C++
    "struct_item", "impl_item", "enum_item",  # Rust
    "interface_declaration",   # TypeScript
    "trait_item",
    "namespace_definition"
}

SPECIAL_CHUNK_TYPES = {
    "jsx_element",
    "jsx_fragment",
    "element",
    "start_tag",
    "script_element",
    "style_element",
    "rule_set",
    "at_rule",
    "style_rule",
    "media_rule"
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

# Initialize parsers for each language
PARSERS = {}
for ext, lang in LANGUAGES.items():
    try:
        PARSERS[ext] = get_parser(lang)
    except Exception as e:
        print(f"⚠️ Could not load parser for {lang} ({ext}): {e}")


class TreeSitterParser:
    """Parse code files and extract function/class chunks"""
    
    def __init__(self, project_context: str = ""):
        self.project_context = project_context
    
    def parse_file(self, file_path: str, content: str) -> List[Dict]:
        """
        Parse a single file and extract code chunks
        
        Returns:
            List of chunks: [{
                'file_path': str,
                'file_name': str,
                'language': str,
                'chunk_type': str,
                'chunk_name': str,
                'code': str,
                'start_line': int,
                'end_line': int,
                'class_name': str (optional)
            }]
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext not in PARSERS:
            return []
        
        try:
            parser = PARSERS[ext]
            tree = parser.parse(bytes(content, "utf-8"))
            root = tree.root_node
            
            chunks = []
            file_name = os.path.basename(file_path)
            language = LANGUAGES.get(ext, "text")
            
            for node in root.children:
                # Top-level functions/methods
                if node.type in METHOD_NODES:
                    chunk = self._make_chunk(
                        node, file_path, file_name, language, content
                    )
                    chunks.append(chunk)
                
                # Class-like structures
                elif node.type in CLASS_NODES:
                    class_name = self._get_node_name(node)
                    has_methods = False
                    
                    # Extract methods from class
                    for child in node.named_children:
                        if child.type in METHOD_NODES:
                            has_methods = True
                            chunk = self._make_chunk(
                                child, file_path, file_name, language, content
                            )
                            chunk['class_name'] = class_name
                            chunks.append(chunk)
                    
                    # If class has no methods, store entire class
                    if not has_methods and node.end_byte - node.start_byte > 5:
                        chunk = self._make_chunk(
                            node, file_path, file_name, language, content
                        )
                        chunk['chunk_type'] = 'class'
                        chunks.append(chunk)
                
                # Special chunks (JSX, CSS rules, etc.)
                elif node.type in SPECIAL_CHUNK_TYPES:
                    chunk = self._make_chunk(
                        node, file_path, file_name, language, content
                    )
                    chunk['chunk_type'] = 'special'
                    chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"❌ Error parsing {file_path}: {e}")
            return []
    
    def _make_chunk(
        self, 
        node, 
        file_path: str, 
        file_name: str, 
        language: str,
        full_content: str
    ) -> Dict:
        """Create a chunk dictionary from a tree-sitter node"""
        chunk_name = self._get_node_name(node)
        code = node.text.decode('utf-8', errors='ignore')
        
        return {
            'file_path': file_path,
            'file_name': file_name,
            'language': language,
            'chunk_type': node.type,
            'chunk_name': chunk_name,
            'code': code,
            'start_line': node.start_point[0] + 1,
            'end_line': node.end_point[0] + 1,
        }
    
    def _get_node_name(self, node) -> str:
        """Extract name from a tree-sitter node"""
        name_node = node.child_by_field_name("name")
        if name_node:
            return name_node.text.decode('utf-8', errors='ignore')
        return "anonymous"


def parse_repository(repo_path: str, file_list: List[Dict], project_context: str = "") -> List[Dict]:
    """
    Parse all files in repository and extract chunks
    
    Args:
        repo_path: Root path of repository
        file_list: List of file dicts from scan_repository()
        project_context: README or user description
    
    Returns:
        List of all chunks across all files
    """
    parser = TreeSitterParser(project_context=project_context)
    all_chunks = []
    
    for file_info in file_list:
        file_path = file_info['absolute_path']
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse and extract chunks
            chunks = parser.parse_file(file_path, content)
            all_chunks.extend(chunks)
            
            if chunks:
                print(f"✅ Parsed {len(chunks)} chunks from {file_info['file_name']}")
        
        except Exception as e:
            print(f"❌ Failed to parse {file_path}: {e}")
            continue
    
    return all_chunks

