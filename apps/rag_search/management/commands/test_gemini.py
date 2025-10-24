from django.core.management.base import BaseCommand
from apps.rag_search.gemini_client import test_gemini_connection
from apps.rag_search.embeddings import EmbeddingService
from apps.rag_search.generation import GenerationService

class Command(BaseCommand):
    help = 'Test Gemini API integration'

    def handle(self, *args, **options):
        self.stdout.write("Testing Gemini API connection...")
        
        # Test basic connection
        if not test_gemini_connection():
            self.stdout.write(self.style.ERROR('Connection failed'))
            return
        
        # Test embeddings
        self.stdout.write("\nTesting embeddings...")
        embed_service = EmbeddingService()
        
        test_text = "def hello_world():\n    print('Hello, World!')"
        embedding = embed_service.embed_text(test_text)
        
        self.stdout.write(f"✅ Generated embedding: {len(embedding)} dimensions")
        self.stdout.write(f"   Sample values: {embedding[:5]}")
        
        # Test generation
        self.stdout.write("\nTesting generation...")
        gen_service = GenerationService()
        
        answer = gen_service.generate_simple("Explain what a Python function is in one sentence.")
        self.stdout.write(f"✅ Generated response: {answer[:100]}...")
        
        self.stdout.write(self.style.SUCCESS('\n✅ All Gemini API tests passed!'))

