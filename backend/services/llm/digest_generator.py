import json
from .providers import get_gemini_client, call_openrouter
from .utils import clean_math_symbols, fix_json_response, create_fallback_digest
from typing import Dict, Any

async def generate_structured_json(text: str) -> Dict[str, Any]:
    """convert raw text to structured json using gemini"""
    gemini_client = get_gemini_client()
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

        # clean response
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
        raise Exception(f"failed to generate structured json: {str(e)}")

async def generate_ai_digest(text: str) -> Dict[str, Any]:
    """create ai-optimized concept outline using openrouter"""
    try:
        # clean text
        cleaned_text = text.replace(chr(10), ' ').replace(chr(13), ' ')
        cleaned_text = clean_math_symbols(cleaned_text)
        
        prompt = f"""
        Analyze this PDF text and create a comprehensive concept outline optimized for building a deep knowledge graph.

        Create a JSON structure with:
        1. "course_info": 
           - "title": descriptive title
           - "subject": academic subject
           - "difficulty_level": basic, intermediate, or advanced
        2. "sequential_concepts": concepts in learning order
        3. "key_formulas": formulas, equations
        4. "specific_examples": concrete examples
        5. "techniques_methods": procedures
        6. "properties_rules": theorems, rules
        7. "important_notes": critical insights

        Text to analyze:
        {cleaned_text}

        Return ONLY valid JSON.
        """
        
        response_text = await call_openrouter("x-ai/grok-4-fast", prompt, 4000)
        
        # parse/fix json
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            fixed_response = fix_json_response(response_text)
            try:
                return json.loads(fixed_response)
            except json.JSONDecodeError:
                return create_fallback_digest(response_text)
    
    except Exception as e:
        raise Exception(f"failed to generate ai digest: {str(e)}")
