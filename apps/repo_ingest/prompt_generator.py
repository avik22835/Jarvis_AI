# apps/repo_ingest/prompt_generator.py
"""
Generate suggested prompts based on repository analysis
"""
import google.generativeai as genai
import os
from .models import Repository, CodeChunk


genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class PromptGenerator:
    """Generate smart prompts for a repository"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def generate_prompts(self, repository: Repository) -> list:
        """
        Analyze repository and generate 8-10 smart prompts
        
        Returns:
            List of prompt strings
        """
        try:
            print(f"🎯 Generating suggested prompts for {repository.name}...")
            
            # Get repository statistics
            stats = self._get_repo_stats(repository)
            
            # Get sample code chunks for context
            sample_chunks = self._get_sample_chunks(repository, limit=10)
            
            # Build analysis context
            context = self._build_context(stats, sample_chunks)
            
            # Generate prompts with Gemini
            prompts = self._generate_with_gemini(repository.name, context)
            
            print(f"✅ Generated {len(prompts)} prompts")
            return prompts
            
        except Exception as e:
            print(f"❌ Prompt generation failed: {e}")
            return self._get_fallback_prompts()
    
    def _get_repo_stats(self, repository: Repository) -> dict:
        """Get repository statistics"""
        chunks = CodeChunk.objects.filter(repository=repository)
        
        # Count by type
        chunk_types = {}
        languages = set()
        files = set()
        
        for chunk in chunks:
            chunk_types[chunk.chunk_type] = chunk_types.get(chunk.chunk_type, 0) + 1
            languages.add(chunk.language)
            files.add(chunk.file_path)
        
        return {
            'total_files': len(files),
            'total_chunks': chunks.count(),
            'chunk_types': chunk_types,
            'languages': list(languages),
            'name': repository.name,
            'description': repository.description
        }
    
    def _get_sample_chunks(self, repository: Repository, limit=10) -> list:
        """Get sample code chunks for context"""
        chunks = CodeChunk.objects.filter(repository=repository)[:limit]
        
        samples = []
        for chunk in chunks:
            samples.append({
                'type': chunk.chunk_type,
                'name': chunk.chunk_name,
                'file': chunk.file_path,
                'summary': chunk.summary[:150]  # First 150 chars
            })
        
        return samples
    
    def _build_context(self, stats: dict, samples: list) -> str:
        """Build context string for Gemini"""
        context = f"""Repository: {stats['name']}
Description: {stats['description'] or 'No description'}

Statistics:
- Total files: {stats['total_files']}
- Total code chunks: {stats['total_chunks']}
- Languages: {', '.join(stats['languages'])}
- Chunk types: {', '.join([f"{k}({v})" for k, v in stats['chunk_types'].items()])}

Sample code chunks:
"""
        
        for i, sample in enumerate(samples[:5], 1):
            context += f"\n{i}. {sample['type']}: {sample['name']} ({sample['file']})"
            context += f"\n   Summary: {sample['summary']}"
        
        return context
    
    def _generate_with_gemini(self, repo_name: str, context: str) -> list:
        """Generate prompts using Gemini"""
        prompt = f"""You are analyzing a code repository to generate smart, specific questions a developer might ask.

{context}

Generate 8-10 diverse, specific questions about this repository that would be useful for a developer to ask.

Requirements:
- Questions should be SPECIFIC to this codebase (not generic)
- Cover different aspects: architecture, functionality, debugging, testing, deployment
- Mix high-level (architecture) and detailed (specific functions)
- Make them actionable and practical
- Keep each question concise (max 10 words)

Format as a JSON array of strings:
["question 1", "question 2", ...]

Only return the JSON array, no other text."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean JSON
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            import json
            prompts = json.loads(result_text)
            
            # Validate
            if isinstance(prompts, list) and len(prompts) >= 5:
                return prompts[:10]  # Max 10
            else:
                return self._get_fallback_prompts()
                
        except Exception as e:
            print(f"⚠️ Gemini generation failed: {e}")
            return self._get_fallback_prompts()
    
    def _get_fallback_prompts(self) -> list:
        """Fallback prompts if generation fails"""
        return [
            "Give me a high-level overview of the architecture",
            "Explain the main functionality of this project",
            "What are the key components and how do they interact?",
            "Show me the most important functions",
            "How does the data flow through the system?",
            "What external libraries and frameworks are used?",
            "Are there any potential bugs or issues?",
            "Explain the testing strategy"
        ]

