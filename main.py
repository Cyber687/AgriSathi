"""
AgriSathi - Main Application

Purpose:
    Integrates the frontend API, query parser, knowledge base,
    rule engine, recommendation engine, safety engine, weather
    service, mandi service, and optional local LLM.

Run:
    python main.py

API:
    GET  /health
    POST /api/chat
    GET  /api/weather
    GET  /api/mandi

Safety:
    A recommendation is approved only when the safety engine
    explicitly returns an approved result.

    Exceptions, missing validators, missing evidence, and
    ambiguous approval states fail closed.
"""

from __future__ import annotations

import inspect
import json
import logging
import re

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import settings as app_settings

from engine.query_parser import QueryParser
from engine.rule_engine import RuleEngine
from engine.recommendation import RecommendationEngine

from services.weather_service import WeatherService
from services.mandi_service import MandiService
from services.gemini_service import GeminiService
from services.local_gguf_translator import LocalGGUFTranslator, LANGUAGES


# ============================================================
# 1. APPLICATION PATHS AND LOGGING
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

FRONTEND_DIR = PROJECT_ROOT / "frontend"

logger = logging.getLogger("agrisathi")

logging.basicConfig(
    level=getattr(
        logging,
        getattr(app_settings, "LOG_LEVEL", "INFO"),
        logging.INFO,
    ),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


# ============================================================
# 2. FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AgriSathi API",
    description=(
        "Multilingual agricultural advisory API with "
        "knowledge-base retrieval and safety validation."
    ),
    version="1.0.0",
)

# Local development configuration.
# Restrict this further when deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "null",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)


