import pypdf
import io

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """extract text from pdf bytes via pypdf"""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = pypdf.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        raise Exception(f"pdf extraction failed: {str(e)}")
