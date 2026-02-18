from fastapi import APIRouter, HTTPException
from services.llm.audio_generator import generate_audio
from models.graph import AudioRequest, AudioResponse

router = APIRouter()

@router.post("/audio", response_model=AudioResponse)
async def create_audio(request: AudioRequest):
    """generate tts audio from script"""
    try:
        audio_url = await generate_audio(request.script_text)
        return AudioResponse(audio_url=audio_url, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"audio error: {str(e)}")
