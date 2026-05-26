"""
STT Service - faster-whisper for speech-to-text
"""
import os
import logging
import tempfile
import asyncio
from functools import partial

from app.config import settings

logger = logging.getLogger(__name__)


class STTService:
    def __init__(self):
        self.model = None
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE

    def _ensure_model(self):
        if self.model is None:
            from faster_whisper import WhisperModel
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type="int8" if self.device == "cpu" else "float16",
            )

    def _transcribe_sync(self, audio_file_path: str, language: str = "zh") -> dict:
        """Synchronous transcription - run in thread pool"""
        self._ensure_model()
        try:
            segments, info = self.model.transcribe(
                audio_file_path,
                language=language,
                beam_size=5,
            )

            text_parts = []
            total_confidence = 0.0
            count = 0

            for segment in segments:
                text_parts.append(segment.text.strip())
                total_confidence += segment.avg_logprob
                count += 1

            text = " ".join(text_parts)
            avg_confidence = min(max((total_confidence / count + 1) * 50, 0), 100) if count > 0 else 0.0

            return {"text": text, "confidence": round(avg_confidence, 2)}
        except Exception as e:
            logger.error(f"STT transcription failed: {e}")
            return {"text": "", "confidence": 0.0}

    async def transcribe(self, audio_file_path: str, language: str = "zh") -> dict:
        """Async wrapper - runs transcription in thread pool to avoid blocking"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(self._transcribe_sync, audio_file_path, language)
        )

    async def transcribe_from_bytes(self, audio_bytes: bytes, language: str = "zh", suffix: str = ".wav") -> dict:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            return await self.transcribe(tmp_path, language)
        finally:
            os.unlink(tmp_path)


stt_service = STTService()
