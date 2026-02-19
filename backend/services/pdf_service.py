import pymupdf4llm
import fitz
import io
import re
import logging

logger = logging.getLogger(__name__)

def clean_markdown(text: str) -> str:
    """post-process markdown to fix common extraction issues"""
    # fix hyphenated words at line breaks (e.g. "for-\n mer" -> "former")
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    
    # normalize multiple spaces
    text = re.sub(r' +', ' ', text)
    
    # limit excessive newlines (max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # normalize bullet points (• -> -)
    text = text.replace('• ', '- ')
    
    # remove replacement characters
    text = text.replace('\ufffd', '')
    
    return text.strip()

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """extract and clean markdown from pdf bytes"""
    pdf_file = io.BytesIO(pdf_content)
    doc = fitz.open(stream=pdf_file, filetype="pdf")
    md_text = pymupdf4llm.to_markdown(doc)
    return clean_markdown(md_text)

class PDFService:
    """service wrapper for pdf extraction"""

    def extract_content(self, file_path: str) -> str:
        """extract markdown from pdf file at path"""
        with open(file_path, "rb") as f:
            return extract_text_from_pdf(f.read())
