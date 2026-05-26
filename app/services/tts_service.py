"""
TTS Service - Edge-TTS for text-to-speech synthesis
"""
import os
import uuid
import logging
import edge_tts
from app.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    def __init__(self):
        self.output_dir = os.path.abspath("./data/audio")
        os.makedirs(self.output_dir, exist_ok=True)
        self.default_voice = settings.TTS_VOICE
        self.default_rate = settings.TTS_RATE

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        rate: str = None,
    ) -> str:
        """
        Synthesize text to speech, return audio file path.
        Returns relative URL path for serving.
        """
        voice = voice or self.default_voice
        rate = rate or self.default_rate

        file_name = f"{uuid.uuid4().hex}.mp3"
        file_path = os.path.join(self.output_dir, file_name)

        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(file_path)
            return f"/audio/{file_name}"
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            return ""

    async def get_voices(self, language: str = "zh") -> list[dict]:
        """List available voices"""
        try:
            voices = await edge_tts.list_voices()
            filtered = [v for v in voices if v["Locale"].startswith(language)]
            return [
                {
                    "name": v["ShortName"],
                    "display_name": v["FriendlyName"],
                    "gender": v["Gender"],
                }
                for v in filtered
            ]
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return []


tts_service = TTSService()
