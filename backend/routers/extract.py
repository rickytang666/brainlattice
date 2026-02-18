from fastapi import APIRouter, UploadFile, File, HTTPException
from services.pdf_service import extract_text_from_pdf
from models.pdf import PDFExtractionResponse

router = APIRouter()

@router.post("/extract", response_model=PDFExtractionResponse)
async def extract_pdf_text(file: UploadFile = File(...)):
    """extract text from uploaded pdf"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="file must be a pdf")
    
    try:
        content = await file.read()
        extracted_text = extract_text_from_pdf(content)
        
        return PDFExtractionResponse(
            filename=file.filename,
            text=extracted_text,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"extraction error: {str(e)}")
