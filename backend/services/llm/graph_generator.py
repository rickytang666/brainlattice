import json
from typing import Dict, Any
from .providers import get_gemini_client

async def generate_relationships(structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """transform digest into hierarchical knowledge graph"""
    gemini_client = get_gemini_client()
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
        raise Exception(f"failed to generate relationships: {str(e)}")
