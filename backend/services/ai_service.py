from dotenv import load_dotenv
import os
import json
from google import genai
import requests
from elevenlabs import ElevenLabs
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Initialize Gemini client globally
gemini_client = None

# Initialize AI services
def init_ai_services():
    """Initialize all AI service API keys"""
    global gemini_client
    # Gemini - using new SDK
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_structured_json(text: str) -> Dict[str, Any]:
    """
    Use Gemini 2.5 Flash Lite to convert raw text to structured JSON
    """
    try:
        prompt = f"""
        Convert the following PDF text into a structured JSON format representing concepts and their relationships.

        Return a JSON object with:
        1. "concepts": array of concept objects with name, description, level, and special_notes
        2. "hierarchy": nested structure showing concept relationships
        3. "metadata": course info, difficulty level, estimated study time

        Text to analyze:
        {text[:2000]}

        Return ONLY valid JSON, no markdown code blocks, no explanations, just the raw JSON object.
        """

        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt,
            config={
                'temperature': 0.1,
                'response_mime_type': 'application/json'
            }
        )

        # Clean response text - remove markdown code blocks if present
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        return json.loads(response_text)

    except Exception as e:
        raise Exception(f"Failed to generate structured JSON: {str(e)}")

async def generate_ai_digest(text: str) -> Dict[str, Any]:
    """
    Use OpenRouter (Grok 4 Fast) to create concise AI-optimized concept outline
    """
    try:
        prompt = f"""
        Analyze this PDF text and create a concise concept outline optimized for AI-to-AI communication.

        Create a JSON structure with:
        1. "course_info": title, subject, difficulty_level
        2. "sequential_concepts": array of concepts in learning order
           - Each concept: name, brief_description, unit/chapter, prerequisites
        3. "key_formulas": important formulas/equations (if any)
        4. "important_notes": critical points for AI understanding

        Text to analyze:
        {text[:3000]}

        Make this maximally efficient for another AI to understand and process.
        Return ONLY valid JSON, no explanations.
        """
        
        response_text = await call_openrouter("x-ai/grok-4-fast", prompt, 1500)
        return json.loads(response_text)
    
    except Exception as e:
        raise Exception(f"Failed to generate AI digest: {str(e)}")

async def generate_relationships(structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use Gemini 2.5 Flash Lite to transform AI digest into knowledge graph
    """
    try:
        prompt = f"""
        Transform this AI digest into a simple knowledge graph.

        AI Digest: {json.dumps(structured_data, indent=2)}

        Create a JSON object with:
        1. "nodes": array of simple concept nodes
           - Each node: name (string), ins (array of prerequisite node names), outs (array of dependent node names)
        2. "graph_metadata": title, subject, total_concepts

        Focus on prerequisite relationships. Keep it simple - just name and connections.
        Return ONLY valid JSON, no markdown code blocks, no explanations, just the raw JSON object.
        """

        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=prompt,
            config={
                'temperature': 0.1,
                'response_mime_type': 'application/json'
            }
        )

        # Clean response text - remove markdown code blocks if present
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        return json.loads(response_text)

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
    Use OpenRouter (Grok 4 Fast) to generate study guide overview
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
        
        return await call_openrouter("x-ai/grok-4-fast", prompt, 1500)
    
    except Exception as e:
        raise Exception(f"Failed to generate overview: {str(e)}")

async def generate_audio_script(graph_data: Dict[str, Any]) -> str:
    """
    Use OpenRouter (Grok 4 Fast) to generate audio script for podcast/newsletter
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
        
        return await call_openrouter("x-ai/grok-4-fast", prompt, 1000)
    
    except Exception as e:
        raise Exception(f"Failed to generate audio script: {str(e)}")

async def generate_audio(script_text: str) -> str:
    """
    Use ElevenLabs to generate audio from script
    """
    try:
        # Initialize ElevenLabs client with API key
        client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

        # Generate audio using ElevenLabs text-to-speech
        audio = client.text_to_speech.convert(
            voice_id="JBFqnCBsd6RMkjVDRZzb",  # Rachel - Professional, clear voice
            text=script_text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )

        # In a real implementation, you'd save this to cloud storage (S3/Vercel Blob)
        # For now, return a placeholder URL
        # TODO: Implement actual audio file storage and return real URL
        return "https://example.com/generated-audio.mp3"

    except Exception as e:
        raise Exception(f"Failed to generate audio: {str(e)}")
