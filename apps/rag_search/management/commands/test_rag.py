from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.chat.models import ChatSession, ChatMessage
from apps.rag_search.rag_pipeline import RAGPipeline

class Command(BaseCommand):
    help = 'Test RAG pipeline'

    def handle(self, *args, **options):
        self.stdout.write("Testing RAG Pipeline...")
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write("✅ Created test user")
        
        # Create test session
        session = ChatSession.objects.create(
            user=user,
            title="RAG Test Session"
        )
        self.stdout.write(f"✅ Created session: {session.id}")
        
        # Add a user message
        ChatMessage.objects.create(
            session=session,
            user=user,
            role='user',
            content='What is Python?'
        )
        
        # Initialize RAG pipeline
        rag = RAGPipeline()
        
        # Test simple query (no code context yet)
        self.stdout.write("\n" + "="*60)
        self.stdout.write("Testing simple query...")
        self.stdout.write("="*60 + "\n")
        
        question = "Can you explain what Python is used for?"
        
        try:
            answer = rag.process_query_simple(
                question=question,
                user_id=user.id,
                session_id=session.id
            )
            
            self.stdout.write(f"\n📥 Question: {question}")
            self.stdout.write(f"\n📤 Answer:\n{answer}\n")
            
            # Save messages
            ChatMessage.objects.create(
                session=session,
                user=user,
                role='user',
                content=question
            )
            
            ChatMessage.objects.create(
                session=session,
                user=user,
                role='assistant',
                content=answer
            )
            
            self.stdout.write(self.style.SUCCESS('\n✅ RAG pipeline test passed!'))
            self.stdout.write(f"Session ID: {session.id}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Test failed: {str(e)}'))

