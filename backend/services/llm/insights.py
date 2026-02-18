import json
from typing import Optional
from .providers import get_gemini_client
from .utils import fix_json_response, fix_latex_json_escapes

async def generate_concept_insights(concept_name: str, context_data: Optional[dict] = None) -> dict:
    """generate concise insights about a concept"""
    gemini_client = get_gemini_client()
    try:
        # build context
        context_info = ""
        if context_data:
            context_info = f"""
            CONTEXT INFORMATION:
            - Subject: {context_data.get('subject', 'Unknown')}
            - Course: {context_data.get('title', 'Unknown')}
            - Related concepts in graph: {', '.join(context_data.get('related_concepts', [])[:10])}
            """
        
        prompt = f"""
        Provide concise, educational insights about the concept: "{concept_name}"
        
        {context_info}
        
        Generate a structured response with:
        
        1. **OVERVIEW** (2-3 sentences): What this concept is and why it's important
        2. **RELATED CONCEPTS** (3-5 items): Key concepts that connect to this one
        3. **IMPORTANT FORMULAS** (up to 5): Key equations, formulas, or mathematical expressions
        4. **KEY THEOREMS** (up to 5): Important theorems, rules, or principles
        
        Guidelines:
        - Be concise but comprehensive
        - Use clear, educational language
        - Focus on what students need to know
        - Include practical applications when relevant
        - For math concepts, include the actual formulas using LaTeX notation
        - Use $inline math$ for inline formulas and $$display math$$ for centered equations
        - For non-math concepts, focus on key principles and relationships
        - IMPORTANT: Double-escape all backslashes in LaTeX (e.g., \\frac not \\frac)
        
        Return ONLY valid JSON in this exact format:
        {{
            "overview": "Brief overview with $inline math$ when needed",
            "related_concepts": ["concept1", "concept2", "concept3"],
            "important_formulas": ["$f(x) = ax + b$", "$$\\int_a^b f(x) dx = F(b) - F(a)$$"],
            "key_theorems": ["theorem1 with $math notation$", "theorem2"]
        }}
        """

        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents=prompt,
            config={
                'temperature': 0.3,
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

        # fix latex for json
        response_text = fix_latex_json_escapes(response_text)

        # parse json
        try:
            insights = json.loads(response_text)
        except json.JSONDecodeError:
            # try repair
            response_text = fix_json_response(response_text)
            insights = json.loads(response_text)
            
        return insights

    except Exception as e:
        # fallback
        return {
            "overview": f"could not generate insights for {concept_name} due to an error.",
            "related_concepts": [],
            "important_formulas": [],
            "key_theorems": []
        }
