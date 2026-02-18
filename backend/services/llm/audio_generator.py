import os
import base64
import json
from typing import Dict, Any, Optional
from fish_audio_sdk import Session, TTSRequest
from .providers import call_openrouter
from core.config import get_settings

async def generate_audio_script(digest_data: Dict[str, Any], graph_data: Optional[Dict[str, Any]] = None) -> str:
    """generate concise audio script from digest"""
    try:
        # extract metadata
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
        raise Exception(f"failed to generate audio script: {str(e)}")

async def generate_audio(script_text: str) -> str:
    """generate audio via fish audio tts"""
    try:
        if not script_text or not script_text.strip():
            raise Exception("script_text is empty")

        settings = get_settings()
        api_key = settings.FISH_AUDIO_API_KEY
        if not api_key:
            raise Exception("fish audio key not set")

        session = Session(api_key)
        
        audio_bytes = b""
        for chunk in session.tts(TTSRequest(
            reference_id="4f5c00a6-96d5-4137-a166-51d08e82d3b2",
            text=script_text,
            format="mp3"
        )):
            audio_bytes += chunk
        
        # return as base64 data url
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        return f"data:audio/mpeg;base64,{audio_base64}"

    except Exception as e:
        raise Exception(f"audio generation failed: {e}")
