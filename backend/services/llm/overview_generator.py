import json
from typing import Dict, Any, Optional
from .providers import call_openrouter

async def generate_overview(digest_data: Dict[str, Any], graph_data: Optional[Dict[str, Any]] = None) -> str:
    """generate study guide overview in markdown"""
    try:
        # extract metadata
        course_info = digest_data.get('course_info', {})
        sequential_concepts = digest_data.get('sequential_concepts', [])
        key_formulas = digest_data.get('key_formulas', [])
        specific_examples = digest_data.get('specific_examples', [])
        techniques_methods = digest_data.get('techniques_methods', [])
        properties_rules = digest_data.get('properties_rules', [])
        important_notes = digest_data.get('important_notes', [])
        
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
        raise Exception(f"failed to generate overview: {str(e)}")
