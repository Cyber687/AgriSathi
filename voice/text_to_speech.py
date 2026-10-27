"""
AgriSathi - Text-to-Speech Module

Converts text responses into speech audio.

Features:
    - English and Hindi voice selection.
    - MP3 audio generation.
    - Configurable speech rate and volume.
    - Asynchronous generation with a synchronous wrapper.
    - Structured results and error handling.

Important:
    edge-tts uses an online service and requires internet access.
    It is not an offline text-to-speech engine.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional


class TextToSpeech:
    """Convert AgriSathi responses into speech."""

    DEFAULT_VOICES = {
        "en": "en-IN-NeerjaNeural",
        "hi": "hi-IN-SwaraNeural"
    }

    def __init__(
        self,
        output_directory: str = "generated_audio",
        default_language: str = "en",
        rate: str = "+0%",
        volume: str = "+0%",
    ) -> None:
        """
        Initialize text-to-speech.

        Args:
            output_directory:
                Directory in which generated audio is stored.

            default_language:
                Default language, "en" or "hi".

            rate:
                Speech rate, e.g. "+0%" or "-10%".

            volume:
                Speech volume, e.g. "+0%".
        """

        self.output_directory = Path(output_directory)
        self.default_language = self._normalize_language(
            default_language
        )
        self.rate = rate
        self.volume = volume

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    async def generate_audio_async(
        self,
        text: str,
        language: Optional[str] = None,
        output_filename: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate speech audio asynchronously.

        Args:
            text:
                Text to speak.

            language:
                "en" for English or "hi" for Hindi.

            output_filename:
                Optional MP3 filename.

            voice:
                Optional supported Edge TTS voice identifier.

        Returns:
            Structured generation result.
        """

        if not isinstance(text, str) or not text.strip():
            return self._error("No text was provided for speech generation.")

        language = self._normalize_language(
            language or self.default_language
        )

        if language not in self.DEFAULT_VOICES:
            return self._error(
                "Unsupported language. Use 'en' or 'hi'."
            )

        selected_voice = voice or self.DEFAULT_VOICES[language]

        if output_filename:
            filename = Path(output_filename)

            # Accept a filename, not an arbitrary external path.
            if filename.name != str(filename):
                return self._error(
                    "output_filename must be a filename, not a path."
                )

            if filename.suffix.lower() != ".mp3":
                filename = filename.with_suffix(".mp3")

        else:
            filename = Path("agrisathi_response.mp3")

        output_path = self.output_directory / filename

        try:
            import edge_tts

            communicate = edge_tts.Communicate(
                text.strip(),
                selected_voice,
                rate=self.rate,
                volume=self.volume,
            )

            await communicate.save(str(output_path))

            if not output_path.is_file() or output_path.stat().st_size == 0:
                return self._error(
                    "Speech service returned no audio data."
                )

            return {
                "status": "success",
                "audio_path": str(output_path.resolve()),
                "language": language,
                "voice": selected_voice,
                "format": "mp3",
                "size_bytes": output_path.stat().st_size,
            }

        except ImportError:
            return self._error(
                "edge-tts is not installed. Run: pip install edge-tts"
            )

        except Exception as exc:
            return self._error(
                f"Speech generation failed: {exc}"
            )

    def generate_audio(
        self,
        text: str,
        language: Optional[str] = None,
        output_filename: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synchronous wrapper around generate_audio_async().

        Use this method from ordinary synchronous Python code.
        For asynchronous web frameworks, await generate_audio_async().
        """

        try:
            asyncio.get_running_loop()

        except RuntimeError:
            return asyncio.run(
                self.generate_audio_async(
                    text=text,
                    language=language,
                    output_filename=output_filename,
                    voice=voice,
                )
            )

        return self._error(
            "An event loop is already running. "
            "Use 'await generate_audio_async(...)' instead."
        )

    @staticmethod
    def _normalize_language(language: str) -> str:
        """Normalize language identifiers."""

        return (
            str(language)
            .strip()
            .lower()
            .replace("_", "-")
            .split("-")[0]
        )

    @staticmethod
    def _error(message: str) -> Dict[str, Any]:
        """Return a consistent error result."""

        return {
            "status": "error",
            "audio_path": None,
            "message": message,
        }


def generate_speech(
    text: str,
    language: str = "en",
    output_filename: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function for generating spoken responses."""

    tts = TextToSpeech()

    return tts.generate_audio(
        text=text,
        language=language,
        output_filename=output_filename,
    )