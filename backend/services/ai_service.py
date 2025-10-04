from dotenv import load_dotenv
import os
import json
from google import genai
import requests
from elevenlabs.client import ElevenLabs
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Initialize AI services
def init_ai_services():
    """Initialize all AI service API keys"""
    # Gemini
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_structured_json(text: str) -> Dict[str, Any]:
    """
    Use Gemini 2.5 Flash Lite to convert raw text to structured JSON
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""
        Convert the following PDF text into a structured JSON format representing concepts and their relationships.
        
        Return a JSON object with:
        1. "concepts": array of concept objects with name, description, level, and special_notes
        2. "hierarchy": nested structure showing concept relationships
        3. "metadata": course info, difficulty level, estimated study time
        
        Text to analyze:
        {text[:8000]}  # Limit to avoid token limits
        
        Return only valid JSON, no additional text.
        """
        
        response = model.generate_content(prompt)
        return json.loads(response.text)
    
    except Exception as e:
        raise Exception(f"Failed to generate structured JSON: {str(e)}")

async def generate_relationships(structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use Gemini 2.5 Flash Lite to extract concept relationships
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""
        Analyze this structured course data and extract concept relationships.
        
        Data: {json.dumps(structured_data, indent=2)}
        
        Return a JSON object with:
        1. "nodes": array of concept nodes for the graph
        2. "edges": array of relationships between concepts
        3. "graph_metadata": layout hints, difficulty levels, etc.
        
        Focus on prerequisite relationships, concept dependencies, and learning paths.
        Return only valid JSON.
        """
        
        response = model.generate_content(prompt)
        return json.loads(response.text)
    
    except Exception as e:
        raise Exception(f"Failed to generate relationships: {str(e)}")

async def call_openrouter(model: str, prompt: str, max_tokens: int = 1500) -> str:
    """
    Call OpenRouter API with specified model
    """
    try:
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
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
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"OpenRouter API error: {response.status_code}")
    
    except Exception as e:
        raise Exception(f"Failed to call OpenRouter: {str(e)}")

async def generate_overview(graph_data: Dict[str, Any]) -> str:
    """
    Use OpenRouter (DeepSeek) to generate study guide overview
    """
    try:
        prompt = f"""
        Create a comprehensive study guide overview based on this knowledge graph:
        
        {json.dumps(graph_data, indent=2)}
        
        Format as a structured study guide with:
        1. Course Overview
        2. Key Concepts (with brief explanations)
        3. Learning Path (recommended order)
        4. Study Tips
        5. Practice Recommendations
        
        Make it concise but informative, suitable for students.
        """
        
        return await call_openrouter("deepseek/deepseek-chat", prompt, 1500)
    
    except Exception as e:
        raise Exception(f"Failed to generate overview: {str(e)}")

async def generate_audio_script(graph_data: Dict[str, Any]) -> str:
    """
    Use OpenRouter (DeepSeek) to generate audio script for podcast/newsletter
    """
    try:
        prompt = f"""
        Create a podcast-style audio script (5-7 minutes) based on this knowledge graph:
        
        {json.dumps(graph_data, indent=2)}
        
        Make it engaging and conversational, like a morning newsletter podcast.
        Include:
        1. Introduction to the topic
        2. Key concepts explained simply
        3. How concepts connect
        4. Study tips and recommendations
        5. Encouraging conclusion
        
        Write for audio delivery - use conversational tone, natural transitions.
        """
        
        return await call_openrouter("deepseek/deepseek-chat", prompt, 1000)
    
    except Exception as e:
        raise Exception(f"Failed to generate audio script: {str(e)}")

async def generate_audio(script_text: str) -> str:
    """
    Use ElevenLabs to generate audio from script
    """
    try:
        # Initialize ElevenLabs client with API key
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        
        # Generate audio using ElevenLabs
        audio = client.generate(
            text=script_text,
            voice="Rachel",  # Professional, clear voice
            model="eleven_multilingual_v2"
        )
        
        # In a real implementation, you'd save this to cloud storage
        # For now, return a placeholder URL
        return "https://example.com/generated-audio.mp3"
    
    except Exception as e:
        raise Exception(f"Failed to generate audio: {str(e)}")
