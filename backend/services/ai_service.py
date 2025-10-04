from dotenv import load_dotenv
import os
import json
import re
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

def clean_math_symbols(text: str) -> str:
    """
    Clean mathematical symbols and special characters that might break JSON or AI processing
    """
    # Replace common math symbols with text equivalents
    replacements = {
        # Greek letters
        'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon',
        'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa',
        'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron',
        'π': 'pi', 'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon',
        'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',
        
        # Uppercase Greek letters
        'Α': 'Alpha', 'Β': 'Beta', 'Γ': 'Gamma', 'Δ': 'Delta', 'Ε': 'Epsilon',
        'Ζ': 'Zeta', 'Η': 'Eta', 'Θ': 'Theta', 'Ι': 'Iota', 'Κ': 'Kappa',
        'Λ': 'Lambda', 'Μ': 'Mu', 'Ν': 'Nu', 'Ξ': 'Xi', 'Ο': 'Omicron',
        'Π': 'Pi', 'Ρ': 'Rho', 'Σ': 'Sigma', 'Τ': 'Tau', 'Υ': 'Upsilon',
        'Φ': 'Phi', 'Χ': 'Chi', 'Ψ': 'Psi', 'Ω': 'Omega',
        
        # Math operators
        '∑': 'sum', '∏': 'product', '∫': 'integral', '∂': 'partial',
        '∇': 'nabla', '∞': 'infinity', '±': 'plus-minus', '∓': 'minus-plus',
        '×': 'times', '÷': 'divided by', '√': 'square root', '∛': 'cube root',
        '≤': 'less than or equal', '≥': 'greater than or equal', '≠': 'not equal',
        '≈': 'approximately equal', '≡': 'equivalent', '∈': 'element of',
        '∉': 'not element of', '⊂': 'subset', '⊃': 'superset', '∪': 'union',
        '∩': 'intersection', '∅': 'empty set', '∀': 'for all', '∃': 'there exists',
        
        # Arrows
        '→': 'arrow right', '←': 'arrow left', '↑': 'arrow up', '↓': 'arrow down',
        '↔': 'arrow both', '⇒': 'implies', '⇐': 'implied by', '⇔': 'if and only if',
        
        # Other symbols
        '°': 'degrees', '′': 'prime', '″': 'double prime', '‴': 'triple prime',
        'ℵ': 'aleph', 'ℏ': 'h-bar', 'ℑ': 'imaginary part', 'ℜ': 'real part',
    }
    
    # Apply replacements
    for symbol, replacement in replacements.items():
        text = text.replace(symbol, replacement)
    
    # Remove any remaining non-printable characters except spaces
    text = ''.join(char if char.isprintable() or char.isspace() else ' ' for char in text)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def fix_json_response(response_text: str) -> str:
    """
    Attempt to fix common JSON issues in AI responses
    """
    # Remove any text before the first {
    start_idx = response_text.find('{')
    if start_idx > 0:
        response_text = response_text[start_idx:]
    
    # Find the last complete closing brace
    brace_count = 0
    last_complete_idx = -1
    
    for i, char in enumerate(response_text):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                last_complete_idx = i
                break
    
    # If we found a complete JSON structure, use it
    if last_complete_idx > 0:
        response_text = response_text[:last_complete_idx + 1]
    else:
        # Fallback: remove any text after the last }
        end_idx = response_text.rfind('}')
        if end_idx > 0:
            response_text = response_text[:end_idx + 1]
    
    # Fix common issues
    # Remove trailing commas before closing braces/brackets
    response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
    
    # Fix incomplete strings at the end
    # If the response ends with an incomplete string, try to close it
    if response_text.count('"') % 2 == 1:  # Odd number of quotes
        response_text += '"'
    
    # Fix incomplete arrays/objects
    if response_text.count('[') > response_text.count(']'):
        response_text += ']'
    if response_text.count('{') > response_text.count('}'):
        response_text += '}'
    
    # Fix mathematical notation that breaks JSON
    # Replace problematic single quotes in mathematical expressions
    response_text = re.sub(r"(\w+)\s*'", r"\1'", response_text)  # Fix derivatives like (sin x)' -> (sin x)'
    response_text = re.sub(r"'([^\"']*?)'", r"'\1'", response_text)  # Fix quoted expressions
    
    # More aggressive JSON repair for mathematical content
    # Find and fix broken string values
    import json
    try:
        # Try to parse and see where it fails
        json.loads(response_text)
        return response_text  # Already valid
    except json.JSONDecodeError as e:
        # Find the error position and try to fix it
        error_pos = e.pos
        if error_pos < len(response_text):
            # Look for the problematic area around the error
            start = max(0, error_pos - 100)
            end = min(len(response_text), error_pos + 100)
            problem_area = response_text[start:end]
            
            # Try to fix common issues in the problem area
            # Fix unescaped quotes in string values
            problem_area = re.sub(r':\s*"([^"]*?)(?="[,\}\]])', lambda m: f': "{m.group(1).replace(chr(39), chr(92) + chr(39))}"', problem_area)
            
            # Replace the problem area
            response_text = response_text[:start] + problem_area + response_text[end:]
    
    return response_text

