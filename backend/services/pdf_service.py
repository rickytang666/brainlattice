import pymupdf.layout
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
    """extract and clean markdown from pdf bytes using layout analysis"""
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