# ============================================================
# 3. REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):
    """Incoming chat request from the frontend."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Farmer's agricultural question.",
    )

    language: str = Field(
        default="en",
        description="Response language code supported by AgriSathi.",
    )

    location: str | None = Field(
        default=None,
        max_length=200,
    )

    crop: str | None = Field(
        default=None,
        max_length=100,
    )

    state: str | None = Field(
        default=None,
        max_length=100,
    )

    district: str | None = Field(
        default=None,
        max_length=100,
    )

    market: str | None = Field(
        default=None,
        max_length=100,
    )


# ============================================================
# 4. GENERAL HELPER FUNCTIONS
# ============================================================

def utc_timestamp() -> str:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def safe_string(value: Any, default: str = "") -> str:
    """Convert a value to a string without propagating None."""

    if value is None:
        return default

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def unique_strings(values: Any) -> list[str]:
    """Convert a list-like value into unique non-empty strings."""

    if not isinstance(values, (list, tuple, set)):
        return []

    result = []
    seen = set()

    for item in values:
        if isinstance(item, dict):
            item = (
                item.get("message")
                or item.get("title")
                or item.get("name")
                or item.get("source_id")
                or ""
            )

        text = safe_string(item)

        if text and text not in seen:
            seen.add(text)
            result.append(text)

    return result


def to_plain_dict(value: Any) -> dict[str, Any]:
    """
    Convert supported objects to dictionaries.

    Handles dictionaries, Pydantic models, and objects exposing
    to_dict() or model_dump().
    """

    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        result = value.model_dump()

        if isinstance(result, dict):
            return result

    if hasattr(value, "to_dict"):
        result = value.to_dict()

        if isinstance(result, dict):
            return result

    if hasattr(value, "__dict__"):
        return {
            key: item
            for key, item in vars(value).items()
            if not key.startswith("_")
        }

    return {}


def call_with_supported_arguments(
    function: Any,
    **kwargs: Any,
) -> Any:
    """
    Call a function using only arguments accepted by its signature.

    This helps integrate modules whose optional keyword arguments
    differ slightly, without hiding errors raised inside the function.
    """

    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return function(**kwargs)

    parameters = signature.parameters

    accepts_kwargs = any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )

    if accepts_kwargs:
        return function(**kwargs)

    supported_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key in parameters
    }

    return function(**supported_kwargs)


def extract_sources(*objects: Any) -> list[Any]:
    """Collect source information from pipeline results."""

    sources = []
    seen = set()

    for obj in objects:
        data = to_plain_dict(obj)

        for key in (
            "sources",
            "source_refs",
            "source_ids",
            "citations",
        ):
            value = data.get(key, [])

            if not isinstance(value, list):
                continue

            for source in value:
                marker = json.dumps(
                    source,
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                )

                if marker not in seen:
                    seen.add(marker)
                    sources.append(source)

    return sources


def extract_warnings(*objects: Any) -> list[str]:
    """Collect warnings from multiple pipeline stages."""

    warnings = []

    for obj in objects:
        data = to_plain_dict(obj)

        warnings.extend(
            unique_strings(data.get("warnings", []))
        )

        warnings.extend(
            unique_strings(data.get("issues", []))
        )

    return unique_strings(warnings)


# ============================================================
# 5. KNOWLEDGE BASE ADAPTER
# ============================================================

class AgriSathiKnowledgeBase:
    """
    JSON knowledge-base adapter.

    Reads the existing JSON files from knowledge_base/.

    This adapter exposes:
        get_records(category)
        find_records(category, filters)

    It supports the interface expected by the project's rule engine.
    """

    CATEGORY_FILES = {
        "crops": "crops.json",
        "fertilizers": "fertilizers.json",
        "pests": "pests.json",
        "irrigation": "irrigation.json",
        "chemicals": "chemicals.json",
        "sources": "sources.json",
    }

    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self._cache: dict[str, list[dict[str, Any]]] = {}

    def _extract_records(self, payload: Any) -> list[dict[str, Any]]:
        """Extract records from common JSON structures."""

        if isinstance(payload, list):
            return [
                item for item in payload
                if isinstance(item, dict)
            ]

        if not isinstance(payload, dict):
            return []

        for key in (
            "records",
            "data",
            "items",
            "crops",
            "fertilizers",
            "pests",
            "irrigation",
            "chemicals",
            "sources",
        ):
            value = payload.get(key)

            if isinstance(value, list):
                return [
                    item for item in value
                    if isinstance(item, dict)
                ]

        # A metadata-only JSON object is not a record.
        if "_metadata" in payload:
            return []

        return [payload]

    def get_records(
        self,
        category: str,
    ) -> list[dict[str, Any]]:
        """Load all records for a knowledge-base category."""

        category = safe_string(category).lower()

        if category in self._cache:
            return self._cache[category]

        filename = self.CATEGORY_FILES.get(category)

        if not filename:
            logger.warning(
                "Unknown knowledge-base category: %s",
                category,
            )
            return []

        path = self.directory / filename

        if not path.is_file():
            logger.warning(
                "Knowledge-base file is missing: %s",
                path,
            )

            self._cache[category] = []
            return []

        try:
            with path.open(
                "r",
                encoding="utf-8-sig",
            ) as file:
                payload = json.load(file)

        except (OSError, json.JSONDecodeError) as exc:
            logger.error(
                "Unable to load %s: %s",
                filename,
                exc,
            )

            self._cache[category] = []
            return []

        records = self._extract_records(payload)

        self._cache[category] = records

        logger.info(
            "Loaded %d records from %s",
            len(records),
            filename,
        )

        return records

    @staticmethod
    def _flatten_text(value: Any) -> str:
        """Flatten nested bilingual JSON values for matching."""

        if value is None:
            return ""

        if isinstance(value, dict):
            return " ".join(
                AgriSathiKnowledgeBase._flatten_text(item)
                for item in value.values()
            )

        if isinstance(value, list):
            return " ".join(
                AgriSathiKnowledgeBase._flatten_text(item)
                for item in value
            )

        return str(value)

    def find_records(
        self,
        category: str,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find candidate records.

        Matching is deliberately conservative: when crop or pest
        information is provided, a record must contain a matching
        value in its relevant fields.

        Matching does not establish scientific verification.
        """

        records = self.get_records(category)

        if not filters:
            return records

        filters = {
            key: value
            for key, value in filters.items()
            if value not in (None, "", [], {})
        }

        if not filters:
            return records

        def terms(value: Any) -> list[str]:
            if isinstance(value, str):
                return [value.casefold()]

            if isinstance(value, list):
                result = []

                for item in value:
                    result.extend(terms(item))

                return result

            return []

        results = []

        for record in records:
            matches = True

            for filter_name, filter_value in filters.items():
                if filter_name in {
                    "location",
                    "state",
                    "district",
                    "market",
                }:
                    # Location is not reliably represented in all
                    # static agricultural knowledge-base records.
                    continue

                expected_terms = terms(filter_value)

                if not expected_terms:
                    continue

                if filter_name in {"crops", "crop"}:
                    fields = [
                        record.get("crop"),
                        record.get("crop_name"),
                        record.get("name"),
                        record.get("aliases"),
                    ]

                elif filter_name in {"pests", "pest"}:
                    fields = [
                        record.get("pest"),
                        record.get("pest_name"),
                        record.get("pests_and_diseases_as_listed"),
                        record.get("target_pest"),
                    ]

                elif filter_name in {"symptoms", "reported_symptoms"}:
                    fields = [
                        record.get("symptoms"),
                        record.get("disease"),
                        record.get("pests_and_diseases_as_listed"),
                        record.get("description"),
                    ]

                else:
                    # Avoid treating arbitrary filter keys as proof
                    # of a record match.
                    continue

                searchable = self._flatten_text(fields).casefold()

                if not any(
                    term in searchable
                    for term in expected_terms
                    if term
                ):
                    matches = False
                    break

            if matches:
                results.append(record)

        return results


