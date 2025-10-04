from fastapi import APIRouter, HTTPException
from services.ai_service import generate_audio
from models.graph import AudioRequest, AudioResponse

router = APIRouter()

@router.post("/audio", response_model=AudioResponse)
async def generate_podcast_audio(request: AudioRequest):
    """
    Use ElevenLabs to generate audio from script
    """
    try:
        audio_url = await generate_audio(request.script_text)
        
        return AudioResponse(
            audio_url=audio_url,
            success=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")
