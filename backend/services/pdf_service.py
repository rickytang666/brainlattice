import pymupdf4llm
import fitz
import io
import re

def clean_markdown(text: str) -> str:
    """post-process markdown to fix common extraction issues"""
    # 1. fix hyphenated words at line breaks (e.g. "for-\n mer" -> "former")
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    
    # 2. fix multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # 3. fix excessive newlines (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 4. fix broken bullet points (sometimes come out as "• " instead of "- ")
    text = text.replace('• ', '- ')
    
    # 5. remove replacement characters
    text = text.replace('\ufffd', '')
    
    return text.strip()

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """extract and clean markdown from pdf bytes"""
    try:
        pdf_file = io.BytesIO(pdf_content)
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        
        # convert to markdown
        md_text = pymupdf4llm.to_markdown(doc)
        
        # post-process
        cleaned_text = clean_markdown(md_text)
        
        return cleaned_text
    except Exception as e:
        raise Exception(f"pdf extraction failed: {str(e)}")
