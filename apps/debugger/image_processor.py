# apps/debugger/image_processor.py
"""
Image processing for debug assistant using Gemini Vision
"""
import google.generativeai as genai
import os
from PIL import Image


genai.configure(api_key=os.getenv('GEMINI_API_KEY'))


class DebugImageProcessor:
    """Extract error information from screenshots"""
    
    def __init__(self):
        self.vision_model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def extract_error_from_image(self, image_path: str) -> dict:
        """
        Extract error details from screenshot
        
        Returns:
            {
                'error_type': str,
                'error_message': str,
                'stack_trace': str,
                'file_location': str,
                'language': str,
                'extracted_text': str
            }
        """
        try:
            image = Image.open(image_path)
            
            prompt = """Analyze this error screenshot and extract:

1. **Error Type** (e.g., ValueError, 404 Error, NullPointerException)
2. **Error Message** (exact error text)
3. **Stack Trace** (if visible, key lines only)
4. **File/Line** (where error occurred)
5. **Language/Framework** (Python, JavaScript, Java, etc.)

Respond ONLY with JSON (no markdown):
{
  "error_type": "...",
  "error_message": "...",
  "stack_trace": "...",
  "file_location": "...",
  "language": "...",
  "extracted_text": "..."
}"""

            response = self.vision_model.generate_content([prompt, image])
            result_text = response.text.strip()
            
            # Clean JSON
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            import json
            return json.loads(result_text)
            
        except Exception as e:
            print(f"❌ Image extraction failed: {e}")
            return {
                'error_type': 'Unknown',
                'error_message': 'Could not extract error from image',
                'extracted_text': str(e)
            }

