# apps/repo_ingest/chunk_summarizer.py
"""
Summarize code chunks using Gemini API
"""
import google.generativeai as genai
import os
from typing import List, Dict
import time


genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class ChunkSummarizer:
    """Generate summaries for code chunks using Gemini"""
    
    def __init__(self, model_name="gemini-2.0-flash-exp"):
        self.model = genai.GenerativeModel(model_name)
        self.request_count = 0
        self.rate_limit_delay = 0.1  # 100ms between requests
    
    def summarize_chunk(self, chunk: Dict, project_context: str = "") -> str:
        """
        Generate summary for a single code chunk
        
        Args:
            chunk: Chunk dictionary with 'code', 'chunk_name', etc.
            project_context: Optional project description from README
        
        Returns:
            Summary string (max 20 words)
        """
        prompt = self._build_summary_prompt(chunk, project_context)
        
        try:
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            
            self.request_count += 1
            
            # Keep summary concise
            if len(summary) > 150:
                summary = summary[:147] + "..."
            
            return summary
            
        except Exception as e:
            print(f"⚠️ Summary failed for {chunk.get('chunk_name', 'unknown')}: {e}")
            # Fallback to simple description
            return f"{chunk.get('chunk_name', 'Code')} in {chunk.get('file_name', 'file')}"
    
    def summarize_chunks_batch(
        self, 
        chunks: List[Dict], 
        project_context: str = "",
        batch_size: int = 50
    ) -> List[Dict]:
        """
        Summarize multiple chunks with progress tracking
        
        Args:
            chunks: List of chunk dictionaries
            project_context: Project description
            batch_size: Print progress every N chunks
        
        Returns:
            Same chunks list with 'summary' field added
        """
        total = len(chunks)
        print(f"📝 Summarizing {total} chunks...")
        
        for i, chunk in enumerate(chunks, 1):
            summary = self.summarize_chunk(chunk, project_context)
            chunk['summary'] = summary
            
            # Progress indicator
            if i % batch_size == 0 or i == total:
                print(f"   Progress: {i}/{total} chunks summarized ({i*100//total}%)")
        
        print(f"✅ Summarization complete! ({self.request_count} API calls)")
        return chunks
    
    def _build_summary_prompt(self, chunk: Dict, project_context: str) -> str:
        """Build prompt for Gemini summarization"""
        code = chunk.get('code', '')
        chunk_name = chunk.get('chunk_name', 'Code')
        file_name = chunk.get('file_name', '')
        
        prompt = f"""You are analyzing a codebase.

PROJECT CONTEXT:
{project_context if project_context else "No project description available."}

CODE CHUNK:
File: {file_name}
Function/Class: {chunk_name}

{code}

TASK:
Summarize in 15-20 words what this code does, mentioning the function/class name and its purpose in the project context.

Summary:"""
        
        return prompt


def add_summaries_to_chunks(
    chunks: List[Dict], 
    project_context: str = ""
) -> List[Dict]:
    """
    Convenience function to add summaries to all chunks
    
    Args:
        chunks: List of chunk dictionaries
        project_context: README or user description
    
    Returns:
        Chunks with 'summary' field added
    """
    summarizer = ChunkSummarizer()
    return summarizer.summarize_chunks_batch(chunks, project_context)

