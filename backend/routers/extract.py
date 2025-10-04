from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_service import extract_text_from_pdf
from models.pdf import PDFExtractionResponse

router = APIRouter()

@router.post("/extract", response_model=PDFExtractionResponse)
async def extract_pdf_text(file: UploadFile = File(...)):
    """
    Extract text from uploaded PDF file using pypdf
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract text using pypdf
        extracted_text = extract_text_from_pdf(content)
        
        return PDFExtractionResponse(
            filename=file.filename,
            text=extracted_text,
            success=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")
