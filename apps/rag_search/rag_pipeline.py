from typing import List, Dict
import json
import google.generativeai as genai
import os
from .embeddings import EmbeddingService
from .generation import GenerationService
from .es_ops import ElasticsearchManager
from apps.chat.models import ChatMessage


# Initialize Gemini for intent detection
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class RAGPipeline:
    """
    Complete RAG pipeline with AI-powered intent detection and Gemini reranking
    - Uses Gemini to classify query intent
    - Dynamically adjusts retrieval count
    - Reranks results with Gemini for better relevance
    - Supports metadata aggregation for "list all X" queries
    """
    
    def __init__(self):
        self.embed_service = EmbeddingService()
        self.generation_service = GenerationService()
        self.es_manager = ElasticsearchManager()
        self.intent_model = genai.GenerativeModel("gemini-2.5-flash")
        self.reranker_model = genai.GenerativeModel("gemini-2.0-flash-exp")  # ✅ NEW: For reranking
    
    def process_query(
        self,
        question: str,
        user_id: int,
        session_id: int,
        max_summaries: int = 3
    ) -> str:
        """
        Process user query with AI-powered intent detection and reranking
        
        Args:
            question: User's question
            user_id: User ID for filtering
            session_id: Chat session ID
            max_summaries: Max past summaries to retrieve
        
        Returns:
            Generated answer
        """
        
        # Step 1: AI-powered intent detection
        intent = self._detect_query_intent_ai(question)
        print(f"🎯 AI Intent: {intent['type']} (confidence: {intent['confidence']:.2f}, retrieving {intent['top_k']} chunks)")
        
        # Step 2: Embed the question
        print(f"🔍 Embedding question: {question[:50]}...")
        query_embedding = self.embed_service.embed_query(question)
        print(f"✅ Generated {len(query_embedding)}-dim embedding")
        
        # Step 3: Smart code retrieval based on intent
        print(f"📚 Searching for relevant code...")
        if intent['type'] == 'aggregation':
            code_chunks = self._retrieve_code_aggregation(
                query_embedding=query_embedding,
                user_id=user_id,
                question=question,
                top_k=intent['top_k']
            )
        else:
            code_chunks = self._retrieve_code_context(
                query_embedding=query_embedding,
                user_id=user_id,
                question=question,  # ✅ Pass question for reranking
                top_k=intent['top_k'],
                use_reranking=(intent['type'] in ['specific', 'overview'])  # ✅ NEW: Enable reranking
            )
        print(f"✅ Found {len(code_chunks)} code chunks")
        
        # Step 4: Retrieve past conversation summaries
        print(f"💭 Searching for past conversations...")
        past_summaries = self._retrieve_past_summaries(
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=max_summaries
        )
        print(f"✅ Found {len(past_summaries)} past summaries")
        
        # Step 5: Get session messages for 3-tier memory
        print(f"🗂️ Loading session history...")
        session_messages = self._get_session_messages(session_id)
        print(f"✅ Loaded {len(session_messages)} messages")
        
        # Step 6: Generate answer with full context
        print(f"🤖 Generating answer...")
        answer = self.generation_service.generate_with_full_context(
            question=question,
            code_chunks=code_chunks,
            past_summaries=past_summaries,
            session_messages=session_messages,
            max_code_chunks=len(code_chunks),
            max_summaries=max_summaries
        )
        print(f"✅ Answer generated ({len(answer)} chars)")
        
        return answer
    
    def _detect_query_intent_ai(self, question: str) -> dict:
        """
        Use Gemini AI to detect query intent
        
        Args:
            question: User's question
        
        Returns:
            {
                'type': 'specific' | 'aggregation' | 'overview',
                'top_k': int,
                'confidence': float,
                'reasoning': str
            }
        """
        
        prompt = f"""You are a query intent classifier for a code search system.

Classify this user query into ONE of these three types:

1. **specific**: Query about a single concept, function, or implementation detail
   - Examples: "How does login work?", "Explain the UserModel class", "What does this function do?"
   - Retrieval strategy: Top 5 most relevant code chunks

2. **aggregation**: Query asking for a complete list or count of all items
   - Examples: "What are all the functions?", "List all API endpoints", "How many classes?"
   - Retrieval strategy: Top 50 chunks to get comprehensive coverage

3. **overview**: Query asking for high-level architecture or project structure
   - Examples: "Explain the project structure", "Give me an overview", "How is this organized?"
   - Retrieval strategy: Top 20 diverse chunks

User Query: "{question}"

Respond with ONLY a valid JSON object (no markdown, no extra text):
{{
  "type": "specific|aggregation|overview",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}"""

        try:
            response = self.intent_model.generate_content(prompt)
            response_text = response.text.strip()
            
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            intent_type = result.get('type', 'specific')
            confidence = float(result.get('confidence', 0.8))
            reasoning = result.get('reasoning', 'AI classification')
            
            top_k_map = {
                'specific': 5,
                'aggregation': 50,
                'overview': 20
            }
            
            top_k = top_k_map.get(intent_type, 5)
            
            return {
                'type': intent_type,
                'top_k': top_k,
                'confidence': confidence,
                'reasoning': reasoning
            }
        
        except Exception as e:
            print(f"⚠️ AI intent detection failed: {str(e)}, falling back to keywords")
            return self._detect_query_intent_fallback(question)
    
    def _detect_query_intent_fallback(self, question: str) -> dict:
        """Fallback keyword-based intent detection"""
        question_lower = question.lower()
        
        aggregation_keywords = [
            'all', 'list all', 'show all', 'every', 'how many',
            'count', 'total', 'entire', 'complete list',
            'what functions', 'what classes', 'what files',
            'all the', 'show me all', 'give me all'
        ]
        
        overview_keywords = [
            'overview', 'summary', 'structure', 'architecture',
            'how is', 'organized', 'explain the project',
            'project structure', 'codebase structure'
        ]
        
        if any(keyword in question_lower for keyword in aggregation_keywords):
            return {
                'type': 'aggregation',
                'top_k': 50,
                'confidence': 0.7,
                'reasoning': 'Keyword match (fallback)'
            }
        elif any(keyword in question_lower for keyword in overview_keywords):
            return {
                'type': 'overview',
                'top_k': 20,
                'confidence': 0.7,
                'reasoning': 'Keyword match (fallback)'
            }
        else:
            return {
                'type': 'specific',
                'top_k': 5,
                'confidence': 0.6,
                'reasoning': 'Default (fallback)'
            }
    
    # ✅ NEW: Gemini-powered reranking
    def _rerank_with_gemini(self, question: str, chunks: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Use Gemini to rerank code chunks by relevance to the question
        
        Args:
            question: User's question
            chunks: List of code chunks from hybrid search
            top_k: Number of top chunks to return after reranking
        
        Returns:
            Reranked list of code chunks
        """
        
        if not chunks:
            return []
        
        # Limit input to top 20 chunks to avoid token limits
        chunks_to_rerank = chunks[:20]
        
        # Format chunks for Gemini
        chunk_summaries = []
        for i, chunk in enumerate(chunks_to_rerank):
            source = chunk.get('_source', {})
            chunk_summaries.append({
                'index': i,
                'type': source.get('chunk_type', 'unknown'),
                'name': source.get('chunk_name', 'unknown'),
                'summary': source.get('summary', '')[:200],  # Limit summary length
                'file': source.get('file_path', 'unknown')
            })
        
        prompt = f"""You are a code relevance ranker. Given a question and code chunks, rank them by relevance.

Question: "{question}"

Code Chunks:
{json.dumps(chunk_summaries, indent=2)}

Rank these chunks from most to least relevant to the question.
Return ONLY a JSON array of indices in ranked order (most relevant first):
[index1, index2, index3, ...]

Return at most {top_k} indices."""

        try:
            response = self.reranker_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean response
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse rankings
            rankings = json.loads(response_text)
            
            # Reorder chunks based on rankings
            reranked_chunks = []
            for idx in rankings[:top_k]:
                if 0 <= idx < len(chunks_to_rerank):
                    reranked_chunks.append(chunks_to_rerank[idx])
            
            print(f"🎯 Gemini reranked {len(reranked_chunks)} chunks")
            return reranked_chunks
        
        except Exception as e:
            print(f"⚠️ Reranking failed: {str(e)}, using original order")
            return chunks[:top_k]
    
    def _retrieve_code_aggregation(
        self,
        query_embedding: List[float],
        user_id: int,
        question: str,
        top_k: int = 50
    ) -> List[Dict]:
        """Retrieve code for aggregation queries (no reranking needed)"""
        try:
            results = self.es_manager.hybrid_search(
                index_name="jarvis_repo_chunks",
                query_vector=query_embedding,
                query_text="",
                user_id=user_id,
                top_k=top_k
            )
            
            if len(results) > 30:
                print(f"⚠️ Large result set ({len(results)}), may need summarization")
            
            return results
        except Exception as e:
            print(f"⚠️ Code aggregation error: {str(e)}")
            return []
    
    def _retrieve_code_context(
        self,
        query_embedding: List[float],
        user_id: int,
        question: str = "",  # ✅ NEW: For reranking
        top_k: int = 5,
        use_reranking: bool = True  # ✅ NEW: Toggle reranking
    ) -> List[Dict]:
        """
        Retrieve relevant code chunks with optional Gemini reranking
        
        Args:
            query_embedding: Query vector
            user_id: User ID for filtering
            question: User's question (for reranking)
            top_k: Number of chunks to return
            use_reranking: Whether to use Gemini reranking
        
        Returns:
            List of code chunks (reranked if enabled)
        """
        try:
            # Retrieve more chunks if reranking (to give Gemini more options)
            retrieve_k = top_k * 4 if use_reranking else top_k
            
            results = self.es_manager.hybrid_search(
                index_name="jarvis_repo_chunks",
                query_vector=query_embedding,
                query_text="",
                user_id=user_id,
                top_k=retrieve_k
            )
            
            # ✅ Rerank with Gemini if enabled
            if use_reranking and question and len(results) > top_k:
                print(f"🎯 Reranking {len(results)} chunks with Gemini...")
                results = self._rerank_with_gemini(question, results, top_k)
            else:
                results = results[:top_k]
            
            return results
        except Exception as e:
            print(f"⚠️ Code retrieval error: {str(e)}")
            return []
    
    def _retrieve_past_summaries(
        self,
        query_embedding: List[float],
        user_id: int,
        top_k: int = 3
    ) -> List[Dict]:
        """Retrieve relevant past conversation summaries"""
        try:
            results = self.es_manager.hybrid_search(
                index_name="jarvis_chat_memory",
                query_vector=query_embedding,
                query_text="",
                user_id=user_id,
                top_k=top_k
            )
            return results
        except Exception as e:
            print(f"⚠️ Summary retrieval error: {str(e)}")
            return []
    
    def _get_session_messages(self, session_id: int) -> List[Dict]:
        """Get all messages from current session for 3-tier memory"""
        try:
            messages = ChatMessage.objects.filter(
                session_id=session_id
            ).order_by('created_at').values('role', 'content')
            
            return [
                {
                    "role": msg["role"],
                    "content": msg["content"]
                }
                for msg in messages
            ]
        except Exception as e:
            print(f"⚠️ Session message retrieval error: {str(e)}")
            return []
    
    def process_query_simple(self, question: str, user_id: int, session_id: int) -> str:
        """Simplified version for testing (no code/summary retrieval)"""
        session_messages = self._get_session_messages(session_id)
        
        answer = self.generation_service.generate_with_full_context(
            question=question,
            code_chunks=[],
            past_summaries=[],
            session_messages=session_messages
        )
        
        return answer