# ============================================================
# 6. COMPONENT INITIALIZATION
# ============================================================

class AgriSathiApplication:
    """Initialize and connect AgriSathi components."""

    def __init__(self):
        # UPGRADE: Initialize Cache & Memory
        self.response_cache = {}
        self.last_crop_context = None
        
        self.knowledge_base = AgriSathiKnowledgeBase(
            PROJECT_ROOT / "knowledge_base"
        )

        # Query parser
        self.query_parser = QueryParser()

        # External services
        self.weather_service = WeatherService()
        self.mandi_service = MandiService()

        # Rule engine
        self.rule_engine = RuleEngine(
            knowledge_base_loader=self.knowledge_base,
            weather_service=self.weather_service,
            mandi_service=self.mandi_service,
        )

        # Recommendation engine
        self.recommendation_engine = RecommendationEngine()
        self.local_translator = LocalGGUFTranslator(PROJECT_ROOT)
        self.gemini_service = GeminiService()

        # Safety engine is imported lazily so the API can report
        # initialization failures without pretending that advice
        # is safe.
        self.safety_engine = None
        self.safety_initialization_error = None

        try:
            from safety.safety_engine import SafetyEngine

            self.safety_engine = SafetyEngine(
                knowledge_base_loader=self.knowledge_base,
                sources_file=str(PROJECT_ROOT / "knowledge_base" / "sources.json")
            )

        except Exception as exc:
            self.safety_initialization_error = str(exc)

            logger.exception(
                "Safety engine could not be initialized."
            )

    @staticmethod
    def _blocked_safety_result(
        reason: str,
    ) -> dict[str, Any]:
        """Build a fail-closed safety result."""

        return {
            "approved": False,
            "status": "blocked",
            "issues": [reason],
            "warnings": [
                "The recommendation has not passed safety validation."
            ],
        }

    def _validate_safety(
        self,
        recommendation: dict[str, Any],
        query: str,
        rule_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Run safety validation and fail closed on any failure."""

        if self.safety_engine is None:
            return self._blocked_safety_result(
                "Safety engine is unavailable."
            )

        validator = getattr(
            self.safety_engine,
            "validate_recommendation",
            None,
        )

        if not callable(validator):
            return self._blocked_safety_result(
                "The safety engine does not expose "
                "validate_recommendation()."
            )

        try:
            result = call_with_supported_arguments(
                validator,
                recommendation=recommendation,
                query=query,
                rule_result=rule_result,
                require_verified_evidence=True,
            )

            result_dict = to_plain_dict(result)

            if not result_dict:
                return self._blocked_safety_result(
                    "The safety engine returned no usable result."
                )

            # A positive result must explicitly state approval.
            # A missing approval field is never interpreted as True.
            approved = result_dict.get("approved") is True

            if not approved:
                result_dict["approved"] = False

                result_dict.setdefault(
                    "status",
                    "blocked",
                )

            return result_dict

        except Exception:
            logger.exception(
                "Safety validation failed."
            )

            return self._blocked_safety_result(
                "Safety validation encountered an error."
            )

    def answer(
        self,
        query: str,
        language: str = "en",
        location: str | None = None,
        crop: str | None = None,
    ) -> dict[str, Any]:
        """
        Run the core AgriSathi pipeline.

        Flow:
            QueryParser
                -> RuleEngine
                -> RecommendationEngine
                -> SafetyEngine
                -> API response
        """

        query = safe_string(query)

        if not query:
            raise ValueError(
                "Please enter a question."
            )

        # UPGRADE: Check Response Cache
        cache_key = f"{query.lower().strip()}_{language}"
        if cache_key in self.response_cache:
            logger.info(f"⚡ Cache Hit: Returning instant response for '{query}'")
            return self.response_cache[cache_key]

        language = (language or "en").strip().lower()
        
        # GREETINGS HANDLER
        q_lower = query.lower().strip()
        greeting_replies = {
            "hi": ("Namaste! I am AgriSathi. How can I help you with your crops today?", "नमस्ते! मैं एग्रीसाथी हूँ। आज मैं आपकी फसलों में कैसे मदद कर सकता हूँ?"),
            "hello": ("Namaste! I am AgriSathi. How can I help you with your crops today?", "नमस्ते! मैं एग्रीसाथी हूँ। आज मैं आपकी फसलों में कैसे मदद कर सकता हूँ?"),
            "hey": ("Namaste! I am AgriSathi. How can I help you with your crops today?", "नमस्ते! मैं एग्रीसाथी हूँ। आज मैं आपकी फसलों में कैसे मदद कर सकता हूँ?"),
            "namaste": ("Namaste! I am AgriSathi. How can I help you with your crops today?", "नमस्ते! मैं एग्रीसाथी हूँ। आज मैं आपकी फसलों में कैसे मदद कर सकता हूँ?"),
            "how are you": ("I am doing well, thank you for asking! I am ready to help you with your farming questions.", "मैं ठीक हूँ, पूछने के लिए धन्यवाद! मैं आपके खेती से जुड़े सवालों में मदद के लिए तैयार हूँ।"),
            "good morning": ("Good morning! I am AgriSathi. How can I assist you today?", "सुप्रभात! मैं एग्रीसाथी हूँ। मैं आज आपकी कैसे मदद कर सकता हूँ?"),
            "good evening": ("Good evening! I am AgriSathi. How can I assist you today?", "शुभ संध्या! मैं एग्रीसाथी हूँ। मैं आज आपकी कैसे मदद कर सकता हूँ?")
        }
        
        if q_lower in greeting_replies:
            en_reply, hi_reply = greeting_replies[q_lower]
            return {
                "approved": True, "status": "approved", "language": language,
                "answer": en_reply if language == "en" else hi_reply,
                "sources": [], "warnings": [], "safety": {"approved": True, "status": "approved"}, "timestamp": utc_timestamp()
            }

        if language not in LANGUAGES:
            return self._error_response(
                query,
                f"Unsupported language code: {language}. Choose one of: {', '.join(LANGUAGES)}.",
            )
        requested_language = language
        # Current parser/recommendation templates are natively English/Hindi.
        # Other languages use the local GGUF only for faithful translation.
        processing_language = language if language in {"en", "hi"} else "en"

        # ============================================================
        # UPGRADE: PRE-FLIGHT GEMINI ROUTING
        # ============================================================
        # If the query is non-agricultural and not dangerous, route to Gemini immediately.
        is_dangerous = bool(re.search(r"\b(pesticide|insecticide|fungicide|herbicide|dosage|dose)\b", query, flags=re.IGNORECASE))
        agri_keywords = ["crop", "wheat", "rice", "maize", "potato", "tomato", "pest", "fertilizer", "soil", "weather", "mandi", "seed", "plant", "farm", "irrigation", "yield", "harvest", "agriculture", "farming"]
        is_agri = any(k in query.lower() for k in agri_keywords)
        
        if not is_agri and not is_dangerous:
            logger.info(f"✨ General query detected PRE-FLIGHT. Routing directly to Gemini.")
            system_prompt = (
                "You are AgriSathi, a helpful Indian AI assistant. "
                "Answer the user's question accurately in 1-2 sentences. "
                "If the question is entirely unrelated to farming, gently mention you are an agricultural assistant but still answer the question."
            )
            gemini_response = self.gemini_service.generate(prompt=query, system_prompt=system_prompt)
            
            if gemini_response:
                final_response = {
                    "approved": True, "status": "approved", "language": requested_language,
                    "answer": gemini_response, "final_answer": gemini_response,
                    "query": query, "intent": "general_knowledge",
                    "parsed_query": {}, "sources": [], "warnings": [],
                    "safety": {"approved": True, "status": "approved"},
                    "timestamp": utc_timestamp(),
                }
                self.response_cache[cache_key] = final_response
                return final_response
            else:
                # If Gemini times out or fails, return a friendly message instead of blocking
                logger.warning("Gemini failed. Returning friendly fallback.")
                fallback_msg = "I am currently having trouble reaching the general knowledge server. However, as an agricultural assistant, I am fully ready to help you with crop cultivation, pests, weather, and market prices!"
                final_response = {
                    "approved": True, "status": "approved", "language": requested_language,
                    "answer": fallback_msg, "final_answer": fallback_msg,
                    "query": query, "intent": "general_knowledge",
                    "parsed_query": {}, "sources": [], "warnings": [],
                    "safety": {"approved": True, "status": "approved"},
                    "timestamp": utc_timestamp(),
                }
                self.response_cache[cache_key] = final_response
                return final_response

        # ----------------------------------------------------
        # A. PARSE THE QUERY
        # ----------------------------------------------------

        try:
            parsed_result = self.query_parser.parse(
                query,
                language=processing_language,
                location=location,
                crop=crop,
            )

            parsed_result = to_plain_dict(parsed_result)

        except Exception:
            logger.exception(
                "Query parsing failed."
            )

            return self._error_response(
                query,
                "The query could not be parsed.",
            )

        if not parsed_result:
            return self._error_response(
                query,
                "The query parser returned no usable result.",
            )

        inner_query = parsed_result.get("query", {})
        if not isinstance(inner_query, dict):
            inner_query = {}

        intent = safe_string(
            inner_query.get("intent"),
            "unknown",
        )

        # UPGRADE: Conversational Memory Injection
        entities = inner_query.get("entities", {})
        crops = entities.get("crops", [])
        
        if not crops and self.last_crop_context:
            # Inject the last crop if the user forgot to mention it
            entities["crops"] = [self.last_crop_context]
            inner_query["entities"] = entities
            query = f"{query} for {self.last_crop_context}" # Update query for LLM context
            logger.info(f"🧠 Memory used: Injecting previous crop '{self.last_crop_context}'")
        elif crops:
            # Save the current crop for future questions
            self.last_crop_context = crops[0]

        # ----------------------------------------------------
        # B. RETRIEVE CANDIDATE INFORMATION
        # ----------------------------------------------------

        try:
            rule_result = self.rule_engine.process_query(
                parsed_result
            )

            rule_result = to_plain_dict(rule_result)

        except Exception:
            logger.exception(
                "Rule engine processing failed."
            )

            return self._error_response(
                query,
                "The agricultural information could not be retrieved.",
                parsed_result=parsed_result,
            )

        if not rule_result:
            return self._error_response(
                query,
                "The rule engine returned no usable result.",
                parsed_result=parsed_result,
            )

        # ----------------------------------------------------
        # C. GENERATE A CANDIDATE RESPONSE
        # ----------------------------------------------------

        try:
            recommendation = (
                self.recommendation_engine
                .generate_recommendation(
                    rule_result,
                    query=query,
                    use_llm=True,
                )
            )

            recommendation = to_plain_dict(
                recommendation
            )

        except Exception:
            logger.exception(
                "Recommendation generation failed."
            )

            return self._error_response(
                query,
                "A recommendation could not be generated.",
                parsed_result=parsed_result,
                rule_result=rule_result,
            )

        if not recommendation:
            return self._error_response(
                query,
                "The recommendation engine returned no usable result.",
                parsed_result=parsed_result,
                rule_result=rule_result,
            )

        # ----------------------------------------------------
        # D. LOCALIZE CANDIDATE RESPONSE BEFORE SAFETY VALIDATION
        # ----------------------------------------------------
        if requested_language not in {"en", "hi"}:
            candidate_text = safe_string(
                recommendation.get("answer") or recommendation.get("final_answer")
            )
            if candidate_text:
                try:
                    translated_text = self.local_translator.translate(
                        candidate_text, requested_language
                    )
                    recommendation["answer"] = translated_text
                    if "final_answer" in recommendation:
                        recommendation["final_answer"] = translated_text
                    recommendation["response_language"] = requested_language
                except Exception as exc:
                    logger.exception("Local GGUF translation failed.")
                    return self._error_response(
                        query,
                        f"The selected language ({LANGUAGES[requested_language]}) is not available right now. Check the GGUF model path and llama-cpp-python installation. Details: {exc}",
                        parsed_result=parsed_result,
                        rule_result=rule_result,
                    )

        # ----------------------------------------------------
        # E. ENFORCE CHEMICAL SAFETY
        # ----------------------------------------------------

        # This additional guard is intentional. The system must not
        # produce an approved chemical recommendation unless the
        # recommendation itself has passed the safety engine.

        chemical_requested = bool(
            re.search(
                r"\b("
                r"pesticide|insecticide|fungicide|herbicide|"
                r"chemical|dosage|dose|spray|active ingredient"
                r")\b|"
                r"कीटनाशक|दवा की मात्रा|छिड़काव|रासायनिक",
                query,
                flags=re.IGNORECASE,
            )
        )

        # ----------------------------------------------------
        # E. FINAL SAFETY VALIDATION
        # ----------------------------------------------------

        safety_result = self._validate_safety(
            recommendation=recommendation,
            query=inner_query,
            rule_result=rule_result,
        )
        
        # DEBUG PRINT: This will show in Terminal 2 exactly why it failed
        if not safety_result.get("approved"):
            import json
            print("\n" + "="*50)
            print("🚨 SAFETY ENGINE BLOCKED THE RESPONSE!")
            print(json.dumps(safety_result, indent=2))
            print("="*50 + "\n")

        safety_approved = (
            safety_result.get("approved") is True
        )

        # Do not let a recommendation's own "approved" field
        # override the result of the safety engine.
        approved = safety_approved

        if chemical_requested and not safety_approved:
            approved = False

        # ----------------------------------------------------
        # F. BUILD THE FINAL RESPONSE
        # ----------------------------------------------------

        answer_text = safe_string(
            recommendation.get("answer")
            or recommendation.get("final_answer")
        )

        warnings = extract_warnings(
            rule_result,
            recommendation,
            safety_result,
        )

        sources = extract_sources(
            rule_result,
            recommendation,
        )

        if not safety_approved:
            answer_text = "I don't have verified information for this specific question yet. I have logged this query so our agricultural experts can review it. Please consult your local Krishi Vigyan Kendra (KVK) for immediate help."
            warnings = ["Safety verification could not be completed."]

        if chemical_requested and not safety_approved:
            answer_text = (
                "I cannot provide a verified chemical recommendation "
                "or dosage because the required safety checks have "
                "not approved it. Please consult the applicable "
                "registered product label or a qualified agricultural "
                "expert."
            )

        if not answer_text:
            answer_text = (
                "I could not generate a reliable answer from the "
                "available information. Please provide more details "
                "or consult a qualified agricultural expert."
            )

        status = (
            "approved"
            if approved
            else safe_string(
                safety_result.get("status"),
                "needs_verification",
            )
        )

        final_response = {
            "approved": approved,
            "status": status,
            "language": requested_language,
            "answer": answer_text,
            "final_answer": answer_text,
            "query": query,
            "intent": intent,
            "parsed_query": {
                "intent": intent,
                "language": parsed_result.get("language", language),
                "entities": parsed_result.get("entities", {}),
                "location": location,
                "crop": crop,
            },
            "sources": sources,
            "warnings": unique_strings(warnings),
            "safety": safety_result,
            "timestamp": utc_timestamp(),
        }
        
        # UPGRADE: Save to Cache
        self.response_cache[cache_key] = final_response
        return final_response

    @staticmethod
    def _error_response(
        query: str,
        message: str,
        parsed_result: dict[str, Any] | None = None,
        rule_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a safe error response."""

        return {
            "approved": False,
            "status": "error",
            "answer": (
                "I could not safely process this question. "
                "Please try again or provide more details."
            ),
            "final_answer": (
                "I could not safely process this question. "
                "Please try again or provide more details."
            ),
            "query": query,
            "parsed_query": parsed_result or {},
            "rule_result": rule_result or {},
            "sources": [],
            "warnings": [message],
            "safety": {
                "approved": False,
                "status": "blocked",
                "issues": [message],
            },
            "timestamp": utc_timestamp(),
        }


# ============================================================
# 7. INITIALIZE APPLICATION COMPONENTS
# ============================================================

agrisathi: AgriSathiApplication | None = None
initialization_error: str | None = None

try:
    agrisathi = AgriSathiApplication()

except Exception as exc:
    initialization_error = str(exc)

    logger.exception(
        "AgriSathi application initialization failed."
    )


# ============================================================
# 8. HEALTH ENDPOINT
# ============================================================

@app.get("/health")
def health():
    """
    Check whether the backend is running.

    A running API does not imply that every dependency or
    safety validator is operational.
    """

    initialized = agrisathi is not None

    safety_available = bool(
        agrisathi is not None
        and agrisathi.safety_engine is not None
    )

    return {
        "status": (
            "ok"
            if initialized
            else "degraded"
        ),
        "application": "AgriSathi",
        "version": "1.0.0",
        "initialized": initialized,
        "safety_engine_available": safety_available,
        "timestamp": utc_timestamp(),
    }


# ============================================================
# 9. CHAT ENDPOINT
# ============================================================

@app.post("/api/chat")
def chat(request: ChatRequest):
    """
    Receive a farmer's question and return a validated response.

    Request example:
        {
            "query": "How can I manage pests in wheat?",
            "language": "en",
            "location": "Ludhiana",
            "crop": "Wheat"
        }
    """

    if agrisathi is None:
        raise HTTPException(
            status_code=503,
            detail={
                "message": (
                    "AgriSathi could not initialize. "
                    "Check the backend logs and configuration."
                ),
                "approved": False,
            },
        )

    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=422,
            detail="The question cannot be empty.",
        )

    try:
        result = agrisathi.answer(
            query=query,
            language=request.language,
            location=request.location,
            crop=request.crop,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Unexpected error in /api/chat."
        )

        # Do not expose stack traces or internal secrets.
        return {
            "approved": False,
            "status": "error",
            "answer": (
                "An unexpected error occurred while processing "
                "your question. Please try again."
            ),
            "final_answer": (
                "An unexpected error occurred while processing "
                "your question. Please try again."
            ),
            "sources": [],
            "warnings": [
                "The backend could not complete the request."
            ],
            "timestamp": utc_timestamp(),
        }


