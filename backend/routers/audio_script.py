from fastapi import APIRouter, HTTPException
from services.ai_service import generate_audio_script
from models.graph import AudioScriptRequest, AudioScriptResponse

router = APIRouter()

@router.post("/audio-script", response_model=AudioScriptResponse)
async def generate_podcast_script(request: AudioScriptRequest):
    """
    Use GPT-4o Mini to generate audio script for ElevenLabs
    """
    try:
        script = await generate_audio_script(request.graph_data)
        
        return AudioScriptResponse(
            script_text=script,
            success=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio script: {str(e)}")
