import pymupdf4llm
import fitz
import io

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """extract markdown from pdf bytes via pymupdf4llm"""
    try:
        # pymupdf4llm expects a fitz.Document
        pdf_file = io.BytesIO(pdf_content)
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        
        # convert to markdown
        md_text = pymupdf4llm.to_markdown(doc)
        
        return md_text.strip()
    except Exception as e:
        raise Exception(f"pdf extraction failed: {str(e)}")