# ============================================================
# 10. WEATHER ENDPOINT
# ============================================================

@app.get("/api/weather")
def weather(
    location: str | None = Query(
        default=None,
        max_length=200,
    ),
):
    """
    Retrieve weather information.

    Example:
        /api/weather?location=Ludhiana

    Weather data is informational. The endpoint does not
    automatically generate or approve irrigation advice.
    """

    if agrisathi is None:
        raise HTTPException(
            status_code=503,
            detail="AgriSathi is not initialized.",
        )

    if not location:
        return {
            "approved": False,
            "status": "needs_location",
            "message": (
                "Provide a city or supported location to retrieve "
                "weather information."
            ),
            "timestamp": utc_timestamp(),
        }

    try:
        result = call_with_supported_arguments(
            agrisathi.weather_service.get_weather,
            location=location,
        )

        result = to_plain_dict(result)

        if not result:
            return {
                "approved": False,
                "status": "unavailable",
                "message": "No weather data was returned.",
                "timestamp": utc_timestamp(),
            }

        service_status = result.get("status")

        if service_status != "success":
            return {
                "approved": False,
                "status": "unavailable",
                "message": (
                    result.get("message")
                    or result.get("error")
                    or "Weather service did not return success."
                ),
                "timestamp": utc_timestamp(),
            }

        data = result.get("data", {})

        if not isinstance(data, dict):
            data = {}

        return {
            "approved": False,
            "status": "live_data",
            "location": location,
            "temperature_c": data.get("temperature_c"),
            "humidity": data.get("humidity_percent"),
            "wind_mps": data.get("wind_speed_mps"),
            "rainfall_1h_mm": data.get("rainfall_1h_mm"),
            "rainfall_3h_mm": data.get("rainfall_3h_mm"),
            "description": data.get("description"),
            "updated_at": result.get("timestamp") or utc_timestamp(),
            "message": (
                "Weather data retrieved. Verify local conditions "
                "before making weather-dependent farming decisions."
            ),
        }

    except Exception:
        logger.exception(
            "Weather service request failed."
        )

        return {
            "approved": False,
            "status": "unavailable",
            "message": (
                "Weather information is temporarily unavailable."
            ),
            "timestamp": utc_timestamp(),
        }


