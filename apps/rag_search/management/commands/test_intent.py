from django.core.management.base import BaseCommand
from apps.rag_search.rag_pipeline import RAGPipeline

class Command(BaseCommand):
    help = 'Test AI-powered intent detection'

    def handle(self, *args, **options):
        self.stdout.write("Testing AI Intent Detection...\n")
        
        rag = RAGPipeline()
        
        test_queries = [
            "How does the login function work?",
            "What are all the functions in this project?",
            "Give me an overview of the architecture",
            "Explain the UserModel class",
            "List all API endpoints",
            "How many classes are there?",
            "Show me the database schema",
            "What files contain authentication logic?",
        ]
        
        for query in test_queries:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Query: {query}")
            self.stdout.write('='*60)
            
            intent = rag._detect_query_intent_ai(query)
            
            self.stdout.write(f"Type:       {intent['type']}")
            self.stdout.write(f"Top-K:      {intent['top_k']}")
            self.stdout.write(f"Confidence: {intent['confidence']:.2f}")
            self.stdout.write(f"Reasoning:  {intent['reasoning']}")
        
        self.stdout.write(self.style.SUCCESS('\n✅ Intent detection test complete!'))

