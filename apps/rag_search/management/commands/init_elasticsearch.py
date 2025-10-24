from django.core.management.base import BaseCommand
from apps.rag_search.es_client import test_connection
from apps.rag_search.es_ops import ElasticsearchManager

class Command(BaseCommand):
    help = 'Initialize Elasticsearch indices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Delete and recreate existing indices',
        )
        parser.add_argument(
            '--embedding-dim',
            type=int,
            default=768,
            help='Embedding vector dimensions (default: 768 for Gemini)',
        )

    def handle(self, *args, **options):
        self.stdout.write("Testing Elasticsearch connection...")
        if not test_connection():
            self.stdout.write(self.style.ERROR('Failed to connect to Elasticsearch'))
            return
        
        self.stdout.write(self.style.SUCCESS('✅ Connected to Elasticsearch'))
        
        manager = ElasticsearchManager()
        manager.create_indices(
            embedding_dim=options['embedding_dim'],
            force_recreate=options['recreate']
        )
        
        self.stdout.write(self.style.SUCCESS('✅ Elasticsearch initialization complete'))
 