def create_fallback_digest(response_text: str) -> Dict[str, Any]:
    """
    Create a fallback digest structure when JSON parsing fails
    """
    return {
        "course_info": {
            "title": "PDF Analysis",
            "subject": "Unknown",
            "difficulty_level": "Unknown"
        },
        "sequential_concepts": [
            {
                "name": "Content Analysis",
                "brief_description": "PDF content was processed but AI response was malformed",
                "unit": "General",
                "prerequisites": []
            }
        ],
        "key_formulas": [],
        "specific_examples": [],
        "techniques_methods": [],
        "properties_rules": [],
        "important_notes": [
            "AI response contained malformed JSON. Raw response length: " + str(len(response_text))
        ],
        "raw_response_preview": response_text[:500] + "..." if len(response_text) > 500 else response_text
    }

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
        # Clean the text (no length limit)
        cleaned_text = text.replace(chr(10), ' ').replace(chr(13), ' ')
        
        # Clean math symbols and special characters
        cleaned_text = clean_math_symbols(cleaned_text)
        
        prompt = f"""
        Analyze this PDF text and create a comprehensive concept outline optimized for building a deep knowledge graph.

        Create a JSON structure with:
        1. "course_info": title, subject, difficulty_level
        2. "sequential_concepts": array of concepts in learning order
           - Each concept: name, brief_description, unit/chapter, prerequisites
        3. "key_formulas": ALL formulas, equations, identities, rules found in text
        4. "specific_examples": concrete examples, applications, special cases
        5. "techniques_methods": specific techniques, tests, procedures mentioned
        6. "properties_rules": mathematical properties, rules, theorems
        7. "important_notes": critical insights, common mistakes, key relationships

        Instructions:
        - Extract ONLY concepts students need to study (definitions, theorems, formulas, techniques)
        - Find important mathematical concepts and methods
        - Identify key formulas, identities, and rules students learn
        - Capture essential properties and mathematical relationships
        - EXCLUDE meta-commentary, teaching advice, style preferences
        - Focus on actual mathematical content, not editorial comments

        Text to analyze:
        {cleaned_text}

        Make this maximally efficient for another AI to understand and process.
        
        IMPORTANT JSON FORMATTING RULES:
        - Use double quotes for all strings
        - Escape any single quotes in text as \'
        - Avoid mathematical notation like (sin x)' - use "derivative of sin x" instead
        - Keep descriptions concise but complete
        - Ensure all strings are properly closed
        
        Return ONLY valid JSON, no explanations.
        """
        
        response_text = await call_openrouter("x-ai/grok-4-fast", prompt, 4000)
        
        # Validate and clean JSON response
        try:
            # Try to parse the JSON
            parsed_json = json.loads(response_text)
            return parsed_json
        except json.JSONDecodeError:
            # Try to fix common JSON issues
            fixed_response = fix_json_response(response_text)
            
            try:
                parsed_json = json.loads(fixed_response)
                return parsed_json
            except json.JSONDecodeError:
                # Return a fallback structure
                return create_fallback_digest(response_text)
    
    except Exception as e:
        raise Exception(f"Failed to generate AI digest: {str(e)}")

