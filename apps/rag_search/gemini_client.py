import google.generativeai as genai
import os
from typing import List, Dict, Optional

def get_gemini_client():
    """Initialize Gemini API client"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    genai.configure(api_key=api_key)
    return genai

def test_gemini_connection():
    """Test Gemini API connection"""
    try:
        client = get_gemini_client()
        # Test with a simple generation
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Say 'Hello Jarvis!'")
        print(f"✅ Gemini API connected successfully")
        print(f"   Response: {response.text}")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Gemini API: {str(e)}")
        return False
 
