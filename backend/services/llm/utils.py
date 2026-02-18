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
