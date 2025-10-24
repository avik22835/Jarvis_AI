import google.generativeai as genai
import os
from typing import List
import time

# Initialize Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class EmbeddingService:
    """Generate embeddings using Gemini API"""
    
    def __init__(self, model_name="text-embedding-004"):
        """
        Initialize embedding service
        
        Args:
            model_name: Gemini embedding model
                - text-embedding-004 (768 dims, stable)
                - gemini-embedding-001 (768 dims, deprecated soon)
        """
        self.model_name = model_name
        self.embedding_dim = 768  # text-embedding-004 outputs 768 dimensions
    
    def embed_text(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            task_type: Task type for embedding
                - RETRIEVAL_DOCUMENT: For indexing documents (code chunks)
                - RETRIEVAL_QUERY: For search queries
                - SEMANTIC_SIMILARITY: For similarity comparison
        
        Returns:
            List of floats (768 dimensions)
        """
        try:
            result = genai.embed_content(
                model=f"models/{self.model_name}",
                content=text,
                task_type=task_type
            )
            return result['embedding']
        except Exception as e:
            print(f"❌ Embedding error: {str(e)}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dim
    
    def embed_batch(
        self, 
        texts: List[str], 
        task_type: str = "RETRIEVAL_DOCUMENT",
        batch_size: int = 100,
        delay: float = 0.1
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (with rate limiting)
        
        Args:
            texts: List of texts to embed
            task_type: Task type for embedding
            batch_size: Number of texts per batch
            delay: Delay between batches (seconds)
        
        Returns:
            List of embeddings
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            try:
                # Gemini API supports batch embedding
                result = genai.embed_content(
                    model=f"models/{self.model_name}",
                    content=batch,
                    task_type=task_type
                )
                
                # Extract embeddings from batch result
                if isinstance(result['embedding'][0], list):
                    embeddings.extend(result['embedding'])
                else:
                    embeddings.append(result['embedding'])
                
                # Rate limiting: Free tier = 1500 requests/day
                time.sleep(delay)
                
            except Exception as e:
                print(f"❌ Batch {i//batch_size} error: {str(e)}")
                # Add zero vectors for failed batch
                embeddings.extend([[0.0] * self.embedding_dim] * len(batch))
        
        return embeddings
    
    def embed_code_chunk(self, code: str, file_path: str, language: str) -> List[float]:
        """
        Generate embedding for a code chunk with metadata
        
        Args:
            code: Code content
            file_path: Path to the file
            language: Programming language
        
        Returns:
            Embedding vector
        """
        # Add context to improve embeddings
        text = f"File: {file_path}\nLanguage: {language}\n\n{code}"
        return self.embed_text(text, task_type="RETRIEVAL_DOCUMENT")
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query
        
        Args:
            query: Search query text
        
        Returns:
            Embedding vector
        """
        return self.embed_text(query, task_type="RETRIEVAL_QUERY")
 
