import re
import json
from typing import Dict, Any

def clean_math_symbols(text: str) -> str:
    """clean math symbols and special chars"""
    # math symbol mappings
    replacements = {
        'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon',
        'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ι': 'iota', 'κ': 'kappa',
        'λ': 'lambda', 'μ': 'mu', 'ν': 'nu', 'ξ': 'xi', 'ο': 'omicron',
        'π': 'pi', 'ρ': 'rho', 'σ': 'sigma', 'τ': 'tau', 'υ': 'upsilon',
        'φ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',
        '∑': 'sum', '∏': 'product', '∫': 'integral', '∂': 'partial',
        '∇': 'nabla', '∞': 'infinity', '±': 'plus-minus', '×': 'times', 
        '÷': 'divided by', '√': 'square root', '≤': 'less than or equal', 
        '≥': 'greater than or equal', '≠': 'not equal'
    }
    
    for symbol, replacement in replacements.items():
        text = text.replace(symbol, replacement)
    
    # remove non-printable
    text = ''.join(char if char.isprintable() or char.isspace() else ' ' for char in text)
    # collapse spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def fix_json_response(response_text: str) -> str:
    """fix common json issues in ai responses"""
    # find first brace
    start_idx = response_text.find('{')
    if start_idx > 0:
        response_text = response_text[start_idx:]
    
    # find last complete brace
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
    
    if last_complete_idx > 0:
        response_text = response_text[:last_complete_idx + 1]
    else:
        end_idx = response_text.rfind('}')
        if end_idx > 0:
            response_text = response_text[:end_idx + 1]
    
    # cleanup trailing commas and quotes
    response_text = re.sub(r',(\s*[}\]])', r'\1', response_text)
    if response_text.count('"') % 2 == 1:
        response_text += '"'
    if response_text.count('[') > response_text.count(']'):
        response_text += ']'
    if response_text.count('{') > response_text.count('}'):
        response_text += '}'
    
    return response_text

def create_fallback_digest(response_text: str) -> Dict[str, Any]:
    """fallback structure for failed parsing"""
    return {
        "course_info": {"title": "pdf analysis", "subject": "unknown"},
        "sequential_concepts": [{"name": "content analysis", "brief_description": "malformed ai response"}],
        "important_notes": ["parsing failed"]
    }

def fix_latex_json_escapes(text: str) -> str:
    """fix latex backslashes for json"""
    return re.sub(r'(?<!\\)\\([a-zA-Z]+)', r'\\\\\1', text)


def repair_note_markdown(text: str) -> str:
    """
    repair common llm markdown issues in study notes.
    safe, non-destructive fixes.
    """
    if not text or not text.strip():
        return text

    # unwrap if llm wrapped entire output in ```markdown or ``` code block
    text = text.strip()
    for opener in (r'```\s*markdown\s*\n', r'```\s*md\s*\n', r'```\s*\n'):
        if re.match(opener, text, re.IGNORECASE):
            text = re.sub(opener, '', text, count=1, flags=re.IGNORECASE)
            break
    if text.endswith('```'):
        text = text[:-3].rstrip()

    # normalize [text](text) -> [[text]] so frontend link parsing works
    text = re.sub(r'\[([^\]]+)\]\(\1\)', r'[[\1]]', text)

    # convert html superscript/subscript to latex (e.g. r<sup>3</sup> -> $r^3$, E=mc<sup>2</sup> -> $E=mc^2$)
    # base is any non-whitespace, non-< chars immediately before the tag
    text = re.sub(r'([^<\s]*)<sup>([^<]+)</sup>', r'$\1^{\2}$', text)
    text = re.sub(r'([^<\s]*)<sub>([^<]+)</sub>', r'$\1_{\2}$', text)

    # fix isolated/unpaired delimiters that break rendering
    # odd $ (latex) - remove last stray $
    if text.count('$') % 2 == 1:
        text = text.rsplit('$', 1)[0] + text.rsplit('$', 1)[1]
    # odd number of ``` - remove trailing unclosed fence
    fence_count = text.count('```')
    if fence_count % 2 == 1:
        text = text.rsplit('```', 1)[0] + text.rsplit('```', 1)[1]
    # odd ` (inline code) - remove last stray backtick
    if text.count('`') % 2 == 1:
        text = text.rsplit('`', 1)[0] + text.rsplit('`', 1)[1]
    # odd ** (bold) - remove last stray **
    if text.count('**') % 2 == 1:
        parts = text.rsplit('**', 1)
        text = parts[0] + parts[1]

    # normalize excessive newlines (keep max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # fix list items missing space after marker: "-word" or "*word" -> "- word" / "* word"
    text = re.sub(r'^(\s*)([-*])([^\s*\-])', r'\1\2 \3', text, flags=re.MULTILINE)

    # fix numbered list missing space: "1.word" -> "1. word"
    text = re.sub(r'^(\s*)(\d+)\.([^\s\d])', r'\1\2. \3', text, flags=re.MULTILINE)

    # trim each line, remove leading/trailing blank lines
    lines = [line.rstrip() for line in text.split('\n')]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    return '\n'.join(lines)
