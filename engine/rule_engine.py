
"""
AgriSathi - Rule Engine
=======================

Purpose:
    Apply deterministic agricultural rules to a parsed farmer query
    and retrieve relevant information from the Knowledge Base.

Responsibilities:
    - Process structured queries from QueryParser
    - Match query intent to relevant Knowledge Base records
    - Retrieve crop, pest, fertilizer, and irrigation information
    - Preserve source references
    - Identify missing information
    - Flag chemical-related records for additional validation
    - Return structured candidate information

This module does not:
    - Generate the final conversational response
    - Diagnose crop diseases conclusively
    - Approve pesticide dosages
    - Validate chemical safety independently
    - Invent missing agricultural information

Expected KnowledgeBaseLoader interface:
    loader.get_records(category)
    loader.find_records(category, filters)

The loader dependency is optional at initialization so that this
module can be integrated incrementally.
"""

from typing import Any, Dict, List, Optional


class RuleEngine:
    """Apply agricultural rules to structured farmer queries."""

    SUPPORTED_INTENTS = {
        "crop_information",
        "fertilizer_advice",
        "pest_management",
        "irrigation",
        "weather",
        "mandi_prices",
        "general_agriculture",
        "needs_clarification",
    }

    CATEGORY_BY_INTENT = {
        "crop_information": "crops",
        "fertilizer_advice": "fertilizers",
        "pest_management": "pests",
        "irrigation": "irrigation",
    }

    def __init__(
        self,
        knowledge_base_loader=None,
        weather_service=None,
        mandi_service=None,
    ):
        """
        Initialize the Rule Engine.

        Args:
            knowledge_base_loader:
                Object responsible for loading and querying
                agricultural Knowledge Base records.

            weather_service:
                Optional service for weather information.

            mandi_service:
                Optional service for agricultural market prices.
        """
        self.knowledge_base_loader = knowledge_base_loader
        self.weather_service = weather_service
        self.mandi_service = mandi_service

    # ---------------------------------------------------------
    # Public entry point
    # ---------------------------------------------------------

    def process_query(
        self,
        parsed_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process a query produced by QueryParser.

        Args:
            parsed_result:
                Either the complete result returned by parse_query()
                or the inner parsed query dictionary.

        Returns:
            A structured candidate result for RecommendationEngine.
        """

        if not isinstance(parsed_result, dict):
            return self._error(
                "invalid_input",
                "The parsed query must be a dictionary.",
            )

        # Accept either parse_query()'s full result or its inner query.
        if "query" in parsed_result:
            if parsed_result.get("status") != "success":
                return self._error(
                    "invalid_input",
                    "The query parser did not return a successful result.",
                )

            query = parsed_result["query"]
        else:
            query = parsed_result

        if not isinstance(query, dict):
            return self._error(
                "invalid_input",
                "The parsed query is missing or malformed.",
            )

        intent = query.get("intent")

        if intent not in self.SUPPORTED_INTENTS:
            return self._error(
                "unsupported_intent",
                "The query contains an unsupported intent.",
            )

        if query.get("requires_clarification", False):
            return {
                "status": "needs_clarification",
                "intent": intent,
                "candidate_records": [],
                "sources": [],
                "warnings": [
                    "The farmer's question requires clarification."
                ],
                "clarification_reasons": query.get(
                    "clarification_reasons", []
                ),
                "requires_clarification": True,
                "chemical_verification_required": False,
            }

        if intent == "weather":
            return self._process_weather_query(query)

        if intent == "mandi_prices":
            return self._process_mandi_query(query)

        if intent == "general_agriculture":
            return {
                "status": "needs_clarification",
                "intent": intent,
                "candidate_records": [],
                "sources": [],
                "warnings": [
                    "The agricultural topic could not be identified."
                ],
                "clarification_reasons": [
                    "Ask the farmer to specify the agricultural topic."
                ],
                "requires_clarification": True,
                "chemical_verification_required": False,
            }

        category = self.CATEGORY_BY_INTENT.get(intent)

        if category is None:
            return self._error(
                "unsupported_intent",
                "No rule category is configured for this intent.",
            )

        return self._process_knowledge_query(
            query=query,
            category=category,
        )

    # ---------------------------------------------------------
    # Knowledge Base queries
    # ---------------------------------------------------------

    def _process_knowledge_query(
        self,
        query: Dict[str, Any],
        category: str,
    ) -> Dict[str, Any]:
        """Retrieve applicable Knowledge Base records."""

        if self.knowledge_base_loader is None:
            return self._error(
                "knowledge_base_unavailable",
                "The agricultural Knowledge Base has not been configured.",
            )

        entities = query.get("entities") or {}

        if not isinstance(entities, dict):
            return self._error(
                "invalid_query",
                "The query entities are malformed.",
            )

        crops = entities.get("crops", [])
        pests = entities.get("pests", [])
        symptoms = entities.get("reported_symptoms", [])

        if not isinstance(crops, list):
            return self._error(
                "invalid_query",
                "The crop entities must be a list.",
            )

        if not isinstance(pests, list):
            return self._error(
                "invalid_query",
                "The pest entities must be a list.",
            )

        if not isinstance(symptoms, list):
            return self._error(
                "invalid_query",
                "The reported symptoms must be a list.",
            )

        # If the query contains symptoms but no confirmed target pest,
        # do not assume a diagnosis.
        if category == "pests" and symptoms and not pests:
            return {
                "status": "needs_clarification",
                "intent": query["intent"],
                "candidate_records": [],
                "sources": [],
                "warnings": [
                    "Reported symptoms do not establish a pest or disease diagnosis."
                ],
                "clarification_reasons": [
                    "Ask for more details or request a clear crop image "
                    "if the application supports image input."
                ],
                "requires_clarification": True,
                "chemical_verification_required": False,
            }

        filters = {
            "crops": crops,
            "pests": pests,
            "symptoms": symptoms,
            "location": query.get("location"),
        }

        try:
            records = self._retrieve_records(
                category=category,
                filters=filters,
            )
        except Exception:
            # Do not expose internal exception details to the UI.
            return self._error(
                "knowledge_base_error",
                "The Knowledge Base could not be queried.",
            )

        if not records:
            return {
                "status": "no_verified_information",
                "intent": query["intent"],
                "candidate_records": [],
                "sources": [],
                "warnings": [
                    "No applicable Knowledge Base records were found."
                ],
                "requires_clarification": False,
                "chemical_verification_required": False,
            }

        # Reject obviously mismatched records before creating candidates.
        applicable_records = [
            record
            for record in records
            if isinstance(record, dict)
            and self._record_matches_query(
                record=record,
                filters=filters,
                category=category,
            )
        ]

        if not applicable_records:
            return {
                "status": "no_verified_information",
                "intent": query["intent"],
                "candidate_records": [],
                "sources": [],
                "warnings": [
                    "Available records did not match the query sufficiently."
                ],
                "requires_clarification": False,
                "chemical_verification_required": False,
            }

        sources = self._collect_source_ids(applicable_records)

        chemical_required = (
            category == "pests"
            and any(
                record.get("chemical_options")
                or record.get("chemical_recommendations")
                for record in applicable_records
            )
        )

        warnings = []

        if chemical_required:
            warnings.append(
                "Chemical-related information requires separate "
                "chemical, dosage, applicability, and source validation."
            )

        return {
            "status": "candidate_information_available",
            "intent": query["intent"],
            "category": category,
            "language": query.get("language", "en"),
            "candidate_records": applicable_records,
            "sources": sources,
            "warnings": warnings,
            "requires_clarification": False,
            "chemical_verification_required": chemical_required,
            "safety_validation_required": True,
        }

    def _retrieve_records(
        self,
        category: str,
        filters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Retrieve records through the configured loader.

        Preferred loader interface:
            find_records(category, filters)

        Fallback loader interface:
            get_records(category)

        The fallback performs filtering locally.
        """

        loader = self.knowledge_base_loader

        find_method = getattr(loader, "find_records", None)

        if callable(find_method):
            result = find_method(
                category=category,
                filters=filters,
            )

            if result is None:
                return []

            if not isinstance(result, list):
                raise TypeError(
                    "find_records() must return a list."
                )

            return result

        get_method = getattr(loader, "get_records", None)

        if callable(get_method):
            records = get_method(category)

            if records is None:
                return []

            if not isinstance(records, list):
                raise TypeError(
                    "get_records() must return a list."
                )

            return [
                record
                for record in records
                if isinstance(record, dict)
                and self._record_matches_query(
                    record=record,
                    filters=filters,
                    category=category,
                )
            ]

        raise TypeError(
            "The Knowledge Base loader does not provide "
            "find_records() or get_records()."
        )

    # ---------------------------------------------------------
    # Record applicability
    # ---------------------------------------------------------

    def _record_matches_query(
        self,
        record: Dict[str, Any],
        filters: Dict[str, Any],
        category: str,
    ) -> bool:
        """
        Check whether a record is sufficiently relevant to the query.

        Records may use different schemas. This method supports common
        crop, pest, and symptom fields without assuming that every
        record contains all of them.
        """

        query_crops = set(filters.get("crops") or [])
        query_pests = set(filters.get("pests") or [])
        query_symptoms = set(filters.get("symptoms") or [])

        record_crop = record.get("crop")
        record_crops = record.get("crops", [])

        if isinstance(record_crop, str):
            record_crops = list(record_crops) + [record_crop]

        if not isinstance(record_crops, list):
            record_crops = []

        record_crops = set(
            item for item in record_crops
            if isinstance(item, str)
        )

        record_pest = record.get("pest")
        record_pests = record.get("pests", [])

        if isinstance(record_pest, str):
            record_pests = list(record_pests) + [record_pest]

        if not isinstance(record_pests, list):
            record_pests = []

        record_pests = set(
            item for item in record_pests
            if isinstance(item, str)
        )

        record_symptoms = record.get("symptoms", [])

        if not isinstance(record_symptoms, list):
            record_symptoms = []

        record_symptoms = set(
            item for item in record_symptoms
            if isinstance(item, str)
        )

        # When a crop is specified, reject records explicitly tied
        # to a different crop. Generic records remain eligible.
        if query_crops and record_crops:
            if not query_crops.intersection(record_crops):
                return False

        # When a specific pest is supplied, require a matching pest
        # for pest-specific records.
        if category == "pests" and query_pests and record_pests:
            if not query_pests.intersection(record_pests):
                return False

        # A record with explicitly structured symptoms should match
        # at least one reported symptom when symptoms were supplied.
        if query_symptoms and record_symptoms:
            if not query_symptoms.intersection(record_symptoms):
                return False

        return True

    # ---------------------------------------------------------
    # Source handling
    # ---------------------------------------------------------

    @staticmethod
    def _collect_source_ids(
        records: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Collect source IDs associated with selected records.

        This method preserves identifiers; it does not independently
        verify that sources substantiate the associated claims.
        """

        source_ids = []

        for record in records:
            ids = record.get("source_ids", [])

            if not isinstance(ids, list):
                ids = []

            # Support the alternative field used by some datasets.
            single_source_id = record.get("information_source_ids")

            if isinstance(single_source_id, list):
                ids = ids + single_source_id

            for source_id in ids:
                if (
                    isinstance(source_id, str)
                    and source_id
                    and source_id not in source_ids
                ):
                    source_ids.append(source_id)

        return source_ids

    # ---------------------------------------------------------
    # Weather service integration
    # ---------------------------------------------------------

    def _process_weather_query(
        self,
        query: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Retrieve weather data through the configured service."""

        if self.weather_service is None:
            return self._error(
                "weather_service_unavailable",
                "Weather information is not configured.",
            )

        location = query.get("location")

        if not location:
            return {
                "status": "needs_clarification",
                "intent": "weather",
                "candidate_records": [],
                "sources": [],
                "warnings": [
                    "A location is needed for location-specific weather."
                ],
                "clarification_reasons": [
                    "Ask the farmer for a district, city, or supported location."
                ],
                "requires_clarification": True,
                "chemical_verification_required": False,
            }

        try:
            method = getattr(
                self.weather_service,
                "get_weather",
                None,
            )

            if not callable(method):
                raise TypeError(
                    "Weather service must provide get_weather()."
                )

            weather_result = method(location=location)

        except Exception:
            return self._error(
                "weather_service_error",
                "Weather information could not be retrieved.",
            )

        if not isinstance(weather_result, dict):
            return self._error(
                "invalid_weather_response",
                "The weather service returned an invalid response.",
            )

        if weather_result.get("status") != "success":
            return {
                "status": "external_data_unavailable",
                "intent": "weather",
                "candidate_records": [],
                "sources": [],
                "warnings": [
                    "A successful live weather response was unavailable."
                ],
                "external_data": None,
                "requires_clarification": False,
                "chemical_verification_required": False,
            }

        return {
            "status": "candidate_information_available",
            "intent": "weather",
            "category": "weather",
            "candidate_records": [],
            "external_data": weather_result,
            "sources": self._extract_external_source(weather_result),
            "warnings": [
                "Weather-dependent agricultural advice requires "
                "additional crop and context checks."
            ],
            "requires_clarification": False,
            "chemical_verification_required": False,
            "safety_validation_required": True,
        }

    # ---------------------------------------------------------
    # Mandi service integration
    # ---------------------------------------------------------

    def _process_mandi_query(
        self,
        query: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Retrieve market prices through the configured service."""

        if self.mandi_service is None:
            return self._error(
                "mandi_service_unavailable",
                "Mandi price information is not configured.",
            )

        entities = query.get("entities") or {}
        crops = entities.get("crops", [])

        if not crops:
            return {
                "status": "needs_clarification",
                "intent": "mandi_prices",
                "candidate_records": [],
                "sources": [],
                "warnings": [
                    "The crop for the market-price query is unknown."
                ],
                "clarification_reasons": [
                    "Ask the farmer which crop's price is needed."
                ],
                "requires_clarification": True,
                "chemical_verification_required": False,
            }

        location = query.get("location")

        try:
            method = getattr(
                self.mandi_service,
                "get_prices",
                None,
            )

            if not callable(method):
                raise TypeError(
                    "Mandi service must provide get_prices()."
                )

            market_result = method(
                crop=crops[0],
                location=location,
            )

        except Exception:
            return self._error(
                "mandi_service_error",
                "Market-price information could not be retrieved.",
            )

        if not isinstance(market_result, dict):
            return self._error(
                "invalid_mandi_response",
                "The mandi service returned an invalid response.",
            )

        if market_result.get("status") != "success":
            return {
                "status": "external_data_unavailable",
                "intent": "mandi_prices",
                "candidate_records": [],
                "sources": [],
                "warnings": [
                    "A successful market-price response was unavailable."
                ],
                "external_data": None,
                "requires_clarification": False,
                "chemical_verification_required": False,
            }

        return {
            "status": "candidate_information_available",
            "intent": "mandi_prices",
            "category": "mandi_prices",
            "candidate_records": [],
            "external_data": market_result,
            "sources": self._extract_external_source(market_result),
            "warnings": [
                "Market prices must retain their market, date, and units."
            ],
            "requires_clarification": False,
            "chemical_verification_required": False,
            "safety_validation_required": True,
        }

    @staticmethod
    def _extract_external_source(
        result: Dict[str, Any],
    ) -> List[str]:
        """Extract source identifiers or provider labels."""

        source = result.get("source")

        if isinstance(source, str) and source.strip():
            return [source.strip()]

        source_id = result.get("source_id")

        if isinstance(source_id, str) and source_id.strip():
            return [source_id.strip()]

        return []

    # ---------------------------------------------------------
    # Error handling
    # ---------------------------------------------------------

    @staticmethod
    def _error(
        code: str,
        message: str,
    ) -> Dict[str, Any]:
        """Return a consistent structured error."""

        return {
            "status": "error",
            "error_code": code,
            "message": message,
            "candidate_records": [],
            "sources": [],
            "warnings": [],
            "requires_clarification": False,
            "chemical_verification_required": False,
        }


# -------------------------------------------------------------
# Convenience function
# -------------------------------------------------------------

def process_query(
    parsed_result: Dict[str, Any],
    knowledge_base_loader=None,
    weather_service=None,
    mandi_service=None,
) -> Dict[str, Any]:
    """
    Process a parsed query without requiring the caller to
    instantiate RuleEngine directly.
    """

    engine = RuleEngine(
        knowledge_base_loader=knowledge_base_loader,
        weather_service=weather_service,
        mandi_service=mandi_service,
    )

    return engine.process_query(parsed_result)
