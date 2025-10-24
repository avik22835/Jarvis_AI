from elasticsearch import Elasticsearch
from django.conf import settings
import os

def get_es_client():
    """Get configured Elasticsearch client (compatible with ES 8.x)"""
    es_url = os.getenv('ES_URL', 'http://34.131.86.211:9200/')
    es_username = os.getenv('ES_USERNAME', None)

    es_password = os.getenv('ES_PASSWORD', None)
    
    # Create client with or without authentication
    if es_username and es_password:
        client = Elasticsearch(
            [es_url],
            basic_auth=(es_username, es_password),  # Changed from http_auth
            verify_certs=False,
            request_timeout=30,  # Changed from timeout
            max_retries=3,
            retry_on_timeout=True
        )
    else:
        client = Elasticsearch(
            [es_url],
            verify_certs=False,
            request_timeout=30,  # Changed from timeout
            max_retries=3,
            retry_on_timeout=True
        )
    
    return client

def test_connection():
    """Test Elasticsearch connection"""
    try:
        client = get_es_client()
        info = client.info()
        print(f"✅ Connected to Elasticsearch: {info['version']['number']}")
        print(f"   Cluster: {info['cluster_name']}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Elasticsearch: {str(e)}")
        return False
