"""Optional local GGUF translation helper for AgriSathi.

Uses llama-cpp-python if installed and a model file exists. It translates only
candidate response text, preserves numbers/source IDs, and never creates
agricultural facts. The main application still runs its safety validator after
translation. If unavailable, English/Hindi remain available; other languages
receive a clear error instead of silently receiving the wrong language.
"""
from __future__ import annotations
import os
import importlib
from pathlib import Path
from typing import Any

LANGUAGES = {
    "en": "English", 
    "hi": "Hindi", 
    "pa": "Punjabi", 
    "ta": "Tamil"
}

class LocalGGUFTranslator:
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        configured = os.getenv("AGRISATHI_GGUF_PATH", "").strip()
        candidates = [Path(configured)] if configured else []
        candidates += [
            self.project_root / "models" / "sarvam-1-v0.5-Q8_0.gguf",
            self.project_root / "llama.cpp" / "models" / "sarvam-1-v0.5-Q8_0.gguf", # <-- Added this line
            self.project_root / "sarvam-1-v0.5-Q8_0.gguf",
        ]
        self.model_path = next((p.resolve() for p in candidates if p and p.is_file()), None)
        self._model = None
        self._load_error = None

    @property
    def available(self) -> bool:
        return self.model_path is not None

    def translate(self, text: str, target_language: str) -> str:
        if target_language == "en" or not text:
            return text
        if target_language not in LANGUAGES:
            raise ValueError(f"Unsupported language code: {target_language}")
        if self.model_path is None:
            raise RuntimeError("GGUF model not found. Set AGRISATHI_GGUF_PATH to its full path.")
        if self._model is None:
            try:
                Llama = importlib.import_module("llama_cpp").Llama
                self._model = Llama(model_path=str(self.model_path), n_ctx=4096, verbose=False)
            except Exception as exc:
                self._load_error = str(exc)
                raise RuntimeError("Could not load GGUF model. Install llama-cpp-python and verify model compatibility.") from exc
        language = LANGUAGES[target_language]
        prompt = (
            "You are a faithful agricultural translation assistant. Translate the text below into "
            f"{language}. Do not add, remove, infer, or correct any agricultural advice. "
            "Preserve all numbers, ratios, units, source IDs, warnings, and uncertainty statements exactly. "
            "If a term has no reliable translation, retain the original term and add no new advice. "
            "Return only the translation.\n\nTEXT TO TRANSLATE:\n" + text
        )
        result = self._model.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1800,
        )
        translated = result["choices"][0]["message"]["content"].strip()
        if not translated:
            raise RuntimeError("The local model returned an empty translation.")
        return translated
