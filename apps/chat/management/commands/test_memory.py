# apps/chat/management/commands/test_memory.py
from django.core.management.base import BaseCommand
from apps.chat.memory_manager import ChatMemoryManager
from apps.chat.models import ChatSession, ChatMessage
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Test chat memory system'
    
    def handle(self, *args, **options):
        # Get first user and session
        user = User.objects.first()
        session = ChatSession.objects.filter(user=user).first()
        
        if not session:
            self.stdout.write("No chat sessions found")
            return
        
        self.stdout.write(f"Testing memory for session: {session.id}")
        
        # Get stats
        memory_manager = ChatMemoryManager()
        stats = memory_manager.get_memory_stats(user.id)
        
        self.stdout.write(f"Total memories: {stats.get('total_memories', 0)}")
        self.stdout.write(f"Trigger count: {stats.get('trigger_count', 5)}")
        
        # Count messages
        message_count = ChatMessage.objects.filter(session=session).count()
        self.stdout.write(f"Messages in session: {message_count}")
        
        # Force check
        self.stdout.write("\nForce checking for summarization...")
        memory_manager.check_and_summarize(session.id, user.id)
        
        self.stdout.write(self.style.SUCCESS('✅ Memory test complete!'))

