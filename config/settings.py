"""
AgriSathi - Central Configuration

Purpose:
    Centralizes project paths, environment variables, API settings,
    language preferences, safety policies, and service configuration.

Security:
    - API keys are loaded from the root .env file.
    - Secrets are never hardcoded in this file.
    - Unverified agricultural chemical recommendations are disabled.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# 1. PROJECT PATHS
# ============================================================

# Project root: parent directory of config/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from the project root .env file.
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE)

CONFIG_DIR = PROJECT_ROOT / "config"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
ENGINE_DIR = PROJECT_ROOT / "engine"
SAFETY_DIR = PROJECT_ROOT / "safety"
SERVICES_DIR = PROJECT_ROOT / "services"
VOICE_DIR = PROJECT_ROOT / "voice"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
MODELS_DIR = PROJECT_ROOT / "models"

# Knowledge base files
CROPS_FILE = KNOWLEDGE_BASE_DIR / "crops.json"
FERTILIZERS_FILE = KNOWLEDGE_BASE_DIR / "fertilizers.json"
PESTS_FILE = KNOWLEDGE_BASE_DIR / "pests.json"
IRRIGATION_FILE = KNOWLEDGE_BASE_DIR / "irrigation.json"
CHEMICALS_FILE = KNOWLEDGE_BASE_DIR / "chemicals.json"
SOURCES_FILE = KNOWLEDGE_BASE_DIR / "sources.json"

# Local language-model file
LLM_MODEL_PATH = MODELS_DIR / "sarvam-1-v0.5-Q8_0.gguf"


# ============================================================
# 2. APPLICATION SETTINGS
# ============================================================

APP_NAME = "AgriSathi"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = (
    "A multilingual agricultural advisory assistant "
    "for Indian farmers."
)

DEBUG = os.getenv("AGRISATHI_DEBUG", "false").lower() == "true"

# Supported languages
SUPPORTED_LANGUAGES = ["en", "hi"]

DEFAULT_LANGUAGE = os.getenv(
    "AGRISATHI_DEFAULT_LANGUAGE",
    "en"
).lower()

if DEFAULT_LANGUAGE not in SUPPORTED_LANGUAGES:
    DEFAULT_LANGUAGE = "en"


# ============================================================
# 3. LOCAL LLM SETTINGS
# ============================================================

LLM_ENABLED = os.getenv(
    "LLM_ENABLED",
    "true"
).lower() == "true"

LLM_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "http://127.0.0.1:8080/v1"
).rstrip("/")

LLM_CHAT_COMPLETIONS_URL = (
    f"{LLM_BASE_URL}/chat/completions"
)

LLM_MODEL_NAME = os.getenv(
    "LLM_MODEL_NAME",
    "sarvam-local"
)

LLM_TIMEOUT_SECONDS = int(
    os.getenv("LLM_TIMEOUT_SECONDS", "60")
)

LLM_MAX_TOKENS = int(
    os.getenv("LLM_MAX_TOKENS", "512")
)

LLM_TEMPERATURE = float(
    os.getenv("LLM_TEMPERATURE", "0.2")
)

# Keep model-generated agricultural facts disabled.
# The model may help rephrase verified information only.
LLM_ALLOW_UNVERIFIED_AGRICULTURAL_FACTS = False
LLM_ALLOW_GENERATED_CHEMICAL_DOSAGES = False


# ============================================================
# 4. WEATHER SERVICE SETTINGS
# ============================================================

OPENWEATHER_API_KEY = os.getenv(
    "OPENWEATHER_API_KEY",
    ""
)

OPENWEATHER_BASE_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
)

WEATHER_TIMEOUT_SECONDS = int(
    os.getenv("WEATHER_TIMEOUT_SECONDS", "15")
)

WEATHER_UNITS = "metric"

WEATHER_LANGUAGE = {
    "en": "en",
    "hi": "hi"
}


# ============================================================
# 5. MANDI PRICE SERVICE SETTINGS
# ============================================================

DATA_GOV_IN_API_KEY = os.getenv(
    "DATA_GOV_IN_API_KEY",
    ""
)

DATA_GOV_IN_RESOURCE_ID = os.getenv(
    "DATA_GOV_IN_RESOURCE_ID",
    "9ef84268-d588-465a-a308-a864a43d0070"
)

DATA_GOV_IN_BASE_URL = (
    "https://api.data.gov.in/resource/"
)

MANDI_API_URL = (
    f"{DATA_GOV_IN_BASE_URL}{DATA_GOV_IN_RESOURCE_ID}"
)

MANDI_TIMEOUT_SECONDS = int(
    os.getenv("MANDI_TIMEOUT_SECONDS", "20")
)

MANDI_DEFAULT_LIMIT = 10
MANDI_MAX_LIMIT = 100

# The data.gov.in dataset normally reports prices in INR per quintal.
MANDI_DEFAULT_CURRENCY = "INR"
MANDI_DEFAULT_PRICE_UNIT = "quintal"


# ============================================================
# 6. KNOWLEDGE BASE SETTINGS
# ============================================================

KNOWLEDGE_BASE_FILES = {
    "crops": CROPS_FILE,
    "fertilizers": FERTILIZERS_FILE,
    "pests": PESTS_FILE,
    "irrigation": IRRIGATION_FILE,
    "chemicals": CHEMICALS_FILE,
    "sources": SOURCES_FILE,
}

# All dataset records must be treated as unverified until
# their evidence has been independently checked.
KNOWLEDGE_BASE_REQUIRE_VERIFIED_SOURCES = True

KNOWLEDGE_BASE_ALLOW_MISSING_FILES = False

KNOWLEDGE_BASE_ENCODING = "utf-8"


# ============================================================
# 7. AGRICULTURAL SAFETY SETTINGS
# ============================================================

SAFETY_ENABLED = True

# Fail closed when required validation cannot be completed.
SAFETY_FAIL_CLOSED = True

# Chemical recommendations require verified evidence.
ALLOW_UNVERIFIED_CHEMICALS = False
ALLOW_UNVERIFIED_DOSAGES = False
ALLOW_MODEL_GENERATED_DOSAGES = False

REQUIRE_CROP_PEST_COMPATIBILITY = True
REQUIRE_AUTHORITATIVE_SOURCES = True
REQUIRE_PRODUCT_LABEL_VERIFICATION = True
REQUIRE_FORMULATION_MATCH = True

# Do not turn incomplete information into a confident recommendation.
ALLOW_UNVERIFIED_FERTILIZER_DOSAGES = False
ALLOW_UNVERIFIED_PEST_CONTROL_INSTRUCTIONS = False

# Missing source evidence must not be treated as verification.
REQUIRE_SOURCE_EVIDENCE_FOR_RECOMMENDATIONS = True


# ============================================================
# 8. RESPONSE SETTINGS
# ============================================================

RESPONSE_INCLUDE_SOURCES = True
RESPONSE_INCLUDE_SAFETY_NOTES = True
RESPONSE_INCLUDE_VERIFICATION_STATUS = True

# Display a warning when information is incomplete.
RESPONSE_WARN_ON_UNVERIFIED_INFORMATION = True

# Avoid returning long responses to farmers.
RESPONSE_MAX_LENGTH = 2000


# ============================================================
# 9. VOICE SETTINGS
# ============================================================

VOICE_ENABLED = os.getenv(
    "VOICE_ENABLED",
    "true"
).lower() == "true"

# Speech recognition uses faster-whisper.
WHISPER_MODEL_SIZE = os.getenv(
    "WHISPER_MODEL_SIZE",
    "base"
)

WHISPER_DEVICE = os.getenv(
    "WHISPER_DEVICE",
    "cpu"
)

WHISPER_COMPUTE_TYPE = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "int8"
)

# Edge TTS requires an internet connection.
TTS_ENABLED = os.getenv(
    "TTS_ENABLED",
    "true"
).lower() == "true"

TTS_VOICES = {
    "en": "en-IN-NeerjaNeural",
    "hi": "hi-IN-SwaraNeural"
}

VOICE_OUTPUT_DIR = PROJECT_ROOT / "voice_output"


# ============================================================
# 10. HTTP AND API SETTINGS
# ============================================================

HTTP_CONNECT_TIMEOUT_SECONDS = 5
HTTP_READ_TIMEOUT_SECONDS = 20

HTTP_DEFAULT_TIMEOUT = (
    HTTP_CONNECT_TIMEOUT_SECONDS,
    HTTP_READ_TIMEOUT_SECONDS
)

HTTP_MAX_RETRIES = 2


# ============================================================
# 11. LOGGING SETTINGS
# ============================================================

LOG_LEVEL = os.getenv(
    "AGRISATHI_LOG_LEVEL",
    "INFO"
).upper()

LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "agrisathi.log"

# Never log API keys, passwords, or other secrets.
LOG_SECRETS = False


# ============================================================
# 12. OPTIONAL DIRECTORIES
# ============================================================

# Create runtime directories when needed.
# Knowledge-base files are not created automatically.

RUNTIME_DIRECTORIES = [
    LOG_DIR,
    VOICE_OUTPUT_DIR,
]


def create_runtime_directories():
    """Create directories required for runtime output."""
    for directory in RUNTIME_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


def get_missing_knowledge_base_files():
    """
    Return the names of configured knowledge-base files
    that do not currently exist.
    """
    return [
        name
        for name, path in KNOWLEDGE_BASE_FILES.items()
        if not path.is_file()
    ]


def validate_configuration():
    """
    Perform basic configuration checks.

    Returns:
        dict: Configuration validation results.

    Note:
        This checks configuration and file presence.
        It does not verify agricultural claims or sources.
    """
    errors = []
    warnings = []

    if LLM_TIMEOUT_SECONDS <= 0:
        errors.append(
            "LLM_TIMEOUT_SECONDS must be greater than zero."
        )

    if LLM_MAX_TOKENS <= 0:
        errors.append(
            "LLM_MAX_TOKENS must be greater than zero."
        )

    if not 0.0 <= LLM_TEMPERATURE <= 2.0:
        errors.append(
            "LLM_TEMPERATURE must be between 0 and 2."
        )

    if MANDI_DEFAULT_LIMIT <= 0:
        errors.append(
            "MANDI_DEFAULT_LIMIT must be greater than zero."
        )

    if MANDI_MAX_LIMIT < MANDI_DEFAULT_LIMIT:
        errors.append(
            "MANDI_MAX_LIMIT cannot be smaller than "
            "MANDI_DEFAULT_LIMIT."
        )

    if not OPENWEATHER_API_KEY:
        warnings.append(
            "OPENWEATHER_API_KEY is missing. "
            "Live weather requests will not work."
        )

    if not DATA_GOV_IN_API_KEY:
        warnings.append(
            "DATA_GOV_IN_API_KEY is missing. "
            "Live mandi price requests may not work."
        )

    if not SOURCES_FILE.is_file():
        warnings.append(
            "sources.json is missing. "
            "Source validation cannot be completed."
        )

    if not LLM_MODEL_PATH.is_file():
        warnings.append(
            "The configured local GGUF model file was not found. "
            "Check LLM_MODEL_PATH."
        )

    missing_files = get_missing_knowledge_base_files()

    if missing_files:
        warnings.append(
            "Missing knowledge-base files: "
            + ", ".join(missing_files)
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "project_root": str(PROJECT_ROOT),
        "default_language": DEFAULT_LANGUAGE,
        "llm_enabled": LLM_ENABLED,
        "safety_enabled": SAFETY_ENABLED,
    }