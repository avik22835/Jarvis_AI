# apps/repo_ingest/chunk_embedder.py
"""
Generate embeddings and index to Elasticsearch
"""
from apps.rag_search.embeddings import EmbeddingService
from apps.rag_search.es_ops import ElasticsearchManager
from typing import List, Dict
from datetime import datetime
import uuid


class ChunkEmbedder:
    """Generate embeddings and index chunks to Elasticsearch"""
    
    def __init__(self):
        self.embed_service = EmbeddingService()
        self.es_manager = ElasticsearchManager()
    
    def embed_and_index_chunks(
        self,
        chunks: List[Dict],
        repository_id: str,
        repository_name: str,
        user_id: int
    ) -> tuple:
        """
        Generate embeddings and index all chunks to Elasticsearch
        
        Args:
            chunks: List of chunk dicts with 'code', 'summary', etc.
            repository_id: UUID of repository
            repository_name: Name of repository
            user_id: User ID
        
        Returns:
            (success_count, failed_count)
        """
        print(f"🔢 Generating embeddings for {len(chunks)} chunks...")
        
        # Prepare documents for indexing
        documents = []
        
        for i, chunk in enumerate(chunks, 1):
            try:
                # Generate embedding
                embedding_text = self._prepare_embedding_text(chunk)
                embedding = self.embed_service.embed_text(
                    embedding_text, 
                    task_type="RETRIEVAL_DOCUMENT"
                )
                
                # Create Elasticsearch document
                doc_id = f"{repository_id}_{uuid.uuid4().hex[:8]}"
                
                doc = {
                    "id": doc_id,
                    "user_id": user_id,
                    "repo_id": str(repository_id),
                    "repo_name": repository_name,
                    "file_path": chunk.get('file_path', ''),
                    "chunk_id": i,
                    "content": chunk.get('code', ''),
                    "language": chunk.get('language', 'text'),
                    "node_type": chunk.get('chunk_type', 'function'),
                    "start_line": chunk.get('start_line', 0),
                    "end_line": chunk.get('end_line', 0),
                    "embedding": embedding,
                    "keywords": [chunk.get('chunk_name', ''), chunk.get('file_name', '')],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                # Add optional fields
                if 'class_name' in chunk:
                    doc['class_name'] = chunk['class_name']
                
                if 'summary' in chunk:
                    doc['summary'] = chunk['summary']
                
                documents.append(doc)
                
                # Progress indicator
                if i % 50 == 0 or i == len(chunks):
                    print(f"   Embedded: {i}/{len(chunks)} chunks ({i*100//len(chunks)}%)")
            
            except Exception as e:
                print(f"⚠️ Failed to embed chunk {i}: {e}")
                continue
        
        # Bulk index to Elasticsearch
        print(f"📊 Indexing {len(documents)} documents to Elasticsearch...")
        
        try:
            success, failed = self.es_manager.bulk_index(
                index_name="jarvis_repo_chunks",
                documents=documents
            )
            
            print(f"✅ Indexed {success} chunks, {len(failed)} failed")
            return success, len(failed)
            
        except Exception as e:
            print(f"❌ Elasticsearch indexing failed: {e}")
            return 0, len(documents)
    
    def _prepare_embedding_text(self, chunk: Dict) -> str:
        """Prepare text for embedding (code + filename + summary)"""
        parts = []
        
        # Add file info
        if 'file_name' in chunk:
            parts.append(f"File: {chunk['file_name']}")
        
        # Add chunk name
        if 'chunk_name' in chunk:
            parts.append(f"Function: {chunk['chunk_name']}")
        
        # Add summary if available
        if 'summary' in chunk:
            parts.append(f"Summary: {chunk['summary']}")
        
        # Add code
        if 'code' in chunk:
            parts.append(f"Code:\n{chunk['code']}")
        
        return "\n".join(parts)