async def generate_relationships(structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use Gemini 2.5 Flash Lite to transform AI digest into deep hierarchical knowledge graph
    """
    try:
        prompt = f"""
        Create a comprehensive, CENTRALIZED hierarchical knowledge graph from this AI digest. 
        
        CRITICAL STRUCTURE REQUIREMENT:
        - Create ONE central "root" or "mother" concept that represents the CORE FUNDAMENTAL concept
        - ALL other concepts must connect to this central concept either directly or through intermediate nodes
        - Build a hierarchical tree structure, NOT disconnected islands
        - Think: tree with a trunk (central concept) and branches (related concepts), not scattered bushes

        AI Digest: {json.dumps(structured_data, indent=2)}

        Instructions:
        1. IDENTIFY CENTRAL CONCEPT: 
           - Find the MOST FUNDAMENTAL concept that everything else builds upon
           - NOT the document title or chapter name (e.g., NOT "review of functions" or "introduction to X")
           - NOT meta descriptions (e.g., NOT "software engineering projects" or "calculus review")
           - USE the core concept itself (e.g., "function" not "review of functions", "calculus" not "introduction to calculus")
           - Think: What Wikipedia article would best represent this entire topic?
           - Examples: "function", "calculus", "programming", "linear algebra", "machine learning"
        2. CREATE ROOT NODE: Make this the central concept with empty "ins" array
        3. BUILD DEEP HIERARCHY: 
           - Create 3-5 levels of depth minimum
           - Extract EVERY meaningful concept from the digest
           - Break down complex topics into granular sub-concepts
           - Include ALL formulas, theorems, techniques, and properties as nodes
           - Don't skip concepts just because they seem minor - students need to study them!
        4. ENSURE CONNECTIVITY: Every node must have a path back to the root concept
        5. USE MEANINGFUL RELATIONSHIPS: "outs" should list direct logical dependencies or related concepts
        
        DEPTH GUIDELINES:
        - Level 1 (Root): Central concept (e.g., "function")
        - Level 2: Major categories (e.g., "polynomial function", "trigonometric function", "function properties")
        - Level 3: Specific types (e.g., "quadratic function", "sine function", "domain and range")
        - Level 4: Detailed concepts (e.g., "discriminant", "amplitude", "vertical line test")
        - Level 5+: Formulas, theorems, techniques (e.g., "quadratic formula", "pythagorean identity", "completing the square")

        HIERARCHY EXAMPLE (Good):
        Root: "function" (NOT "review of functions for calculus")
        ├─→ "domain and range" → "function notation" → "function composition"
        ├─→ "types of functions" → "linear function" → "slope"
        └─→ "function properties" → "continuity" → "limits"

        Another Good Example:
        Root: "software engineering" (NOT "john's software projects")
        ├─→ "programming fundamentals" → "python programming" → "object oriented programming"
        ├─→ "robotics" → "sensor control" → "motor optimization"
        └─→ "web development" → "frontend frameworks" → "react development"

        BAD EXAMPLES (Avoid):
        - Root: "review of functions for calculus" ❌ (too meta, use "function" instead)
        - Root: "introduction to linear algebra" ❌ (use "linear algebra" instead)
        - Root: "calculus review" ❌ (use "calculus" instead)
        - Disconnected islands: "python programming", "sensor control", "react development" (no connection) ❌

        NAMING RULES (CRITICAL - FOLLOW EXACTLY):
        1. ALL NAMES MUST BE LOWERCASE
        2. NEVER USE FORMULAS OR NOTATION: "quadratic function" not "f(x) = x²"
        3. USE CONCEPTUAL NAMES: "pythagorean identity" not "sin²(x) + cos²(x) = 1"
        4. BE CONSISTENT: "trigonometric function" not "trig function"
        5. USE SINGULAR FORMS: "function" not "functions"
        6. NO ABBREVIATIONS: "vertical line test" not "VLT"
        7. DESCRIPTIVE NAMES: Make them clear and specific

        WHAT TO INCLUDE (Be Comprehensive):
        - ALL core concepts, definitions, theorems from the digest
        - EVERY technique, method, and procedure mentioned
        - ALL formulas, identities, and rules (named conceptually, not as formulas)
        - Properties, tests, and conditions
        - Types and classifications (e.g., "linear function", "exponential function")
        - Specific examples if they represent distinct concept types
        - Skills, competencies, and problem-solving strategies
        - Domain-specific terminology and notation concepts
        
        IMPORTANT: If the digest mentions 20+ concepts, your graph should have 20+ nodes (excluding very basic prerequisites)

        WHAT TO EXCLUDE (Be Selective):
        - Pure meta-commentary without substance ("emphasis on...", "note that...")
        - Teaching style advice ("students should practice...")
        - Document structure references ("in this chapter...", "as mentioned earlier...")
        - Redundant variations of the same concept (pick the most standard name)
        
        QUALITY CHECK:
        - If you have fewer than 15 nodes for a typical chapter/document, you're probably being too conservative
        - Each concept in "sequential_concepts", "key_formulas", "techniques_methods" should become a node
        - Break down compound concepts into multiple connected nodes

        Create JSON with:
        1. "nodes": array of concept nodes
           - Root node: {{"name": "central_concept", "ins": [], "outs": ["major_topic_1", "major_topic_2", ...]}}
           - Other nodes: {{"name": "concept_name", "ins": ["prerequisite"], "outs": ["dependent_concepts"]}}
        2. "graph_metadata": {{"title": "course/document title", "subject": "subject", "total_concepts": number, "depth_levels": number}}

        VERIFICATION CHECKLIST:
        - ✓ EVERY node (except root) has at least one "ins" connection
        - ✓ There's a path from the root to every node (no orphaned nodes)
        - ✓ The root node has EMPTY ins array and multiple outs (3+ major branches)
        - ✓ Depth is 3-5+ levels for comprehensive content
        - ✓ Total node count matches the richness of the digest (15+ nodes minimum for typical content)
        - ✓ Each item in "sequential_concepts", "key_formulas", "techniques_methods" is represented
        - ✓ No meaningless filler concepts - every node is study-worthy
        - ✓ No redundant concepts with different names

        FINAL REMINDER: 
        Create a DEEP, COMPREHENSIVE graph. Don't be conservative. Students need ALL concepts to study effectively.
        Better to have 40 meaningful nodes than 10 overly-broad ones.

        Return ONLY valid JSON, no explanations.
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
            response_json = response.json()
            return response_json["choices"][0]["message"]["content"]
        else:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
    
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
