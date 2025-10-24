import google.generativeai as genai
import os
from typing import List, Dict, Optional

# Initialize Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class GenerationService:
    """Generate answers using Gemini with RAG and multi-tier memory"""
    
    def __init__(self, model_name="gemini-2.5-flash"):
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        
        # Memory stack configuration
        self.RECENT_SIZE = 3
        self.MEDIUM_SIZE = 5
        self.OLDER_SIZE = 10
    
    def generate_with_full_context(
        self,
        question: str,
        code_chunks: List[Dict],
        past_summaries: List[Dict],
        session_messages: List[Dict],
        max_code_chunks: int = 5,
        max_summaries: int = 3
    ) -> str:
        prompt = self._build_full_prompt(
            question, code_chunks, past_summaries, 
            session_messages, max_code_chunks, max_summaries
        )
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def generate_with_full_context_stream(
        self,
        question: str,
        code_chunks: List[Dict],
        past_summaries: List[Dict],
        session_messages: List[Dict],
        max_code_chunks: int = 5,
        max_summaries: int = 3
    ):
        """Stream response from Gemini"""
        prompt = self._build_full_prompt(
            question, code_chunks, past_summaries, 
            session_messages, max_code_chunks, max_summaries
        )
        try:
            response = self.model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Sorry, I encountered an error: {str(e)}"
    
    def _build_full_prompt(
        self,
        question: str,
        code_chunks: List[Dict],
        past_summaries: List[Dict],
        session_messages: List[Dict],
        max_code_chunks: int,
        max_summaries: int
    ) -> str:
        recent_msgs, medium_msgs, older_summary = self._build_memory_stack(session_messages)
        code_context = self._build_code_context(code_chunks[:max_code_chunks])
        past_context = self._build_past_context(past_summaries[:max_summaries])
        system_prompt = self._get_system_prompt()
        older_formatted = self._format_older_messages(older_summary)
        medium_formatted = self._format_medium_messages(medium_msgs)
        recent_formatted = self._format_recent_messages(recent_msgs)
        code_section = self._format_context_section("CODE CONTEXT", code_context)
        past_section = self._format_context_section("PREVIOUS CONVERSATION CONTEXT", past_context)
        
        prompt = f"""{system_prompt}

---

AVAILABLE CONTEXT:

{code_section}

{past_section}

---

CHAT HISTORY (Current Session):

{older_formatted}

{medium_formatted}

{recent_formatted}

---

CURRENT QUESTION: {question}

INSTRUCTIONS:
- Answer the question directly and helpfully
- For pronouns (it, this, that): Refer to [RECENT] messages
- For follow-ups: Use [MEDIUM] messages
- For questions ABOUT the codebase: Use CODE CONTEXT
- For requests to WRITE NEW CODE in any language: Use your knowledge freely, ignore CODE CONTEXT language
- For references to past discussions: Use PREVIOUS CONVERSATION CONTEXT
- Combine contexts when helpful

ANSWER:"""
        return prompt
    
    def _build_memory_stack(self, messages: List[Dict]) -> tuple:
        total = len(messages)
        recent_start = max(0, total - self.RECENT_SIZE)
        recent = messages[recent_start:]
        medium_start = max(0, recent_start - self.MEDIUM_SIZE)
        medium = messages[medium_start:recent_start] if recent_start > 0 else []
        older = messages[:medium_start] if medium_start > 0 else []
        older_summary = self._summarize_older_messages(older) if older else None
        return recent, medium, older_summary
    
    def _summarize_older_messages(self, messages: List[Dict]) -> str:
        if not messages:
            return None
        topics = []
        for msg in messages:
            if msg['role'] == 'user':
                topics.append(msg['content'][:100])
        if len(topics) > 3:
            return f"Earlier in conversation: {', '.join(topics[:3])}... and {len(topics)-3} more topics"
        else:
            return f"Earlier in conversation: {', '.join(topics)}"
    
    def _format_recent_messages(self, messages: List[Dict]) -> str:
        if not messages:
            return ""
        formatted = ["[RECENT MESSAGES] (Last 2-3 exchanges):"]
        for msg in messages:
            role = "User" if msg['role'] == 'user' else "Assistant"
            content = msg['content'][:200]
            formatted.append(f"- {role}: {content}")
        return "\n".join(formatted)
    
    def _format_medium_messages(self, messages: List[Dict]) -> str:
        if not messages:
            return ""
        formatted = ["[MEDIUM MESSAGES] (Earlier in session):"]
        for msg in messages:
            role = "User" if msg['role'] == 'user' else "Assistant"
            content = msg['content'][:150]
            formatted.append(f"- {role}: {content}")
        return "\n".join(formatted)
    
    def _format_older_messages(self, summary: Optional[str]) -> str:
        if not summary:
            return ""
        return f"[OLDER MESSAGES] (Summarized):\n- {summary}"
    
    def _build_code_context(self, chunks: List[Dict]) -> str:
        if not chunks:
            return "No relevant code found."
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get('source', {})
            file_path = source.get('file_path', 'Unknown')
            content = source.get('content', '')
            language = source.get('language', 'text')
            context_parts.append(f"""Snippet {i}:
File: {file_path}
Language: {language}

{content}
""")
        return "\n\n".join(context_parts)
    
    def _build_past_context(self, summaries: List[Dict]) -> str:
        if not summaries:
            return "No relevant past conversations."
        context_parts = []
        for i, summary_doc in enumerate(summaries, 1):
            source = summary_doc.get('source', {})
            summary = source.get('summary', '')
            timestamp = source.get('timestamp', 'Unknown time')
            context_parts.append(f"- {summary} (from {timestamp})")
        return "\n".join(context_parts)
    
    def _format_context_section(self, title: str, content: str) -> str:
        return f"""{title}:
{content}"""
    
    def _get_system_prompt(self) -> str:
        return """You are Jarvis, a helpful AI assistant with access to code context and previous conversation summaries.

When answering questions:
1. Use **Markdown formatting** for better readability:
   - Use **bold** for emphasis
   - Use bullet points (- or *) for lists
   - Use numbered lists (1. 2. 3.) when order matters
   - Use code blocks with language tags for code: ```language
   - Use tables for comparisons
   - Use emojis when appropriate to make it interactive 🎯 
   - Use headings (## or ###) for sections

2. **IMPORTANT - Context Usage Rules:**
   - If user asks ABOUT existing code (explain, debug, analyze): Use CODE CONTEXT
   - If user asks to WRITE NEW code in ANY language: Use your own knowledge, ignore CODE CONTEXT language constraints
   - If query doesn't need code context: Answer normally using your knowledge
   - CODE CONTEXT is for reference only - you can write code in any language the user requests

3. Primary focus: Answer the question directly and helpfully

4. For pronouns (it, this, that): Refer to [RECENT] messages, not [MEDIUM] or [OLDER]

5. For questions about the existing codebase: Use the provided CODE CONTEXT

6. For requests to write new code: Write in whatever language the user asks for, regardless of CODE CONTEXT language

7. For follow-up questions: Use PREVIOUS CONVERSATION CONTEXT when relevant

8. For general questions: Answer naturally but consider available context

9. Format code examples properly in code blocks with language tags

10. Structure long answers with headings and bullet points

Context Types Available:
- CODE CONTEXT: Functions, classes, and code snippets from project files (FOR REFERENCE about existing code)
- PREVIOUS CONVERSATION CONTEXT: Summaries of past discussions for continuity
- CHAT HISTORY: 
  - [RECENT]: Last 2-3 exchanges (use for immediate context and pronouns)
  - [MEDIUM]: Earlier in current session (use for session continuity)
  - [OLDER]: Summarized older messages (background context only)

Usage Guidelines:
- CODE CONTEXT is for understanding the EXISTING codebase, not limiting your responses
- When user asks "write a C program", write C code using your knowledge
- When user asks "explain this Python function", use CODE CONTEXT if available
- When user asks "debug my code", use CODE CONTEXT to understand their code
- You can write code in ANY language regardless of what's in CODE CONTEXT
- Prioritize answering what the user actually asks for
- Use PREVIOUS CONVERSATION CONTEXT for references to past discussions
- Use [RECENT] messages for pronouns and immediate context
- Use [MEDIUM] messages for session-level continuity
- Combine contexts when helpful for comprehensive answers
- If no relevant context, answer based on general knowledge

**Remember:** CODE CONTEXT shows you the existing codebase. It does NOT restrict what languages you can use in your answers. If a user asks for C code, write C code. If they ask for Java, write Java. The context is just for reference!

Note: Recent messages are tagged [RECENT] - use these when user says it, this, that, etc.
Note: Always format your responses with proper Markdown for best readability."""
    
    def generate_simple(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_stream(self, prompt: str):
        try:
            response = self.model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"Error: {str(e)}"