from .es_client import get_es_client
from .es_indices import (
    REPO_CHUNKS_INDEX,
    CHAT_MEMORY_INDEX,
    EXTERNAL_SOURCES_INDEX,
    get_repo_chunks_mapping,
    get_chat_memory_mapping,
    get_external_sources_mapping
)
from elasticsearch.helpers import bulk
from datetime import datetime

class ElasticsearchManager:
    def __init__(self):
        self.client = get_es_client()
    
    def create_indices(self, embedding_dim=768, force_recreate=False):
        """Create all required indices"""
        indices = {
            REPO_CHUNKS_INDEX: get_repo_chunks_mapping(embedding_dim),
            CHAT_MEMORY_INDEX: get_chat_memory_mapping(embedding_dim),
            EXTERNAL_SOURCES_INDEX: get_external_sources_mapping(embedding_dim)
        }
        
        for index_name, mapping in indices.items():
            try:
                if self.client.indices.exists(index=index_name):
                    if force_recreate:
                        print(f"🗑️  Deleting existing index: {index_name}")
                        self.client.indices.delete(index=index_name)
                    else:
                        print(f"✅ Index already exists: {index_name}")
                        continue
                
                self.client.indices.create(index=index_name, body=mapping)
                print(f"✅ Created index: {index_name}")
            except Exception as e:
                print(f"❌ Error creating index {index_name}: {str(e)}")
    
    def index_document(self, index_name, doc_id, document):
        """Index a single document"""
        try:
            self.client.index(index=index_name, id=doc_id, body=document)
            return True
        except Exception as e:
            print(f"❌ Error indexing document: {str(e)}")
            return False
    
    def bulk_index(self, index_name, documents):
        """Bulk index multiple documents"""
        actions = [
            {
                "_index": index_name,
                "_id": doc.get("id"),
                "_source": doc
            }
            for doc in documents
        ]
        
        try:
            success, failed = bulk(self.client, actions, raise_on_error=False)
            print(f"✅ Indexed {success} documents, {len(failed)} failed")
            return success, failed
        except Exception as e:
            print(f"❌ Bulk indexing error: {str(e)}")
            return 0, len(documents)
    
    def hybrid_search(self, index_name, query_text, query_vector, user_id=None, top_k=5):
        """
        Hybrid search: combine vector similarity + keyword (BM25)
        """
        must_clauses = []
        
        # Add user filter if provided
        if user_id is not None:
            must_clauses.append({"term": {"user_id": user_id}})
        
        search_body = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": must_clauses,
                    "should": [
                        # Vector similarity search
                        {
                            "script_score": {
                                "query": {"match_all": {}},
                                "script": {
                                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                    "params": {"query_vector": query_vector}
                                }
                            }
                        },
                        # BM25 keyword search
                        {
                            "multi_match": {
                                "query": query_text,
                                "fields": ["content^2", "file_path", "keywords"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "_source": True
        }
        
        try:
            response = self.client.search(index=index_name, body=search_body)
            return [
                {
                    "score": hit["_score"],
                    "source": hit["_source"]
                }
                for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            return []
    
    def delete_user_data(self, user_id):
        """Delete all data for a specific user"""
        indices = [REPO_CHUNKS_INDEX, CHAT_MEMORY_INDEX]
        
        for index in indices:
            try:
                self.client.delete_by_query(
                    index=index,
                    body={"query": {"term": {"user_id": user_id}}}
                )
                print(f"✅ Deleted user {user_id} data from {index}")
            except Exception as e:
                print(f"❌ Error deleting user data from {index}: {str(e)}")
 
