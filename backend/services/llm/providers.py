from google import genai
import requests
import os
from core.config import get_settings

# global gemini client
gemini_client = None

def init_ai_services():
    """initialize ai service clients"""
    global gemini_client
    settings = get_settings()
    # initialize gemini client
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def call_openrouter(model: str, prompt: str, max_tokens: int = 1500) -> str:
    """call openrouter api"""
    settings = get_settings()
    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        else:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
    
    except Exception as e:
        raise Exception(f"Failed to call OpenRouter: {str(e)}")

def get_gemini_client():
    if gemini_client is None:
        init_ai_services()
    return gemini_client
