from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.chat.models import ChatSession, ChatMessage
from apps.rag_search.rag_pipeline import RAGPipeline

class Command(BaseCommand):
    help = 'Test full RAG pipeline with code retrieval'

    def handle(self, *args, **options):
        self.stdout.write("Testing FULL RAG Pipeline...")
        
        user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR('No user found. Create one first.'))
            return
        
        # Create session
        session = ChatSession.objects.create(
            user=user,
            title="Full RAG Test"
        )
        
        # Initialize RAG
        rag = RAGPipeline()
        
        # Test query that would search for code
        question = "Show me how authentication works in this project"
        
        self.stdout.write(f"\n📥 Question: {question}\n")
        
        try:
            answer = rag.process_query(
                question=question,
                user_id=user.id,
                session_id=session.id
            )
            
            self.stdout.write(f"\n📤 Answer:\n{answer}\n")
            self.stdout.write(self.style.SUCCESS('✅ Full RAG test passed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Test failed: {str(e)}'))
            import traceback
            traceback.print_exc()

