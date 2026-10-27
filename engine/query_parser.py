"""
AgriSathi Query Parser
----------------------
Parses agricultural questions from farmers.

Features:
- English, Hindi, and Punjabi keyword recognition
- Case-insensitive English matching
- Crop and pest entity extraction
- Agricultural intent classification
- General questions do not require unnecessary clarification
- Chemical dosage questions are flagged for safety validation
- Consistent output schema for the AgriSathi backend

This module identifies the user's intent and entities.
It does not generate or approve agricultural recommendations.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any


class QueryParser:
    """Parse multilingual agricultural questions."""

    # ---------------------------------------------------------
    # 1. Crop names and their aliases
    # ---------------------------------------------------------

    CROP_ALIASES = {
        "wheat": [
            "wheat",
            "गेहूं",
            "गेहूँ",
            "कनक",
            "ਕਣਕ",
        ],
        "rice": [
            "rice",
            "paddy",
            "धान",
            "चावल",
            "ਝੋਨਾ",
            "ਚੌਲ",
        ],
        "maize": [
            "maize",
            "corn",
            "मक्का",
            "ਮੱਕੀ",
        ],
        "tomato": [
            "tomato",
            "टमाटर",
            "ਟਮਾਟਰ",
        ],
        "potato": [
            "potato",
            "आलू",
            "ਆਲੂ",
        ],
        "sugarcane": [
            "sugarcane",
            "sugar cane",
            "गन्ना",
            "ਗੰਨਾ",
        ],
        "cotton": [
            "cotton",
            "कपास",
            "ਰੂੰ",
            "ਕਪਾਹ",
        ],
        "mustard": [
            "mustard",
            "सरसों",
            "सरसो",
            "ਸਰ੍ਹੋਂ",
        ],
        "soybean": [
            "soybean",
            "soya bean",
            "सोयाबीन",
            "ਸੋਇਆਬੀਨ",
        ],
        "chickpea": [
            "chickpea",
            "chickpeas",
            "gram",
            "चना",
            "ਚਣਾ",
        ],
        "lentil": [
            "lentil",
            "masoor",
            "मसूर",
            "ਮਸੂਰ",
        ],
        "onion": [
            "onion",
            "प्याज",
            "प्याज़",
            "ਪਿਆਜ਼",
        ],
        "garlic": [
            "garlic",
            "लहसुन",
            "ਲਸਣ",
        ],
        "chilli": [
            "chilli",
            "chili",
            "pepper",
            "मिर्च",
            "ਮਿਰਚ",
        ],
        "brinjal": [
            "brinjal",
            "eggplant",
            "बैंगन",
            "ਬੈਂਗਣ",
        ],
        "groundnut": [
            "groundnut",
            "peanut",
            "मूंगफली",
            "ਮੂੰਗਫਲੀ",
        ],
        "banana": [
            "banana",
            "केला",
            "ਕੇਲਾ",
        ],
        "mango": [
            "mango",
            "आम",
            "ਅੰਬ",
        ],
        "apple": [
            "apple",
            "सेब",
            "ਸੇਬ",
        ],
        "grape": [
            "grape",
            "grapes",
            "अंगूर",
            "ਅੰਗੂਰ",
        ],
        "pea": [
            "pea",
            "peas",
            "मटर",
            "ਮਟਰ",
        ],
        "cabbage": [
            "cabbage",
            "पत्ता गोभी",
            "ਬੰਦ ਗੋਭੀ",
        ],
        "cauliflower": [
            "cauliflower",
            "फूलगोभी",
            "ਫੁੱਲ ਗੋਭੀ",
        ],
        "okra": [
            "okra",
            "ladyfinger",
            "भिंडी",
            "ਭਿੰਡੀ",
        ],
        "sunflower": [
            "sunflower",
            "सूरजमुखी",
            "ਸੂਰਜਮੁਖੀ",
        ],
        "millet": [
            "millet",
            "बाजरा",
            "बाजरी",
            "ਬਾਜਰਾ",
        ],
        "barley": [
            "barley",
            "जौ",
            "ਜੌਂ",
        ],
        "oat": [
            "oat",
            "oats",
            "जई",
            "ਜਵੀ",
        ],
        "jute": [
            "jute",
            "जूट",
            "ਜੂਟ",
        ],
        "turmeric": [
            "turmeric",
            "हल्दी",
            "ਹਲਦੀ",
        ],
        "ginger": [
            "ginger",
            "अदरक",
            "ਅਦਰਕ",
        ],
    }

    # ---------------------------------------------------------
    # 2. Intent keywords
    # ---------------------------------------------------------

    INTENT_KEYWORDS = {
        "pest_management": [
            "pest",
            "pests",
            "insect",
            "insects",
            "bug",
            "bugs",
            "infestation",
            "pest control",
            "control pest",
            "control pests",
            "manage pest",
            "manage pests",
            "disease",
            "diseases",
            "fungus",
            "fungal",
            "infection",
            "infected",
            "yellow leaves",
            "yellowing leaves",
            "leaf spots",
            "wilting",
            "spots on leaves",
            "crop damage",
            "plant damage",
            "कीट",
            "कीटों",
            "कीड़ा",
            "कीड़े",
            "रोग",
            "बीमारी",
            "फफूंद",
            "पत्ते पीले",
            "पत्तियां पीली",
            "ਪੌਦਿਆਂ ਦੇ ਕੀੜੇ",
            "ਕੀੜੇ",
            "ਕੀਟ",
            "ਬਿਮਾਰੀ",
            "ਰੋਗ",
            "ਫਫੂੰਦੀ",
            "ਪੀਲੇ ਪੱਤੇ",
        ],
        "fertilizer_advice": [
            "fertilizer",
            "fertiliser",
            "fertilizers",
            "fertilisers",
            "manure",
            "nutrient",
            "nutrients",
            "npk",
            "urea",
            "dap",
            "compost",
            "खाद",
            "उर्वरक",
            "खाद की मात्रा",
            "ਖਾਦ",
            "ਯੂਰੀਆ",
            "ਖਾਦ ਦੀ ਮਾਤਰਾ",
        ],
        "irrigation": [
            "irrigation",
            "irrigate",
            "watering",
            "water requirement",
            "water requirements",
            "how much water",
            "water my crop",
            "paani",
            "सिंचाई",
            "पानी",
            "कितना पानी",
            "पਾਣੀ",
            "ਸਿੰਚਾਈ",
            "ਕਿੰਨਾ ਪਾਣੀ",
        ],
        "weather": [
            "weather",
            "temperature",
            "rainfall",
            "rain",
            "forecast",
            "humidity",
            "मौसम",
            "बारिश",
            "तापमान",
            "मौसम पूर्वानुमान",
            "ਮੌਸਮ",
            "ਮੀਂਹ",
            "ਤਾਪਮਾਨ",
        ],
        "market_price": [
            "mandi",
            "market price",
            "crop price",
            "selling price",
            "price of",
            "price for",
            "today's price",
            "today price",
            "modal price",
            "भाव",
            "मंडी",
            "कीमत",
            "दाम",
            "आज का भाव",
            "ਮੰਡੀ",
            "ਭਾਅ",
            "ਕੀਮਤ",
        ],
        "sowing": [
            "sowing",
            "when to sow",
            "planting time",
            "planting season",
            "seed sowing",
            "播种",
            "बुवाई",
            "बोने का समय",
            "ਬਿਜਾਈ",
            "ਬੀਜਣ ਦਾ ਸਮਾਂ",
        ],
        "harvesting": [
            "harvesting",
            "harvest",
            "harvest time",
            "when to harvest",
            "कटाई",
            "फसल काटना",
            "कटाई का समय",
            "ਵਾਢੀ",
            "ਫ਼ਸਲ ਕੱਟਣ",
        ],
        "crop_information": [
            "tell me about",
            "information about",
            "information on",
            "details about",
            "requirements of",
            "requirements for",
            "soil for",
            "soil requirement",
            "soil requirements",
            "season for",
            "season of",
            "growing conditions",
            "crop information",
            "फसल की जानकारी",
            "मिट्टी",
            "मिट्टी की आवश्यकता",
            "ਫ਼ਸਲ ਬਾਰੇ",
            "ਮਿੱਟੀ",
        ],
    }

    # ---------------------------------------------------------
    # 3. Pest and symptom keywords
    # ---------------------------------------------------------

    PEST_ALIASES = {
        "aphids": [
            "aphid",
            "aphids",
            "एफिड",
            "चेपा",
            "ਤੇਲਾ",
        ],
        "whitefly": [
            "whitefly",
            "whiteflies",
            "सफेद मक्खी",
            "ਚਿੱਟੀ ਮੱਖੀ",
        ],
        "bollworm": [
            "bollworm",
            "bollworms",
            "सुंडी",
            "ਗੁਲਾਬੀ ਸੁੰਡੀ",
        ],
        "stem_borer": [
            "stem borer",
            "तना छेदक",
            "ਤਣਾ ਛੇਦਕ",
        ],
        "leaf_curl": [
            "leaf curl",
            "leaf curling",
            "पत्ती मोड़क",
            "पत्तियां मुड़ना",
            "ਪੱਤੇ ਮੁੜਨਾ",
        ],
        "powdery_mildew": [
            "powdery mildew",
            "पाउडरी मिल्ड्यू",
        ],
        "rust": [
            "rust",
            "rust disease",
            "रस्ट",
            "रतुआ",
            "ਕੁੰਗੀ",
        ],
        "blast": [
            "blast",
            "blast disease",
            "झोंका रोग",
        ],
    }

    SYMPTOM_ALIASES = {
        "yellow_leaves": [
            "yellow leaves",
            "yellowing leaves",
            "leaves turning yellow",
            "leaves are yellow",
            "पत्ते पीले",
            "पत्तियां पीली",
            "पत्ते पीले पड़ना",
            "ਪੱਤੇ ਪੀਲੇ",
        ],
        "wilting": [
            "wilting",
            "wilting plants",
            "plant is wilting",
            "पौधा मुरझाना",
            "पौधे मुरझा रहे",
            "ਬੂਟਾ ਮੁਰਝਾਉਣਾ",
        ],
        "leaf_spots": [
            "leaf spots",
            "spots on leaves",
            "brown spots",
            "black spots",
            "पत्तों पर धब्बे",
            "पत्तियों पर धब्बे",
            "ਪੱਤਿਆਂ ਉੱਤੇ ਧੱਬੇ",
        ],
        "holes_in_leaves": [
            "holes in leaves",
            "holes in the leaves",
            "leaves have holes",
            "पत्तों में छेद",
            "पत्तियों में छेद",
            "ਪੱਤਿਆਂ ਵਿੱਚ ਛੇਕ",
        ],
        "stunted_growth": [
            "stunted growth",
            "not growing",
            "poor growth",
            "विकास रुकना",
            "वृद्धि रुकना",
            "ਵਾਧਾ ਰੁਕਣਾ",
        ],
    }

    CHEMICAL_KEYWORDS = [
        "pesticide dosage",
        "pesticide dose",
        "chemical dosage",
        "chemical dose",
        "dosage of",
        "dose of",
        "how much pesticide",
        "how much chemical",
        "spray quantity",
        "application rate",
        "कीटनाशक की मात्रा",
        "दवा की मात्रा",
        "कितनी दवा",
        "ਕੀਟਨਾਸ਼ਕ ਦੀ ਮਾਤਰਾ",
        "ਦਵਾਈ ਦੀ ਮਾਤਰਾ",
    ]

    # ---------------------------------------------------------
    # 4. Initialization
    # ---------------------------------------------------------

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

        self.crop_aliases = self._prepare_aliases(
            self.CROP_ALIASES
        )
        self.pest_aliases = self._prepare_aliases(
            self.PEST_ALIASES
        )
        self.symptom_aliases = self._prepare_aliases(
            self.SYMPTOM_ALIASES
        )

    # ---------------------------------------------------------
    # 5. Text normalization
    # ---------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize Unicode and whitespace; casefold English text."""

        text = unicodedata.normalize("NFKC", text or "")
        text = text.casefold()
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @classmethod
    def _prepare_aliases(cls, mapping):
        """Prepare aliases and sort longer phrases first."""

        prepared = []

        for canonical_name, aliases in mapping.items():
            for alias in aliases:
                normalized_alias = cls._normalize(alias)

                if normalized_alias:
                    prepared.append(
                        (normalized_alias, canonical_name)
                    )

            # Also recognize the canonical English name.
            canonical_normalized = cls._normalize(
                canonical_name.replace("_", " ")
            )

            if canonical_normalized:
                prepared.append(
                    (canonical_normalized, canonical_name)
                )

        # Longest matches first help recognize multiword crop names.
        prepared.sort(
            key=lambda item: len(item[0]),
            reverse=True,
        )

        return prepared

    @staticmethod
    def _contains_phrase(text: str, phrase: str) -> bool:
        """
        Match Latin aliases on word boundaries.
        Match non-Latin aliases by normalized substring.
        """

        if not phrase:
            return False

        if re.search(r"[a-z0-9]", phrase):
            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(phrase)
                + r"(?![a-z0-9])"
            )
            return re.search(pattern, text) is not None

        return phrase in text

    @classmethod
    def _extract_entities(cls, text: str, prepared_aliases):
        """Extract unique canonical entity names."""

        found = []
        occupied_spans = []

        for alias, canonical_name in prepared_aliases:
            for match in re.finditer(
                r"(?<![a-z0-9])"
                + re.escape(alias)
                + r"(?![a-z0-9])"
                if re.search(r"[a-z0-9]", alias)
                else re.escape(alias),
                text,
            ):
                start, end = match.span()

                # Avoid matching a shorter alias inside a longer match.
                overlaps = any(
                    start < existing_end
                    and end > existing_start
                    for existing_start, existing_end in occupied_spans
                )

                if overlaps:
                    continue

                occupied_spans.append((start, end))

                if canonical_name not in found:
                    found.append(canonical_name)

                break

        return found

    # ---------------------------------------------------------
    # 6. Language detection
    # ---------------------------------------------------------

    @staticmethod
    def _detect_language(text: str) -> dict[str, Any]:
        """Detect Hindi, Punjabi, or English using script characters."""

        devanagari_count = len(
            re.findall(r"[\u0900-\u097F]", text)
        )

        gurmukhi_count = len(
            re.findall(r"[\u0A00-\u0A7F]", text)
        )

        if gurmukhi_count > 0 and gurmukhi_count >= devanagari_count:
            return {
                "language": "pa",
                "method": "script_detection",
                "confidence": "high",
                "selected_language": "pa",
                "selection_method": "script_detection",
            }

        if devanagari_count > 0:
            return {
                "language": "hi",
                "method": "script_detection",
                "confidence": "high",
                "selected_language": "hi",
                "selection_method": "script_detection",
            }

        return {
            "language": "en",
            "method": "script_detection",
            "confidence": "medium",
            "selected_language": "en",
            "selection_method": "script_detection",
        }

    # ---------------------------------------------------------
    # 7. Intent classification
    # ---------------------------------------------------------

    @classmethod
    def _detect_intent(cls, text: str):
        """Return the strongest matching agricultural intent."""

        matched = {}

        for intent, keywords in cls.INTENT_KEYWORDS.items():
            matches = []

            for keyword in keywords:
                normalized_keyword = cls._normalize(keyword)

                if cls._contains_phrase(text, normalized_keyword):
                    matches.append(normalized_keyword)

            if matches:
                matched[intent] = matches

        # More specific intents should win over generic crop information.
        priority = [
            "market_price",
            "weather",
            "fertilizer_advice",
            "pest_management",
            "irrigation",
            "sowing",
            "harvesting",
            "crop_information",
        ]

        if not matched:
            return (
                "general_agriculture",
                "low",
                [],
                [],
            )

        selected_intent = max(
            matched,
            key=lambda intent: (
                priority.index(intent)
                if intent in priority
                else len(priority)
            ),
        )

        matched_keywords = matched[selected_intent]

        if len(matched_keywords) >= 2:
            confidence = "high"
        else:
            confidence = "medium"

        alternatives = [
            intent
            for intent in matched
            if intent != selected_intent
        ]

        return (
            selected_intent,
            confidence,
            matched_keywords,
            alternatives,
        )

    # ---------------------------------------------------------
    # 8. Chemical dosage detection
    # ---------------------------------------------------------

    @classmethod
    def _requests_chemical_dosage(cls, text: str) -> bool:
        return any(
            cls._contains_phrase(
                text,
                cls._normalize(keyword),
            )
            for keyword in cls.CHEMICAL_KEYWORDS
        )

    # ---------------------------------------------------------
    # 9. Main parser
    # ---------------------------------------------------------

    def parse(
        self,
        message: str,
        language: str | None = None,
        location: str | None = None,
        crop: str | None = None,
    ) -> dict[str, Any]:
        """
        Parse a farmer's message.

        The return structure is compatible with the parser output
        previously used by AgriSathi.
        """

        if not isinstance(message, str) or not message.strip():
            return {
                "status": "error",
                "error": "Please enter a non-empty agricultural question.",
            }

        original_message = message.strip()
        normalized_message = self._normalize(original_message)

        language_detection = self._detect_language(
            original_message
        )

        selected_language = (
            language
            if language in {"en", "hi", "pa"}
            else language_detection["language"]
        )

        # Extract crops, pests, and symptoms.
        crops = self._extract_entities(
            normalized_message,
            self.crop_aliases,
        )

        pests = self._extract_entities(
            normalized_message,
            self.pest_aliases,
        )

        symptoms = self._extract_entities(
            normalized_message,
            self.symptom_aliases,
        )

        # A crop explicitly supplied by the caller takes precedence.
        if crop:
            normalized_crop = self._normalize(crop)

            for alias, canonical_name in self.crop_aliases:
                if normalized_crop == alias:
                    crops = [canonical_name]
                    break
            else:
                # Preserve an explicitly supplied crop if it is not
                # present in the built-in alias dictionary.
                if normalized_crop not in crops:
                    crops = [normalized_crop]

        # Detect intent.
        (
            intent,
            intent_confidence,
            matched_keywords,
            alternative_intents,
        ) = self._detect_intent(normalized_message)

        chemical_dosage_requested = (
            self._requests_chemical_dosage(
                normalized_message
            )
        )

        # Chemical-specific questions need stricter handling.
        if chemical_dosage_requested:
            intent = "pest_management"

        # Clarification rules:
        # A known crop is sufficient for a general pest question.
        # A specific pest or symptom is helpful, but not mandatory.
        requires_clarification = False
        clarification_reasons = []

        if intent in {
            "pest_management",
            "fertilizer_advice",
            "irrigation",
            "sowing",
            "harvesting",
            "crop_information",
        } and not crops:
            requires_clarification = True
            clarification_reasons.append(
                "Please specify which crop you are asking about."
            )

        # Weather needs a location for location-specific advice.
        if intent == "weather" and not (
            location and location.strip()
        ):
            requires_clarification = True
            clarification_reasons.append(
                "Please provide your city or district for local weather information."
            )

        # Market-price requests need the crop.
        if intent == "market_price" and not crops:
            requires_clarification = True
            clarification_reasons.append(
                "Please specify the crop whose market price you want."
            )

        # Dosage requests are flagged for safety checks, not guessed.
        if chemical_dosage_requested:
            clarification_reasons.append(
                "Chemical dosage requires a verified product, crop, target pest, and authoritative source."
            )

            if not crops:
                requires_clarification = True
                clarification_reasons.append(
                    "Please specify the crop involved."
                )

        query_result = {
            "original_message": original_message,
            "normalized_message": normalized_message,
            "language": selected_language,
            "language_detection": language_detection,
            "intent": intent,
            "intent_confidence": intent_confidence,
            "matched_keywords": matched_keywords,
            "alternative_intents": alternative_intents,
            "entities": {
                "crops": crops,
                "pests": pests,
                "reported_symptoms": symptoms,
            },
            "location": location,
            "requires_clarification": requires_clarification,
            "clarification_reasons": clarification_reasons,
            "chemical_dosage_requested": chemical_dosage_requested,
            "llm_enhanced": False,
        }

        return {
            "status": "success",
            "query": query_result,
        }