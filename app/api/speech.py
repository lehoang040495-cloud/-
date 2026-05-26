"""
Speech API - TTS and STT endpoints
"""
import os
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.schemas import TTSRequest, STTResponse
from app.services.tts_service import tts_service
from app.services.stt_service import stt_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/speech", tags=["Speech"])


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """Convert text to speech audio"""
    audio_url = await tts_service.synthesize(
        text=request.text,
        voice=request.voice,
        rate=request.rate,
    )
    if not audio_url:
        raise HTTPException(500, "TTS synthesis failed")
    return {"audio_url": audio_url}


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(file: UploadFile = File(...)):
    """Convert speech audio to text"""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".wav", ".mp3", ".ogg", ".flac", ".m4a", ".webm"):
        raise HTTPException(400, f"Unsupported audio format: {ext}")

    audio_bytes = await file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(400, "Empty audio file")

    result = await stt_service.transcribe_from_bytes(audio_bytes, suffix=ext)
    return STTResponse(**result)


@router.get("/voices")
async def list_voices(language: str = "zh"):
    """List available TTS voices"""
    voices = await tts_service.get_voices(language)
    return {"voices": voices}


@router.get("/audio/{file_name}")
async def serve_audio(file_name: str):
    """Serve generated audio files"""
    audio_path = os.path.abspath(os.path.join("./data/audio", file_name))
    if not os.path.exists(audio_path):
        raise HTTPException(404, "Audio file not found")
    return FileResponse(audio_path, media_type="audio/mpeg")
