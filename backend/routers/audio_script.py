from fastapi import APIRouter, HTTPException
from services.ai_service import generate_audio_script
from models.graph import AudioScriptRequest, AudioScriptResponse

router = APIRouter()

@router.post("/audio-script", response_model=AudioScriptResponse)
async def generate_podcast_script(request: AudioScriptRequest):
    """
    Use OpenRouter (Grok 4 Fast) to generate audio script for ElevenLabs from AI digest data
    """
    try:
        # Use digest_data (primary) or fallback to graph_data for backward compatibility
        data_to_use = request.digest_data if request.digest_data else request.graph_data
        script = await generate_audio_script(data_to_use, request.graph_data)
        
        return AudioScriptResponse(
            script_text=script,
            success=True
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio script: {str(e)}")
