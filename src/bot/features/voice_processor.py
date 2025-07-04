"""
Voice message processing for transcription using OpenAI Whisper API.

This module handles voice message transcription by:
1. Downloading voice files from Telegram
2. Converting them to supported formats if needed
3. Transcribing using OpenAI Whisper API
4. Cleaning up temporary files
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple

import aiofiles
import openai
from telegram import Voice

from ...config.settings import Settings
from ...security.validators import SecurityValidator

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Handles voice message transcription using OpenAI Whisper."""

    def __init__(self, config: Settings, security: SecurityValidator):
        """Initialize voice processor with configuration and security validator."""
        self.config = config
        self.security = security
        # Extract the actual string value from SecretStr if needed
        api_key = (
            config.openai_api_key.get_secret_value() if config.openai_api_key else None
        )
        if api_key:
            logger.info(f"Initializing OpenAI client with API key: {api_key[:10]}...")
        else:
            logger.warning("No OpenAI API key provided")
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.temp_dir = Path(tempfile.gettempdir()) / "claude_bot_voice"
        self.temp_dir.mkdir(exist_ok=True)

    async def process_voice_message(
        self, voice: Voice, user_id: int
    ) -> Tuple[str, float]:
        """
        Process a voice message and return transcribed text and estimated cost.

        Args:
            voice: Telegram Voice object
            user_id: User ID for security validation

        Returns:
            Tuple of (transcribed_text, estimated_cost)

        Raises:
            ValueError: If voice message is invalid or too long
            RuntimeError: If transcription fails
        """
        # Validate voice message
        self._validate_voice_message(voice)

        # Generate unique filename
        temp_file = self.temp_dir / f"voice_{user_id}_{voice.file_id}.ogg"

        try:
            # Download voice file
            await self._download_voice_file(voice, temp_file)

            # Transcribe audio
            transcript = await self._transcribe_audio(temp_file)

            # Calculate cost
            cost = self._calculate_transcription_cost(voice.duration, voice.file_size)

            logger.info(
                "Voice message transcribed successfully",
                extra={
                    "user_id": user_id,
                    "duration": voice.duration,
                    "file_size": voice.file_size,
                    "transcript_length": len(transcript),
                    "cost": cost,
                },
            )

            return transcript, cost

        except Exception as e:
            logger.error(
                "Failed to process voice message",
                extra={
                    "user_id": user_id,
                    "error": str(e),
                    "voice_duration": voice.duration,
                    "voice_file_size": voice.file_size,
                },
            )
            raise RuntimeError(f"Voice transcription failed: {str(e)}") from e

        finally:
            # Clean up temporary file
            await self._cleanup_temp_file(temp_file)

    def _validate_voice_message(self, voice: Voice) -> None:
        """Validate voice message constraints."""
        if not self.config.voice_enabled:
            raise ValueError("Voice message processing is disabled")

        if voice.duration > self.config.voice_max_duration:
            raise ValueError(
                f"Voice message too long: {voice.duration}s "
                f"(max: {self.config.voice_max_duration}s)"
            )

        if voice.file_size and voice.file_size > self.config.voice_max_file_size:
            raise ValueError(
                f"Voice file too large: {voice.file_size} bytes "
                f"(max: {self.config.voice_max_file_size} bytes)"
            )

    async def _download_voice_file(self, voice: Voice, file_path: Path) -> None:
        """Download voice file from Telegram."""
        try:
            # Get file from Telegram
            file = await voice.get_file()

            # Download to temporary file
            await file.download_to_drive(str(file_path))

            logger.debug(
                "Voice file downloaded",
                extra={
                    "file_id": voice.file_id,
                    "file_path": str(file_path),
                    "file_size": voice.file_size,
                },
            )

        except Exception as e:
            raise RuntimeError(f"Failed to download voice file: {str(e)}") from e

    async def _transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe audio file using OpenAI Whisper."""
        try:
            async with aiofiles.open(audio_path, "rb") as audio_file:
                audio_data = await audio_file.read()

            # Create a temporary file-like object for OpenAI API
            import io

            audio_buffer = io.BytesIO(audio_data)
            audio_buffer.name = "voice.ogg"  # OpenAI needs a filename

            # Transcribe using OpenAI Whisper
            transcript = await self.client.audio.transcriptions.create(
                model=self.config.whisper_model,
                file=audio_buffer,
                language=self.config.whisper_language,
                response_format="text",
                temperature=0.0,  # For consistent results
            )

            # Clean up transcript
            cleaned_transcript = transcript.strip()

            if not cleaned_transcript:
                raise RuntimeError("Transcription resulted in empty text")

            logger.debug(
                "Audio transcribed successfully",
                extra={
                    "transcript_length": len(cleaned_transcript),
                    "audio_path": str(audio_path),
                },
            )

            return cleaned_transcript

        except Exception as e:
            logger.error(
                "Transcription failed",
                extra={
                    "error": str(e),
                    "audio_path": str(audio_path),
                },
            )
            raise RuntimeError(f"Audio transcription failed: {str(e)}") from e

    def _calculate_transcription_cost(
        self, duration: int, file_size: Optional[int]
    ) -> float:
        """Calculate estimated cost for voice transcription."""
        # OpenAI Whisper pricing: $0.006 per minute
        base_cost_per_minute = 0.006

        # Convert duration to minutes (round up)
        duration_minutes = (duration + 59) // 60

        # Base transcription cost
        transcription_cost = duration_minutes * base_cost_per_minute

        # Add small processing overhead
        processing_cost = 0.001

        total_cost = transcription_cost + processing_cost

        logger.debug(
            "Voice transcription cost calculated",
            extra={
                "duration": duration,
                "duration_minutes": duration_minutes,
                "transcription_cost": transcription_cost,
                "total_cost": total_cost,
            },
        )

        return total_cost

    async def _cleanup_temp_file(self, file_path: Path) -> None:
        """Clean up temporary voice file."""
        try:
            if file_path.exists():
                file_path.unlink()
                logger.debug(
                    "Temporary voice file cleaned up",
                    extra={"file_path": str(file_path)},
                )
        except Exception as e:
            logger.warning(
                "Failed to clean up temporary voice file",
                extra={
                    "file_path": str(file_path),
                    "error": str(e),
                },
            )

    async def health_check(self) -> bool:
        """Check if voice processing is healthy."""
        try:
            # Check if OpenAI client is configured
            if not self.config.openai_api_key:
                logger.warning("OpenAI API key not configured for voice processing")
                return False

            # Check if temp directory is writable
            test_file = self.temp_dir / "health_check.tmp"
            try:
                test_file.touch()
                test_file.unlink()
            except Exception:
                logger.warning("Voice temp directory not writable")
                return False

            return True

        except Exception as e:
            logger.error("Voice processor health check failed", extra={"error": str(e)})
            return False
