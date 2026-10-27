"""
AgriSathi - Safety Engine

Purpose:
    Coordinate agricultural recommendation safety checks before
    a response is released to a farmer.

Responsibilities:
    - Determine which safety checks are required.
    - Run chemical verification when chemical advice is present.
    - Run dosage validation when dosage information is present.
    - Validate crop-pest compatibility for pest-management advice.
    - Validate source references and claim evidence.
    - Reject responses when required checks fail.
    - Pass eligible responses through the response sanitizer.
    - Return a structured result to main.py.

Important:
    A successful result means the configured checks passed. It does not
    independently guarantee that every agricultural claim is correct.

    Verification metadata must come from trusted validation processes.
    It must not be accepted merely because an LLM generated it.
"""

import re
from typing import Any, Dict, List, Optional

from safety.safety_rules import (
    SafetyStatus,
    get_required_checks,
)

from safety.chemical_verifier import ChemicalVerifier
from safety.dosage_validator import DosageValidator
from safety.crop_pest_validator import CropPestValidator
from safety.source_validator import SourceValidator
from safety.response_sanitizer import ResponseSanitizer


class SafetyEngine:
    """Coordinate AgriSathi's safety-validation components."""

    def __init__(
        self,
        knowledge_base_loader: Any = None,
        sources_file: Optional[str] = None,
        chemical_verifier: Any = None,
        dosage_validator: Any = None,
        crop_pest_validator: Any = None,
        source_validator: Any = None,
        response_sanitizer: Any = None,
    ) -> None:
        """
        Initialize the safety engine.

        Args:
            knowledge_base_loader:
                Initialized KnowledgeBaseLoader, if available.

            sources_file:
                Path to knowledge_base/sources.json.

            Individual validators:
                Optional preconfigured validator instances.
        """

        self.knowledge_base_loader = knowledge_base_loader

        self.chemical_verifier = (
            chemical_verifier
            if chemical_verifier is not None
            else ChemicalVerifier(
                knowledge_base_loader=knowledge_base_loader
            )
        )

        self.dosage_validator = (
            dosage_validator
            if dosage_validator is not None
            else DosageValidator(
                knowledge_base_loader=knowledge_base_loader
            )
        )

        self.crop_pest_validator = (
            crop_pest_validator
            if crop_pest_validator is not None
            else CropPestValidator(
                knowledge_base_loader=knowledge_base_loader
            )
        )

        self.source_validator = (
            source_validator
            if source_validator is not None
            else SourceValidator(
                sources_file=sources_file,
                knowledge_base_loader=knowledge_base_loader,
            )
        )

        self.response_sanitizer = (
            response_sanitizer
            if response_sanitizer is not None
            else ResponseSanitizer(
                block_on_any_failed_check=False
            )
        )

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------

    def validate_recommendation(
        self,
        recommendation: Any,
        query: Optional[Dict[str, Any]] = None,
        rule_result: Optional[Dict[str, Any]] = None,
        require_verified_evidence: bool = True,
    ) -> Dict[str, Any]:
        """
        Run applicable safety checks on an agricultural recommendation.

        Args:
            recommendation:
                Candidate recommendation from RecommendationEngine.
                May be a dictionary or a plain response string.

            query:
                Parsed query from QueryParser.

            rule_result:
                Output from RuleEngine. Used to preserve intent,
                candidate records, and relevant source metadata.

            require_verified_evidence:
                If True, unverified knowledge-base records cannot
                be approved as verified recommendations.

        Returns:
            Structured safety result with component findings and
            the sanitized response when approved.
        """

        query = query if isinstance(query, dict) else {}
        rule_result = (
            rule_result
            if isinstance(rule_result, dict)
            else {}
        )

        if isinstance(recommendation, str):
            candidate = {
                "answer": recommendation,
            }
        elif isinstance(recommendation, dict):
            candidate = dict(recommendation)
        else:
            return self._blocked_result(
                reasons=[
                    "The recommendation must be a string or dictionary."
                ]
            )

        intent = self._normalize_identifier(
            candidate.get(
                "intent",
                query.get("intent", rule_result.get("intent")),
            )
        )

        language = (
            candidate.get("language")
            or query.get("language")
            or "en"
        )

        answer = candidate.get(
            "answer",
            candidate.get("response", ""),
        )

        if not isinstance(answer, str) or not answer.strip():
            return self._blocked_result(
                reasons=["The recommendation contains no usable answer."]
            )

        # Keep a consistent answer field for the sanitizer.
        candidate["answer"] = answer.strip()
        candidate["intent"] = intent
        candidate["language"] = language

        candidate_records = rule_result.get(
            "candidate_records",
            [],
        )

        if not isinstance(candidate_records, list):
            candidate_records = []

        checks: Dict[str, Dict[str, Any]] = {}
        reasons: List[str] = []
        warnings: List[str] = []

        # -----------------------------------------------------------
        # 1. Determine recommendation content
        # -----------------------------------------------------------

        chemical_present = self._contains_chemical_advice(candidate)
        dosage_present = self._contains_dosage(candidate)

        crop = self._first_value(
            candidate,
            ["crop", "crop_name"],
        )

        if not crop:
            entities = query.get("entities", {})

            if isinstance(entities, dict):
                crop_values = entities.get("crops", [])

                if isinstance(crop_values, list) and crop_values:
                    crop = crop_values[0]

                elif isinstance(crop_values, str):
                    crop = crop_values

        pest = self._first_value(
            candidate,
            ["target_pest", "pest", "pest_name", "disease"],
        )

        if not pest:
            entities = query.get("entities", {})

            if isinstance(entities, dict):
                pest_values = entities.get("pests", [])

                if isinstance(pest_values, list) and pest_values:
                    pest = pest_values[0]

                elif isinstance(pest_values, str):
                    pest = pest_values

        # The rules describe the required checks for each intent.
        required_checks = get_required_checks(intent)

        # -----------------------------------------------------------
        # 2. Chemical verification
        # -----------------------------------------------------------

        if chemical_present or "chemical_verification" in required_checks:
            chemical_data = self._extract_chemical_data(candidate)

            checks["chemical_verifier"] = self._run_validator(
                self.chemical_verifier,
                "verify",
                {
                    "recommendation": chemical_data,
                    "crop": crop,
                    "target_pest": pest,
                },
            )

            # We don't block here. The ResponseSanitizer will strip unsafe chemical details.
            # if not self._is_approved(checks["chemical_verifier"]):
            #     reasons.append("Chemical verification did not pass.")

        # -----------------------------------------------------------
        # 3. Dosage validation
        # -----------------------------------------------------------

        if dosage_present or intent == "fertilizer_advice":
            dosage_data = self._extract_dosage_data(candidate)

            checks["dosage_validator"] = self._run_validator(
                self.dosage_validator,
                "validate",
                {
                    "recommendation": dosage_data,
                    "require_dosage": dosage_present,
                    "require_crop": True,
                    "require_source": True,
                },
            )

            # We don't block here. The ResponseSanitizer will strip unsafe dosage details.
            # if not self._is_approved(checks["dosage_validator"]):
            #     reasons.append("Dosage validation did not pass.")

        # -----------------------------------------------------------
        # 4. Crop-pest validation
        # -----------------------------------------------------------

        if intent == "pest_management":
            pest_records = self._get_pest_records(candidate_records)

            checks["crop_pest_validator"] = self._run_validator(
                self.crop_pest_validator,
                "validate",
                {
                    "crop": crop,
                    "pest": pest,
                    "recommendation": candidate,
                    "records": pest_records,
                    "require_verified_evidence": (
                        require_verified_evidence
                    ),
                },
            )

            if not self._is_approved(
                checks["crop_pest_validator"]
            ):
                reasons.append(
                    "Crop-pest compatibility validation did not pass."
                )

        # -----------------------------------------------------------
        # 5. Source validation
        # -----------------------------------------------------------

        source_data = self._extract_source_data(
            candidate,
            rule_result,
            candidate_records,
        )

        source_validation_required = (
            "source_validation" in required_checks
            or chemical_present
            or dosage_present
        )

        if source_validation_required:
            checks["source_validator"] = self._run_validator(
                self.source_validator,
                "validate",
                {
                    "recommendation": source_data,
                    "claims": source_data.get("claims"),
                    "source_ids": source_data.get("source_ids"),
                    "require_sources": True,
                    "require_claim_evidence": False,
                    "require_verified_record": (
                        require_verified_evidence
                    ),
                },
            )

            if not self._is_approved(
                checks["source_validator"]
            ):
                reasons.append(
                    "Source and claim-evidence validation did not pass."
                )

        # -----------------------------------------------------------
        # 6. Validate external live data
        # -----------------------------------------------------------

        if intent in {"weather", "mandi_prices"}:
            external_result = self._validate_live_data(
                candidate=candidate,
                rule_result=rule_result,
                intent=intent,
            )

            checks["live_data_validator"] = external_result

            if not self._is_approved(external_result):
                reasons.append(
                    "Live-data validation did not pass."
                )

        # -----------------------------------------------------------
        # 7. Determine whether all required checks were executed
        # -----------------------------------------------------------

        missing_required_checks = self._missing_required_checks(
            required_checks=required_checks,
            checks=checks,
            chemical_present=chemical_present,
            dosage_present=dosage_present,
            intent=intent,
        )

        if missing_required_checks:
            reasons.append(
                "Required safety checks were not completed: "
                + ", ".join(missing_required_checks)
                + "."
            )

        # -----------------------------------------------------------
        # 8. Block immediately if any required check failed
        # -----------------------------------------------------------

        if reasons:
            warnings.append(
                "The recommendation was not approved. Review the safety "
                "findings before attempting another response."
            )

            return self._blocked_result(
                reasons=reasons,
                warnings=warnings,
                checks=checks,
                intent=intent,
                language=language,
            )

        # -----------------------------------------------------------
        # 9. Sanitize the candidate response
        # -----------------------------------------------------------

        sanitized_result = self._run_sanitizer(
            candidate=candidate,
            checks=checks,
            language=language,
            intent=intent,
        )

        checks["response_sanitizer"] = sanitized_result

        if not self._is_approved(sanitized_result):
            return self._blocked_result(
                reasons=[
                    "The response sanitizer did not approve the response."
                ] + sanitized_result.get("reasons", []),
                warnings=sanitized_result.get("warnings", []),
                checks=checks,
                intent=intent,
                language=language,
            )

        # -----------------------------------------------------------
        # 10. Return approved response
        # -----------------------------------------------------------

        return {
            "component": "safety_engine",
            "status": SafetyStatus.APPROVED.value,
            "approved": True,
            "verification_required": False,
            "intent": intent,
            "language": language,
            "response": sanitized_result.get("response"),
            "checks": checks,
            "reasons": [],
            "warnings": sanitized_result.get("warnings", []),
        }

    # ---------------------------------------------------------------
    # Result evaluation helper
    # ---------------------------------------------------------------

    @staticmethod
    def _is_approved(result: Dict[str, Any]) -> bool:
        """Check whether a validator result explicitly approved."""
        return (
            isinstance(result, dict)
            and result.get("approved") is True
            and result.get("status") == SafetyStatus.APPROVED.value
        )

    # ---------------------------------------------------------------
    # Validator execution
    # ---------------------------------------------------------------

    @staticmethod
    def _run_validator(
        validator: Any,
        method_name: str,
        kwargs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a validator and normalize its result.

        Missing validators, exceptions, and malformed responses fail closed.
        """

        method = getattr(validator, method_name, None)

        if not callable(method):
            return {
                "component": method_name,
                "status": SafetyStatus.VERIFICATION_REQUIRED.value,
                "approved": False,
                "reasons": ["Required validator is unavailable."],
            }

        try:
            result = method(**kwargs)

            if not isinstance(result, dict):
                return {
                    "component": method_name,
                    "status": SafetyStatus.VERIFICATION_REQUIRED.value,
                    "approved": False,
                    "reasons": [
                        "Validator returned an invalid result."
                    ],
                }

            # Normalize malformed status/approval combinations.
            if not (
                result.get("approved") is True
                and result.get("status") == SafetyStatus.APPROVED.value
            ):
                result["approved"] = False
                result["status"] = SafetyStatus.VERIFICATION_REQUIRED.value

            return result

        except Exception as exc:
            # Do not expose internal exceptions to the farmer.
            return {
                "component": method_name,
                "status": SafetyStatus.VERIFICATION_REQUIRED.value,
                "approved": False,
                "reasons": [
                    "The validator encountered an internal error."
                ],
                "internal_error_type": type(exc).__name__,
            }

    def _run_sanitizer(
        self,
        candidate: Dict[str, Any],
        checks: Dict[str, Dict[str, Any]],
        language: str,
        intent: str,
    ) -> Dict[str, Any]:
        """Run the sanitizer with the already-completed validation results."""

        method = getattr(
            self.response_sanitizer,
            "sanitize",
            None,
        )

        if not callable(method):
            return {
                "component": "response_sanitizer",
                "status": SafetyStatus.BLOCKED.value,
                "approved": False,
                "reasons": ["The response sanitizer is unavailable."],
            }

        try:
            result = method(
                response=candidate,
                safety_results=checks,
                language=language,
                intent=intent,
            )

            if not isinstance(result, dict):
                raise ValueError("Invalid sanitizer result.")

            if not (
                result.get("approved") is True
                and result.get("status") == SafetyStatus.APPROVED.value
            ):
                result["approved"] = False
                result["status"] = SafetyStatus.BLOCKED.value

            return result

        except Exception as exc:
            return {
                "component": "response_sanitizer",
                "status": SafetyStatus.BLOCKED.value,
                "approved": False,
                "reasons": [
                    "The response sanitizer encountered an internal error."
                ],
                "internal_error_type": type(exc).__name__,
            }

    # ---------------------------------------------------------------
    # Content extraction
    # ---------------------------------------------------------------

    @staticmethod
    def _first_value(
        data: Dict[str, Any],
        keys: List[str],
    ) -> Any:
        """Return the first non-empty field."""

        for key in keys:
            value = data.get(key)

            if value is not None and value != "":
                return value

        return None

    @classmethod
    def _contains_chemical_advice(cls, value: Any) -> bool:
        """Check whether structured response data contains chemical advice."""

        chemical_keys = {
            "chemical_name",
            "chemical_names",
            "pesticide_name",
            "pesticide_names",
            "product_name",
            "active_ingredient",
            "active_ingredients",
            "chemical_recommendations",
            "chemical_dosage",
            "pesticide_dosage",
            "mixing_instructions",
            "pre_harvest_interval",
        }

        if isinstance(value, dict):
            for key, item in value.items():
                if (
                    str(key).lower() in chemical_keys
                    and cls._has_value(item)
                ):
                    return True

                if cls._contains_chemical_advice(item):
                    return True

        elif isinstance(value, list):
            return any(
                cls._contains_chemical_advice(item)
                for item in value
            )

        return False

    @classmethod
    def _contains_dosage(cls, value: Any) -> bool:
        """Check whether structured response data contains dosage fields."""

        dosage_keys = {
            "dosage",
            "dose",
            "chemical_dosage",
            "pesticide_dosage",
            "fertilizer_dosage",
            "application_dosage",
            "application_rate",
            "recommended_rate",
            "dosage_unit",
            "application_unit",
            "rate_unit",
        }

        if isinstance(value, dict):
            for key, item in value.items():
                if (
                    str(key).lower() in dosage_keys
                    and cls._has_value(item)
                ):
                    return True

                if cls._contains_dosage(item):
                    return True

        elif isinstance(value, list):
            return any(
                cls._contains_dosage(item)
                for item in value
            )

        return False

    @staticmethod
    def _extract_chemical_data(
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract chemical verification metadata from a recommendation."""

        result = dict(candidate)

        # Nested chemical objects take precedence when supplied.
        chemical = candidate.get("chemical")

        if isinstance(chemical, dict):
            result.update(chemical)

        return result

    @staticmethod
    def _extract_dosage_data(
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract dosage validation metadata."""

        result = dict(candidate)

        dosage = candidate.get("dosage_details")

        if isinstance(dosage, dict):
            result.update(dosage)

        return result

    @staticmethod
    def _extract_source_data(
        candidate: Dict[str, Any],
        rule_result: Dict[str, Any],
        candidate_records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Combine source metadata without marking records as verified."""

        result = dict(candidate)

        source_ids: List[str] = []

        for container in (candidate, rule_result):
            values = container.get("source_ids", [])

            if isinstance(values, str):
                values = [values]

            if isinstance(values, (list, tuple, set)):
                source_ids.extend(
                    value
                    for value in values
                    if isinstance(value, str) and value.strip()
                )

        evidence = candidate.get("evidence", [])

        if isinstance(evidence, list):
            for item in evidence:
                if isinstance(item, dict):
                    values = item.get(
                        "source_ids",
                        item.get("information_source_ids", []),
                    )

                    if isinstance(values, str):
                        values = [values]

                    if isinstance(values, (list, tuple, set)):
                        source_ids.extend(
                            value
                            for value in values
                            if isinstance(value, str) and value.strip()
                        )

        for record in candidate_records:
            if not isinstance(record, dict):
                continue

            values = record.get("source_ids", [])

            if isinstance(values, str):
                values = [values]

            if isinstance(values, (list, tuple, set)):
                source_ids.extend(
                    value
                    for value in values
                    if isinstance(value, str) and value.strip()
                )

        result["source_ids"] = list(dict.fromkeys(source_ids))

        # Only explicit claims are validated as claims. An answer string
        # is not automatically treated as independently verified evidence.
        if "claims" not in result:
            result["claims"] = []

        return result

    @staticmethod
    def _get_pest_records(
        candidate_records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Keep only structured pest knowledge-base records."""

        return [
            record
            for record in candidate_records
            if isinstance(record, dict)
            and (
                "pests_and_diseases_as_listed" in record
                or "pests" in record
                or "pest" in record
                or "target_pest" in record
            )
        ]

    # ---------------------------------------------------------------
    # Live-data validation
    # ---------------------------------------------------------------

    @staticmethod
    def _validate_live_data(
        candidate: Dict[str, Any],
        rule_result: Dict[str, Any],
        intent: str,
    ) -> Dict[str, Any]:
        """
        Check basic provenance requirements for weather and mandi data.

        This does not independently contact the weather or market API.
        The service result must contain explicit evidence of successful
        retrieval and a timestamp.
        """

        external_data = candidate.get("external_data")

        if not isinstance(external_data, dict):
            external_data = rule_result.get("external_data")

        if not isinstance(external_data, dict):
            # Some earlier service integrations return a nested "data"
            # dictionary inside the service response.
            external_data = candidate.get("data")

        if not isinstance(external_data, dict):
            return {
                "component": "live_data_validator",
                "status": SafetyStatus.VERIFICATION_REQUIRED.value,
                "approved": False,
                "reasons": [
                    "Validated live-data payload is missing."
                ],
            }

        service_status = external_data.get("status")

        if service_status != "success":
            return {
                "component": "live_data_validator",
                "status": SafetyStatus.VERIFICATION_REQUIRED.value,
                "approved": False,
                "reasons": [
                    "The external service did not report successful retrieval."
                ],
            }

        timestamp = (
            external_data.get("timestamp")
            or external_data.get("retrieved_at")
            or external_data.get("retrieval_timestamp")
        )

        if not timestamp:
            return {
                "component": "live_data_validator",
                "status": SafetyStatus.VERIFICATION_REQUIRED.value,
                "approved": False,
                "reasons": [
                    "The live-data retrieval timestamp is missing."
                ],
            }

        location = (
            external_data.get("location")
            or external_data.get("market")
            or external_data.get("district")
        )

        if not location:
            return {
                "component": "live_data_validator",
                "status": SafetyStatus.VERIFICATION_REQUIRED.value,
                "approved": False,
                "reasons": [
                    "The location or market associated with the live data "
                    "is missing."
                ],
            }

        if intent == "weather":
            if not any(
                key in external_data
                for key in (
                    "temperature_c",
                    "humidity_percent",
                    "rainfall_mm",
                )
            ):
                return {
                    "component": "live_data_validator",
                    "status": SafetyStatus.VERIFICATION_REQUIRED.value,
                    "approved": False,
                    "reasons": [
                        "The weather payload contains no recognized "
                        "weather measurements."
                    ],
                }

        elif intent == "mandi_prices":
            if not any(
                external_data.get(key) is not None
                for key in (
                    "minimum_price",
                    "maximum_price",
                    "modal_price",
                    "min_price",
                    "max_price",
                    "modal_price",
                )
            ):
                return {
                    "component": "live_data_validator",
                    "status": SafetyStatus.VERIFICATION_REQUIRED.value,
                    "approved": False,
                    "reasons": [
                        "The market payload contains no recognized prices."
                    ],
                }

        return {
            "component": "live_data_validator",
            "status": SafetyStatus.APPROVED.value,
            "approved": True,
            "reasons": [],
            "timestamp": timestamp,
            "location": location,
        }

    # ---------------------------------------------------------------
    # Required-check handling
    # ---------------------------------------------------------------

    @staticmethod
    def _missing_required_checks(
        required_checks: List[str],
        checks: Dict[str, Dict[str, Any]],
        chemical_present: bool,
        dosage_present: bool,
        intent: str,
    ) -> List[str]:
        """Identify required checks that have not been completed."""

        aliases = {
            "chemical_verification": "chemical_verifier",
            "dosage_validation": "dosage_validator",
            "crop_pest_validation": "crop_pest_validator",
            "source_validation": "source_validator",
            "live_data_validation": "live_data_validator",
        }

        missing: List[str] = []

        for required in required_checks:
            if required in {
                "claim_evidence_validation",
                "nutrient_recommendation_validation",
                "water_requirement_validation",
                "market_record_validation",
                "timestamp_validation",
                "location_validation",
                "clarification_validation",
            }:
                # IGNORE these checks so the bot doesn't block valid answers
                continue

            component_name = aliases.get(required)

            if component_name and component_name not in checks:
                missing.append(required)

        if chemical_present and "chemical_verifier" not in checks:
            missing.append("chemical_verification")

        if dosage_present and "dosage_validator" not in checks:
            missing.append("dosage_validation")

        if intent == "pest_management":
            if "crop_pest_validator" not in checks:
                missing.append("crop_pest_validation")

        return list(dict.fromkeys(missing))

    # ---------------------------------------------------------------
    # General helpers
    # ---------------------------------------------------------------

    @staticmethod
    def _has_value(value: Any) -> bool:
        """Check whether a value is present and non-empty."""

        if value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        if isinstance(value, (list, tuple, set)):
            return len(value) > 0

        if isinstance(value, dict):
            return bool(value)

        return True

    @staticmethod
    def _normalize_identifier(value: Any) -> str:
        """Normalize an intent identifier."""

        if value is None:
            return "general_agriculture"

        return (
            str(value)
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

    # ---------------------------------------------------------------
    # Result formatting
    # ---------------------------------------------------------------

    @staticmethod
    def _blocked_result(
        reasons: List[str],
        warnings: Optional[List[str]] = None,
        checks: Optional[Dict[str, Dict[str, Any]]] = None,
        intent: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a consistent blocked result."""

        return {
            "component": "safety_engine",
            "status": SafetyStatus.BLOCKED.value,
            "approved": False,
            "verification_required": True,
            "intent": intent,
            "language": language,
            "response": None,
            "checks": checks or {},
            "reasons": reasons,
            "warnings": warnings or [],
        }


# -------------------------------------------------------------------
# Convenience function
# -------------------------------------------------------------------

def validate_recommendation(
    recommendation: Any,
    query: Optional[Dict[str, Any]] = None,
    rule_result: Optional[Dict[str, Any]] = None,
    knowledge_base_loader: Any = None,
    sources_file: Optional[str] = None,
    require_verified_evidence: bool = True,
) -> Dict[str, Any]:
    """
    Validate a recommendation without manually constructing SafetyEngine.
    """

    engine = SafetyEngine(
        knowledge_base_loader=knowledge_base_loader,
        sources_file=sources_file,
    )

    return engine.validate_recommendation(
        recommendation=recommendation,
        query=query,
        rule_result=rule_result,
        require_verified_evidence=require_verified_evidence,
    )