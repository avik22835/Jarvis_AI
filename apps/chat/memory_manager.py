# apps/chat/memory_manager.py
"""
ENHANCED Chat Memory Manager - Full timestamp tracking + metadata
"""
import google.generativeai as genai
import os
from datetime import datetime
from apps.rag_search.embeddings import EmbeddingService
from apps.rag_search.es_ops import ElasticsearchManager
from .models import ChatSession, ChatMessage
import uuid


genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class ChatMemoryManager:
    """
    Enhanced memory manager with:
    - Individual Q&A timestamps
    - Per-question summaries (max 20 words)
    - Searchable question previews
    - Session metadata
    - Batch tracking
    """
    
    def __init__(self):
        self.trigger_count = 5  # Summarize every 5 Q&As
        self.embed_service = EmbeddingService()
        self.es_manager = ElasticsearchManager()
        self.summarizer = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def check_and_summarize(self, session_id: int, user_id: int):
        """
        Check if session needs summarization
        Triggers every 5 Q&A pairs
        """
        try:
            # Count total messages in session
            total_messages = ChatMessage.objects.filter(session_id=session_id).count()
            
            # Each Q&A pair = 2 messages
            qa_pairs = total_messages // 2
            
            # Check if we just hit a multiple of 5
            if qa_pairs > 0 and qa_pairs % self.trigger_count == 0:
                print(f"🎯 Summarization trigger: {qa_pairs} Q&A pairs reached")
                
                # Get last 5 Q&A pairs (10 messages)
                last_messages = ChatMessage.objects.filter(
                    session_id=session_id
                ).order_by('-created_at')[:10]
                
                # Reverse to chronological order
                last_messages = list(reversed(last_messages))
                
                # Get session info
                session = ChatSession.objects.get(id=session_id)
                
                # Group into Q&A pairs with full metadata
                qa_list = []
                for i in range(0, len(last_messages), 2):
                    if i + 1 < len(last_messages):
                        user_msg = last_messages[i]
                        assistant_msg = last_messages[i + 1]
                        
                        qa_list.append({
                            'question': user_msg.content,
                            'answer': assistant_msg.content,
                            'question_timestamp': user_msg.created_at.isoformat(),
                            'answer_timestamp': assistant_msg.created_at.isoformat(),
                            'user_message_id': user_msg.id,
                            'assistant_message_id': assistant_msg.id
                        })
                
                # Summarize with full metadata
                self._summarize_and_index(
                    session_id=session_id,
                    session_title=session.title,
                    user_id=user_id,
                    qa_list=qa_list,
                    batch_number=qa_pairs // self.trigger_count
                )
                
        except Exception as e:
            print(f"❌ Memory summarization failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _summarize_and_index(
        self, 
        session_id: int, 
        session_title: str,
        user_id: int, 
        qa_list: list,
        batch_number: int
    ):
        """
        ENHANCED: Summarize with full metadata tracking
        """
        try:
            print(f"📝 Summarizing {len(qa_list)} Q&A pairs (Batch #{batch_number})...")
            
            # Generate individual summaries with timestamps
            individual_summaries = []
            combined_text_parts = []
            
            for i, qa in enumerate(qa_list, 1):
                # Generate concise summary (max 20 words)
                summary = self._generate_summary(qa['question'], qa['answer'])
                
                # Store individual summary with ALL metadata
                individual_summaries.append({
                    'qa_number': i,
                    'summary': summary,
                    'question_preview': qa['question'][:150],  # First 150 chars
                    'answer_preview': qa['answer'][:150],
                    'question_timestamp': qa['question_timestamp'],
                    'answer_timestamp': qa['answer_timestamp'],
                    'user_message_id': qa['user_message_id'],
                    'assistant_message_id': qa['assistant_message_id']
                })
                
                # Add to combined text for embedding
                combined_text_parts.append(f"[Q{i}] {summary}")
                
                print(f"  ✅ Summary {i}/{len(qa_list)}: {summary[:60]}...")
            
            # Create combined summary text (for embedding)
            combined_text = " | ".join(combined_text_parts)
            
            # Generate embedding
            print(f"🔢 Generating embedding...")
            embedding = self.embed_service.embed_text(
                combined_text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            
            # Create ENHANCED Elasticsearch document
            doc_id = f"memory_{session_id}_batch{batch_number}_{uuid.uuid4().hex[:6]}"
            
            doc = {
                # Core identifiers
                "id": doc_id,
                "user_id": user_id,
                "session_id": str(session_id),
                "session_title": session_title,
                
                # Batch info
                "batch_number": batch_number,
                "message_count": len(qa_list) * 2,
                
                # Summary text (for BM25 keyword search)
                "summary": combined_text,
                
                # Vector embedding (for semantic search)
                "embedding": embedding,
                
                # Individual summaries with FULL metadata
                "qa_summaries": individual_summaries,
                
                # Timestamps (for temporal filtering)
                "created_at": datetime.now().isoformat(),
                "timestamp": datetime.now().isoformat(),
                "first_qa_timestamp": qa_list[0]['question_timestamp'],
                "last_qa_timestamp": qa_list[-1]['answer_timestamp'],
                
                # Searchable keywords
                "keywords": [
                    session_title,
                    f"batch_{batch_number}",
                    f"session_{session_id}"
                ]
            }
            
            # Index to Elasticsearch
            print(f"📊 Indexing to Elasticsearch...")
            success = self.es_manager.index_document(
                index_name="jarvis_chat_memory",
                doc_id=doc_id,
                document=doc
            )
            
            if success:
                print(f"✅ Chat memory indexed: {doc_id}")
                print(f"   Session: {session_title}")
                print(f"   Batch: #{batch_number}")
                print(f"   Q&As: {len(qa_list)}")
                print(f"   Timespan: {qa_list[0]['question_timestamp']} to {qa_list[-1]['answer_timestamp']}")
            else:
                print(f"❌ Failed to index chat memory")
                
        except Exception as e:
            print(f"❌ Summarization & indexing failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _generate_summary(self, question: str, answer: str) -> str:
        """
        Generate CONCISE summary for a single Q&A pair
        Max 20 words to prevent long combined summaries
        """
        try:
            # Truncate long Q&A for summarization
            q_truncated = question[:500]
            a_truncated = answer[:500]
            
            prompt = f"""Summarize this Q&A exchange in EXACTLY 15-20 words. Be concise and focus on the main topic.

Question: {q_truncated}
Answer: {a_truncated}

Summary (15-20 words only):"""
            
            response = self.summarizer.generate_content(prompt)
            summary = response.text.strip()
            
            # Force max 150 characters
            if len(summary) > 150:
                summary = summary[:147] + "..."
            
            return summary
            
        except Exception as e:
            print(f"⚠️ Summary generation failed: {e}")
            # Fallback: extract first 15 words from question
            words = question.split()[:15]
            return " ".join(words) + "..."
    
    def get_memory_stats(self, user_id: int) -> dict:
        """Get statistics about stored memories"""
        try:
            # Query Elasticsearch for total memories
            results = self.es_manager.client.search(
                index="jarvis_chat_memory",
                body={
                    "query": {
                        "term": {"user_id": user_id}
                    },
                    "size": 0
                }
            )
            
            total_memories = results['hits']['total']['value']
            
            # Calculate total Q&As stored
            total_qas = total_memories * self.trigger_count
            
            return {
                'total_memories': total_memories,
                'total_qas_summarized': total_qas,
                'trigger_count': self.trigger_count
            }
        except Exception as e:
            return {'error': str(e)}
    
    def search_memories(self, user_id: int, query: str, top_k: int = 3) -> list:
        """
        Search user's memories by query
        Used for debugging/testing
        """
        try:
            # Generate query embedding
            query_embedding = self.embed_service.embed_query(query)
            
            # Hybrid search on memories
            results = self.es_manager.client.search(
                index="jarvis_chat_memory",
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"user_id": user_id}}
                            ],
                            "should": [
                                {
                                    "script_score": {
                                        "query": {"match_all": {}},
                                        "script": {
                                            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                            "params": {"query_vector": query_embedding}
                                        }
                                    }
                                },
                                {
                                    "multi_match": {
                                        "query": query,
                                        "fields": ["summary^2", "keywords"]
                                    }
                                }
                            ]
                        }
                    },
                    "size": top_k
                }
            )
            
            memories = []
            for hit in results['hits']['hits']:
                source = hit['_source']
                memories.append({
                    'id': source['id'],
                    'session_title': source['session_title'],
                    'summary': source['summary'],
                    'batch_number': source['batch_number'],
                    'qa_count': len(source['qa_summaries']),
                    'timestamp': source['first_qa_timestamp'],
                    'score': hit['_score']
                })
            
            return memories
            
        except Exception as e:
            print(f"❌ Memory search failed: {e}")
            return []
