# apps/chat/image_handler.py
"""
Handle images in main chat (diagrams, code screenshots, UI mockups)
NOT for error debugging - that's in debugger app
"""
import google.generativeai as genai
import os
from PIL import Image
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid


genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class ChatImageHandler:
    """Process images in main chat context"""
    
    def __init__(self):
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def save_image(self, image_file) -> str:
        """Save uploaded image and return path"""
        try:
            filename = f"chat_{uuid.uuid4().hex}.{image_file.name.split('.')[-1]}"
            image_path = default_storage.save(f"chat_images/{filename}", ContentFile(image_file.read()))
            return image_path
        except Exception as e:
            print(f"❌ Image save failed: {e}")
            return None
    
    def analyze_image(self, image_path: str, user_question: str, code_context: str = "") -> str:
        """
        Analyze image with Gemini Vision in context of user's codebase
        
        Args:
            image_path: Path to saved image
            user_question: User's question about the image
            code_context: Relevant code chunks (optional)
        
        Returns:
            AI response analyzing the image
        """
        try:
            full_path = os.path.join(default_storage.location, image_path)
            image = Image.open(full_path)
            
            # Build prompt with code context if available
            if code_context:
                prompt = f"""You are analyzing an image in the context of the user's codebase.

**User Question:** {user_question}

**Relevant Code Context:**
{code_context}

**Instructions:**
1. Analyze the image (diagram, screenshot, mockup, etc.)
2. Relate it to the user's code if relevant
3. Answer the user's question comprehensively
4. Use markdown formatting

Your analysis:"""
            else:
                prompt = f"""Analyze this image and answer the user's question.

**User Question:** {user_question}

**Instructions:**
1. Describe what you see in the image
2. Provide technical insights
3. Answer the question thoroughly
4. Use markdown formatting

Your analysis:"""
            
            # Generate response with image
            response = self.vision_model.generate_content([prompt, image])
            
            return response.text
            
        except Exception as e:
            print(f"❌ Image analysis failed: {e}")
            return f"Sorry, I couldn't analyze the image. Error: {str(e)}"
    
    def analyze_image_stream(self, image_path: str, user_question: str, code_context: str = ""):
        """
        Analyze image with STREAMING response
        """
        try:
            full_path = os.path.join(default_storage.location, image_path)
            image = Image.open(full_path)
            
            # Build prompt
            if code_context:
                prompt = f"""You are analyzing an image in the context of the user's codebase.

**User Question:** {user_question}

**Relevant Code Context:**
{code_context[:1000]}...

Analyze the image and answer comprehensively. Use markdown formatting."""
            else:
                prompt = f"""Analyze this image and answer: {user_question}

Use markdown formatting."""
            
            # Stream response
            response = self.vision_model.generate_content([prompt, image], stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"\n\n❌ Image analysis failed: {str(e)}"
 
