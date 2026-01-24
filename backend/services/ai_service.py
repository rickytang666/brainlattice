from dotenv import load_dotenv
import os
import json
import re
from google import genai
import requests
from fish_audio_sdk import Session, TTSRequest
from io import BytesIO

from typing import Dict, Any, Optional

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
        1. "course_info": 
           - "title": A descriptive yet concise title that captures the CORE topic (e.g., "Functions and Trigonometry", "Linear Algebra Fundamentals", "Intro to Machine Learning"). NOT generic like "PDF Analysis" or verbose chapter names.
           - "subject": The academic subject (e.g., "Mathematics", "Computer Science", "Physics")
           - "difficulty_level": Basic, Intermediate, or Advanced
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
        - For the title: Be specific about what's being taught, not how it's being taught

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

async def generate_overview(digest_data: Dict[str, Any], graph_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Use OpenRouter (Grok 4 Fast) to generate study guide overview in Markdown format from AI digest
    """
    try:
        # Extract metadata from digest
        course_info = digest_data.get('course_info', {})
        sequential_concepts = digest_data.get('sequential_concepts', [])
        key_formulas = digest_data.get('key_formulas', [])
        specific_examples = digest_data.get('specific_examples', [])
        techniques_methods = digest_data.get('techniques_methods', [])
        properties_rules = digest_data.get('properties_rules', [])
        important_notes = digest_data.get('important_notes', [])
        
        # Get graph metadata if available
        graph_metadata = graph_data.get('graph_metadata', {}) if graph_data else {}
        
        prompt = f"""
        You're helping your best friend crush their exam. They need a NO-BS overview that cuts straight to what matters.

        COURSE: {course_info.get('title', 'Study Guide')} ({course_info.get('subject', 'Unknown')})
        DIFFICULTY: {course_info.get('difficulty_level', 'Unknown')}

        CONCEPTS TO MASTER:
        {json.dumps(sequential_concepts[:20], indent=2)}
        
        FORMULAS TO MEMORIZE:
        {json.dumps(key_formulas[:15], indent=2) if key_formulas else "None"}
        
        TECHNIQUES THAT ACTUALLY WORK:
        {json.dumps(techniques_methods[:10], indent=2) if techniques_methods else "None"}
        
        RULES & THEOREMS:
        {json.dumps(properties_rules[:10], indent=2) if properties_rules else "None"}
        
        EXAMPLES THAT MATTER:
        {json.dumps(specific_examples[:8], indent=2) if specific_examples else "None"}
        
        GOTCHAS TO AVOID:
        {json.dumps(important_notes[:8], indent=2) if important_notes else "None"}

        Create a CRUSH-THE-EXAM overview with this structure:

        # {course_info.get('title', 'Study Guide')} - The Stuff That Actually Matters

        ## 🎯 Core Concepts (Master These = You're Golden)
        List ONLY the essential concepts. Be direct:
        - **Concept Name**: What it is, why it matters, when to use it
        - No fluff, just the facts

        ## 📐 Formulas You Need (Stop Forgetting These)
        List the actual formulas with:
        - Formula: $actual_formula_here$
        - When to use: One line explanation
        - Watch out for: Common mistakes

        ## 🔧 Problem-Solving Techniques
        Step-by-step methods that actually work:
        - **Technique Name**: Step 1, Step 2, Step 3
        - Pro tip: One insider tip

        ## ⚡ Quick Rules & Theorems
        The rules that show up on EVERY exam:
        - **Rule Name**: What it says + when to use it

        ## 💡 Exam Hacks & Gotchas
        Stuff that trips people up:
        - Common mistakes to avoid
        - Tricks that save time
        - What professors love to test

        ## 🚀 Study Order (Don't Study Random Stuff)
        Master in this order:
        1. **Foundation**: [List 3-4 core concepts]
        2. **Build Up**: [List 4-5 intermediate concepts]  
        3. **Advanced**: [List 2-3 final concepts]

        ## 📋 Last-Minute Cheat Sheet
        The absolute essentials you need memorized:
        - Top 5 formulas: $formula1$, $formula2$, etc.
        - Top 3 concepts: Brief definitions
        - Top 3 rules: Quick statements

        **TONE**: You're their smart friend who already aced this class. Be encouraging but direct. Use "you" and "your". No corporate speak. Tease them a little but make them feel confident they'll crush it.

        **FORMATTING**: 
        - Use **bold** for concept/formula names
        - Use $math$ for formulas
        - Keep it scannable
        - No unnecessary sections
        - Be concise but complete

        Generate the overview now:
        """
        
        return await call_openrouter("x-ai/grok-4-fast", prompt, 3500)
    
    except Exception as e:
        raise Exception(f"Failed to generate overview: {str(e)}")

async def generate_audio_script(digest_data: Dict[str, Any], graph_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Use OpenRouter (Grok 4 Fast) to generate audio script for podcast/newsletter from AI digest
    """
    try:
        # Extract data from digest
        course_info = digest_data.get('course_info', {})
        sequential_concepts = digest_data.get('sequential_concepts', [])
        key_formulas = digest_data.get('key_formulas', [])
        techniques_methods = digest_data.get('techniques_methods', [])
        important_notes = digest_data.get('important_notes', [])
        
        prompt = f"""
        Create a sharp, concise audio script (1-2 minutes MAX) based on this AI digest.
        
        COURSE INFO:
        - Title: {course_info.get('title', 'Course Overview')}
        - Subject: {course_info.get('subject', 'Unknown')}
        - Difficulty: {course_info.get('difficulty_level', 'Unknown')}
        
        KEY CONCEPTS (first 12):
        {json.dumps(sequential_concepts[:12], indent=2)}
        
        KEY FORMULAS (first 6):
        {json.dumps(key_formulas[:6], indent=2) if key_formulas else "None"}
        
        TECHNIQUES (first 5):
        {json.dumps(techniques_methods[:5], indent=2) if techniques_methods else "None"}
        
        IMPORTANT NOTES (first 4):
        {json.dumps(important_notes[:4], indent=2) if important_notes else "None"}
        
        Write like a smart buddy explaining this over coffee. Direct, casual, zero BS.
        
        STRUCTURE (1-2 minutes total):
        1. **Quick Intro** (5 seconds)
           - One punchy line. Jump right in.
           - "Alright, [topic]..." or "Here's the deal with [topic]..."
        
        2. **Core Ideas** (45-60 seconds)
           - Hit the 3-5 most critical concepts
           - Each concept: one sharp sentence, maybe two
           - 10-15 seconds per concept MAX
           - How they connect (one line)
        
        3. **Key Takeaway** (10-15 seconds)
           - One main thing to lock in
           - Quick study tip if relevant
           - Done. No outro needed.
        
        STYLE - CRITICAL (BRO/BUDDY VIBE):
        - **NO YAPPING** - cut all filler, every word counts
        - Casual but sharp - like texting a smart friend
        - Use contractions: "it's", "you're", "here's", "that's"
        - Direct statements: "This does X" not "So this is kinda doing X"
        - Confident, no hedging: "This is" not "This might be" or "This could be"
        - Short, punchy sentences
        - Occasional casual interjections: "Look", "Real talk", "Here's the thing"
        - Get in, drop knowledge, get out
        
        MATH & SYMBOLS - CRITICAL FOR AUDIO:
        - **USE PLAIN ENGLISH** - this is for text-to-speech!
        - Write "sine" not "sin", "cosine" not "cos", "tangent" not "tan"
        - Write "f of g of x" not "f(g(x))"
        - Write "x squared" not "x²" or "x^2"
        - Write "the integral of" not "∫"
        - Write "pi" not "π", "theta" not "θ"
        - Write "equals" not "=", "plus" not "+"
        - NO mathematical notation or symbols - they sound terrible when read aloud
        - Example: "The derivative of sine x equals cosine x" NOT "d/dx sin(x) = cos(x)"
        
        EXAMPLES OF GOOD VS BAD:
        ❌ BAD: "So, let's talk about derivatives. Now, derivatives are really interesting because they help us understand how things change over time, and that's super important in calculus."
        ✅ GOOD: "Alright, derivatives. They measure rate of change. How fast something's moving? That's your derivative."
        
        ❌ BAD: "And another thing I wanted to mention is that when you're working with these formulas..."
        ✅ GOOD: "Here's the thing: nail the formulas first, everything else follows."
        
        ❌ BAD: "I think it's important to understand that this concept is fundamental..."
        ✅ GOOD: "This is the core concept. Everything builds from here."
        
        ❌ BAD (MATH): "The chain rule is d/dx f(g(x)) = f'(g(x)) · g'(x)"
        ✅ GOOD (MATH): "Chain rule: derivative of f of g of x equals f prime of g of x times g prime of x"
        
        ❌ BAD (MATH): "sin²(x) + cos²(x) = 1"
        ✅ GOOD (MATH): "Sine squared x plus cosine squared x equals one"
        
        AVOID:
        - Any intro longer than 5 words
        - Filler phrases: "basically", "essentially", "kind of", "sort of", "you know", "so", "well"
        - Hedge words: "maybe", "possibly", "might", "could be", "I think"
        - Long closings or motivational speeches
        - Repeating yourself
        - Meta-commentary: "let's talk about", "we're going to cover", "as I mentioned"
        - Formality: "one must understand", "it is important to note"
        
        TARGET: 150-250 words MAX (1-2 minutes when spoken)
        
        Generate the script now - casual, sharp, buddy vibe, ZERO yapping:
        """
        
        return await call_openrouter("x-ai/grok-4-fast", prompt, 1500)
    
    except Exception as e:
        raise Exception(f"Failed to generate audio script: {str(e)}")

async def generate_audio(script_text: str) -> str:
    """
    Use Fish Audio to generate audio from script and return as base64 data URL
    """
    try:
        # Validate inputs and environment
        if not script_text or not script_text.strip():
            raise Exception("script_text is empty; cannot generate audio")

        api_key = os.getenv("FISH_AUDIO_API_KEY")
        if not api_key:
            raise Exception(
                "FISH_AUDIO_API_KEY is not set. Set it locally and in Cloud Run env vars."
            )

        # Initialize Fish Audio session with API key
        session = Session(api_key)

        # Generate audio using Fish Audio TTS
        # Using a standard male voice ID as reference (can be customized)
        # Assuming we want a high quality English output
        
        audio_bytes = b""
        for chunk in session.tts(TTSRequest(
            reference_id="4f5c00a6-96d5-4137-a166-51d08e82d3b2", # Standard male voice
            text=script_text,
            format="mp3"
        )):
            audio_bytes += chunk
        
        # Convert to base64 for transmission
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Return data URL that can be used directly in audio player
        return f"data:audio/mpeg;base64,{audio_base64}"

    except Exception as e:
        # Surface upstream error details to help diagnose (e.g., quota, auth)
        raise Exception(f"Failed to generate audio: {e}")

def fix_latex_json_escapes(text: str) -> str:
    """
    Fix LaTeX escape sequences that break JSON parsing
    """
    # Replace single backslashes that aren't already escaped
    # This is a more conservative approach
    import re
    
    # Fix unescaped backslashes in LaTeX commands (but not already escaped ones)
    # Pattern: \ followed by letters, but not \\ (already escaped)
    text = re.sub(r'(?<!\\)\\([a-zA-Z]+)', r'\\\\\1', text)
    
    return text

async def generate_concept_insights(concept_name: str, context_data: Optional[dict] = None) -> dict:
    """
    Use Gemini 2.0 Flash Lite to generate concise insights about a concept
    """
    try:
        # Build context information if available
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

        # Clean response text - remove markdown code blocks if present
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        # Fix LaTeX escape sequences for JSON
        response_text = fix_latex_json_escapes(response_text)

        # Parse JSON response with better error handling
        try:
            insights = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Response text: {response_text}")
            # Try to fix common JSON issues
            response_text = fix_json_response(response_text)
            insights = json.loads(response_text)
        
        return {
            "concept_name": concept_name,
            "overview": insights.get("overview", ""),
            "related_concepts": insights.get("related_concepts", []),
            "important_formulas": insights.get("important_formulas", []),
            "key_theorems": insights.get("key_theorems", []),
            "success": True
        }

    except Exception as e:
        return {
            "concept_name": concept_name,
            "overview": "",
            "related_concepts": [],
            "important_formulas": [],
            "key_theorems": [],
            "success": False,
            "error": str(e)
        }
