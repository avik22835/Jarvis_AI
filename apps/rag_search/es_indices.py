# Index mappings for Elasticsearch

REPO_CHUNKS_INDEX = "jarvis_repo_chunks"
CHAT_MEMORY_INDEX = "jarvis_chat_memory"
EXTERNAL_SOURCES_INDEX = "jarvis_external_sources"

def get_repo_chunks_mapping(embedding_dim=768):
    """
    Mapping for code repository chunks
    Stores: code chunks, embeddings, metadata
    """
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,  # No replicas for development
            "analysis": {
                "analyzer": {
                    "code_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stop"]
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "user_id": {"type": "integer"},
                "repo_id": {"type": "keyword"},
                "repo_name": {"type": "text"},
                "file_path": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "chunk_id": {"type": "integer"},
                "content": {
                    "type": "text",
                    "analyzer": "code_analyzer",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
                },
                "language": {"type": "keyword"},
                "node_type": {"type": "keyword"},  # function, class, etc.
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": embedding_dim,
                    "index": True,
                    "similarity": "cosine"
                },
                "keywords": {"type": "keyword"},  # For BM25 hybrid search
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"}
            }
        }
    }

def get_chat_memory_mapping(embedding_dim=768):
    """
    Mapping for chat memory summaries
    Stores: chat summaries from Google Drive, embeddings
    """
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "user_id": {"type": "integer"},
                "session_id": {"type": "keyword"},
                "summary": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": embedding_dim,
                    "index": True,
                    "similarity": "cosine"
                },
                "drive_file_id": {"type": "keyword"},  # Google Drive file ID
                "message_count": {"type": "integer"},
                "created_at": {"type": "date"},
                "timestamp": {"type": "date"}
            }
        }
    }

def get_external_sources_mapping(embedding_dim=768):
    """
    Mapping for external debugging sources
    Stores: StackOverflow, GitHub Issues snippets, embeddings
    """
    return {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "source": {"type": "keyword"},  # stackoverflow, github, etc.
                "url": {"type": "keyword"},
                "title": {"type": "text"},
                "snippet": {"type": "text"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": embedding_dim,
                    "index": True,
                    "similarity": "cosine"
                },
                "keywords": {"type": "keyword"},
                "score": {"type": "float"},  # Original source score/votes
                "created_at": {"type": "date"}
            }
        }
    }
 