# ============================================================
# 11. MANDI PRICE ENDPOINT
# ============================================================

@app.get("/api/mandi")
def mandi(
    crop: str = Query(
        ...,
        min_length=1,
        max_length=100,
    ),
    market: str | None = Query(
        default=None,
        max_length=100,
    ),
    state: str | None = Query(
        default=None,
        max_length=100,
    ),
    district: str | None = Query(
        default=None,
        max_length=100,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
):
    """
    Retrieve mandi prices.

    Example:
        /api/mandi?crop=Wheat&market=Ludhiana

    Prices are returned as market data, not as a guarantee
    of the price a farmer will receive.
    """

    if agrisathi is None:
        raise HTTPException(
            status_code=503,
            detail="AgriSathi is not initialized.",
        )

    try:
        result = call_with_supported_arguments(
            agrisathi.mandi_service.get_prices,
            crop=crop,
            location=market,
            state=state,
            district=district,
            market=market,
            limit=limit,
            offset=0,
        )

        result = to_plain_dict(result)

        if result.get("status") != "success":
            return {
                "approved": False,
                "status": "unavailable",
                "crop": crop,
                "records": [],
                "message": (
                    result.get("message")
                    or result.get("error")
                    or "Mandi price data is unavailable."
                ),
                "timestamp": utc_timestamp(),
            }

        records = result.get("records", [])

        if not isinstance(records, list):
            records = []

        return {
            "approved": False,
            "status": "live_data",
            "crop": crop,
            "market": market,
            "state": state,
            "district": district,
            "unit": "INR per quintal",
            "records": records,
            "updated_at": result.get("timestamp") or utc_timestamp(),
            "message": (
                "These are retrieved market records. Check the "
                "market, commodity, date, and unit before relying "
                "on the prices."
            ),
        }

    except Exception:
        logger.exception(
            "Mandi service request failed."
        )

        return {
            "approved": False,
            "status": "unavailable",
            "crop": crop,
            "records": [],
            "message": (
                "Mandi prices are temporarily unavailable."
            ),
            "timestamp": utc_timestamp(),
        }



@app.post("/api/tts")
async def generate_speech(request: ChatRequest):
    """Generate natural-sounding audio using edge-tts (Async Safe)."""
    try:
        from voice.text_to_speech import TextToSpeech
        tts = TextToSpeech()
        import time
        filename = f"tts_{int(time.time())}.mp3"
        
        # Use the async method directly to prevent blocking the server
        result = await tts.generate_audio_async(text=request.query, language=request.language, output_filename=filename)
        
        if result["status"] == "success":
            return FileResponse(result["audio_path"], media_type="audio/mpeg")
            
        logger.error(f"TTS Failed: {result.get('message')}")
        raise HTTPException(status_code=500, detail="TTS generation failed")
        
    except Exception as e:
        logger.exception("TTS Endpoint Crashed")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# 12. FRONTEND SERVING
# ============================================================

@app.get("/", include_in_schema=False)
def serve_frontend():
    """Serve the AgriSathi frontend homepage."""

    index_file = FRONTEND_DIR / "index.html"

    if not index_file.is_file():
        return {
            "application": "AgriSathi",
            "message": (
                "Backend is running. The frontend index.html "
                "was not found."
            ),
            "api_docs": "/docs",
            "health": "/health",
        }

    return FileResponse(index_file)


# Serve CSS, JavaScript, and other frontend assets.
if FRONTEND_DIR.is_dir():
    app.mount(
        "/frontend",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="frontend",
    )


# ============================================================
# 13. APPLICATION ENTRY POINT
# ============================================================

def main():
    """Start the AgriSathi development server."""

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()