"""
AgriSathi - Speech-to-Text Module

Converts spoken farmer queries into text using faster-whisper.

Features:
    - English and Hindi speech recognition.
    - Automatic language detection.
    - Optional language restriction.
    - Local inference after model download.
    - Structured results and error handling.

The first model initialization may require an internet connection
to download the selected model. Subsequent use can be offline
when the model is available locally.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union


class SpeechToText:
    """Convert audio into text using faster-whisper."""

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
    }

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        model_path: Optional[str] = None,
    ) -> None:
        """
        Initialize speech recognition.

        Args:
            model_size:
                Model name such as tiny, base, small, or medium.

            device:
                "cpu" or "cuda".

            compute_type:
                "int8" is a reasonable CPU starting point.
                For a compatible NVIDIA GPU, "float16" may be used.

            model_path:
                Optional path to an already downloaded local model.
        """

        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model_path = model_path

        self.model: Any = None
        self.initialization_error: Optional[str] = None

    def load_model(self) -> Dict[str, Any]:
        """Load the speech-recognition model when required."""

        if self.model is not None:
            return {
                "status": "success",
                "message": "Speech model is already loaded.",
            }

        try:
            from faster_whisper import WhisperModel

            model_source = self.model_size

            if self.model_path:
                model_directory = Path(self.model_path)

                if not model_directory.exists():
                    return {
                        "status": "error",
                        "message": (
                            f"Model path does not exist: "
                            f"{self.model_path}"
                        ),
                    }

                model_source = str(model_directory)

            self.model = WhisperModel(
                model_source,
                device=self.device,
                compute_type=self.compute_type,
            )

            self.initialization_error = None

            return {
                "status": "success",
                "message": "Speech model loaded successfully.",
            }

        except ImportError:
            self.initialization_error = (
                "faster-whisper is not installed."
            )

            return {
                "status": "error",
                "message": self.initialization_error,
            }

        except Exception as exc:
            self.initialization_error = (
                f"Unable to load speech model: {exc}"
            )

            return {
                "status": "error",
                "message": self.initialization_error,
            }

    def transcribe(
        self,
        audio_path: Union[str, Path],
        language: Optional[str] = None,
        beam_size: int = 5,
        vad_filter: bool = True,
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file.

        Args:
            audio_path:
                Path to the recorded audio file.

            language:
                Optional language code, e.g. "en" or "hi".
                None enables automatic language detection.

            beam_size:
                Beam-search width used by Whisper.

            vad_filter:
                Filter non-speech portions of the recording.

        Returns:
            A structured result containing the transcript,
            detected language, and segment information.
        """

        audio_file = Path(audio_path)

        if not audio_file.is_file():
            return self._error(
                f"Audio file does not exist: {audio_file}"
            )

        if language is not None:
            language = language.strip().lower()

            if language not in self.SUPPORTED_LANGUAGES:
                return self._error(
                    "Unsupported language. Use 'en', 'hi', "
                    "or None for automatic detection."
                )

        if self.model is None:
            load_result = self.load_model()

            if load_result["status"] != "success":
                return self._error(load_result["message"])

        try:
            segments, info = self.model.transcribe(
                str(audio_file),
                language=language,
                beam_size=beam_size,
                vad_filter=vad_filter,
            )

            segment_results = []
            transcript_parts = []

            for segment in segments:
                text = segment.text.strip()

                if text:
                    transcript_parts.append(text)

                    segment_results.append({
                        "start": round(segment.start, 2),
                        "end": round(segment.end, 2),
                        "text": text,
                    })

            transcript = " ".join(transcript_parts).strip()

            if not transcript:
                return self._error(
                    "No recognizable speech was found in the audio."
                )

            detected_language = getattr(
                info,
                "language",
                language,
            )

            return {
                "status": "success",
                "text": transcript,
                "language": detected_language,
                "language_probability": getattr(
                    info,
                    "language_probability",
                    None,
                ),
                "segments": segment_results,
                "audio_file": str(audio_file),
                "model": self.model_size,
            }

        except Exception as exc:
            return self._error(
                f"Speech transcription failed: {exc}"
            )

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        suffix: str = ".wav",
    ) -> Dict[str, Any]:
        """
        Transcribe audio supplied as bytes.

        Useful when the frontend uploads a recording to a Python backend.

        The suffix should match the uploaded audio format.
        """

        import os
        import tempfile

        if not audio_bytes:
            return self._error("The uploaded audio is empty.")

        if not suffix.startswith("."):
            suffix = "." + suffix

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                delete=False,
            ) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            return self.transcribe(
                audio_path=temp_path,
                language=language,
            )

        except Exception as exc:
            return self._error(
                f"Unable to process uploaded audio: {exc}"
            )

        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    @staticmethod
    def _error(message: str) -> Dict[str, Any]:
        """Return a consistent error result."""

        return {
            "status": "error",
            "text": "",
            "language": None,
            "segments": [],
            "message": message,
        }


def transcribe_audio(
    audio_path: Union[str, Path],
    language: Optional[str] = None,
    model_size: str = "small",
) -> Dict[str, Any]:
    """Convenience function for transcribing an audio file."""

    speech_engine = SpeechToText(
        model_size=model_size,
    )

    return speech_engine.transcribe(
        audio_path=audio_path,
        language=language,
    )