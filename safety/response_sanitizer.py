"""
AgriSathi - Response Sanitizer

Purpose:
    Inspect farmer-facing agricultural responses before release.

Responsibilities:
    - Reject malformed or empty responses.
    - Block responses that failed required safety checks.
    - Remove chemical and dosage details when their verification
      has not been established.
    - Reject unsupported source-verification claims.
    - Flag fabricated or unverified live-data claims.
    - Preserve relevant source references and safety warnings.
    - Return a consistent result for SafetyEngine.

Important:
    This module is a final response safeguard, not a substitute for
    chemical verification, dosage validation, crop-pest validation,
    or source validation.

    It does not independently establish whether agricultural facts
    are true. Required upstream validation results must be supplied.
"""

import re
from typing import Any, Dict, List, Optional

from safety.safety_rules import SafetyStatus


class ResponseSanitizer:
    """Sanitize agricultural recommendations before they reach farmers."""

    # Fields that may contain pesticide or other chemical advice.
    CHEMICAL_FIELDS = {
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
        "dosage",
        "dose",
        "application_rate",
        "mixing_instructions",
        "application_frequency",
        "pre_harvest_interval",
        "waiting_period",
    }

    # Fields that commonly contain dosage details.
    DOSAGE_FIELDS = {
        "dosage",
        "dose",
        "chemical_dosage",
        "pesticide_dosage",
        "fertilizer_dosage",
        "application_dosage",
        "application_rate",
        "recommended_rate",
        "rate",
        "dosage_unit",
        "application_unit",
        "rate_unit",
    }

    # Fields that may contain current weather or market information.
    LIVE_DATA_FIELDS = {
        "temperature_c",
        "humidity_percent",
        "rain_probability",
        "rainfall_mm",
        "wind_speed_mps",
        "minimum_price",
        "maximum_price",
        "modal_price",
        "market_price",
        "mandi_price",
        "market_prices",
        "weather_data",
        "market_data",
    }

    # Fields that can contain source claims or verification metadata.
    SOURCE_FIELDS = {
        "source_verified",
        "source_evidence_verified",
        "sources_verified",
        "verification_status",
        "verified",
        "source_ids",
        "sources",
        "citations",
    }

    def __init__(
        self,
        block_on_any_failed_check: bool = True,
        preserve_source_metadata: bool = True,
    ) -> None:
        """
        Initialize the sanitizer.

        Args:
            block_on_any_failed_check:
                If True, a failed required safety check prevents release.

            preserve_source_metadata:
                Preserve source IDs and source references in the output.
        """

        self.block_on_any_failed_check = block_on_any_failed_check
        self.preserve_source_metadata = preserve_source_metadata

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------

    def sanitize(
        self,
        response: Any,
        safety_results: Optional[Dict[str, Any]] = None,
        language: str = "en",
        intent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sanitize a candidate response.

        Args:
            response:
                A response string or recommendation dictionary.

            safety_results:
                Results from upstream safety components.

                Example:
                    {
                        "chemical_verifier": {"approved": True},
                        "dosage_validator": {"approved": True},
                        "crop_pest_validator": {"approved": True},
                        "source_validator": {"approved": True}
                    }

                This example is illustrative. Required checks depend
                on the recommendation's content and intent.

            language:
                Requested response language, such as "en" or "hi".

            intent:
                Query intent, such as "pest_management" or "weather".

        Returns:
            {
                "component": "response_sanitizer",
                "status": "approved",
                "approved": True,
                "response": "...",
                "removed_fields": [],
                "reasons": [],
                "warnings": []
            }

        Important:
            The sanitizer does not infer missing verification results.
            A missing required check is not treated as a successful check.
        """

        reasons: List[str] = []
        warnings: List[str] = []
        removed_fields: List[str] = []

        if isinstance(response, str):
            candidate = {
                "answer": response,
                "intent": intent,
                "language": language,
            }
        elif isinstance(response, dict):
            candidate = dict(response)
        else:
            return self._result(
                status=SafetyStatus.BLOCKED,
                reasons=[
                    "The candidate response must be a string or dictionary."
                ],
            )

        answer = candidate.get(
            "answer",
            candidate.get("response", ""),
        )

        if not isinstance(answer, str) or not answer.strip():
            return self._result(
                status=SafetyStatus.BLOCKED,
                reasons=["The candidate response is empty or malformed."],
            )

        candidate["answer"] = self._normalize_text(answer)

        # -----------------------------------------------------------
        # 1. Check upstream safety results
        # -----------------------------------------------------------

        if not isinstance(safety_results, dict):
            safety_results = {}

        failed_checks = self._find_failed_checks(safety_results)

        if failed_checks and self.block_on_any_failed_check:
            reasons.append(
                "One or more upstream safety checks failed or were "
                "not approved: " + ", ".join(failed_checks) + "."
            )

        # -----------------------------------------------------------
        # 2. Inspect chemical and dosage content
        # -----------------------------------------------------------

        chemical_present = self._contains_chemical_content(candidate)
        dosage_present = self._contains_dosage_content(candidate)

        chemical_result = self._get_check(
            safety_results,
            "chemical_verifier",
        )

        dosage_result = self._get_check(
            safety_results,
            "dosage_validator",
        )

        if chemical_present and not self._is_approved(chemical_result):
            self._remove_fields(candidate, self.CHEMICAL_FIELDS, removed_fields)

            warnings.append(
                "Unverified chemical recommendation details were withheld."
            )

            # A text response may contain chemical advice even when
            # structured chemical fields are absent.
            candidate["answer"] = self._remove_unverified_chemical_text(
                candidate["answer"]
            )

        if dosage_present and not self._is_approved(dosage_result):
            self._remove_fields(candidate, self.DOSAGE_FIELDS, removed_fields)

            warnings.append(
                "Unverified dosage details were withheld."
            )

            candidate["answer"] = self._remove_unverified_dosage_text(
                candidate["answer"]
            )

        # -----------------------------------------------------------
        # 3. Inspect source-verification claims
        # -----------------------------------------------------------

        source_result = self._get_check(
            safety_results,
            "source_validator",
        )

        source_claims_verified = self._is_approved(source_result)

        if not source_claims_verified:
            self._remove_unverified_source_fields(
                candidate,
                removed_fields,
            )

            candidate["answer"] = self._remove_unverified_source_claims(
                candidate["answer"]
            )

            warnings.append(
                "Source-verification claims were removed because source "
                "validation was not approved."
            )

        # -----------------------------------------------------------
        # 4. Inspect live-data content
        # -----------------------------------------------------------

        normalized_intent = self._normalize_identifier(
            intent or candidate.get("intent")
        )

        if normalized_intent in {"weather", "mandi_prices"}:
            live_result = self._get_check(
                safety_results,
                "live_data_validator",
            )

            if not self._is_approved(live_result):
                self._remove_fields(
                    candidate,
                    self.LIVE_DATA_FIELDS,
                    removed_fields,
                )

                candidate["answer"] = self._remove_unverified_live_claims(
                    candidate["answer"],
                    normalized_intent,
                )

                warnings.append(
                    "Current weather or market information was withheld "
                    "because live-data validation was not approved."
                )

        # -----------------------------------------------------------
        # 5. Validate final answer
        # -----------------------------------------------------------

        final_answer = candidate.get("answer", "")

        if not isinstance(final_answer, str) or not final_answer.strip():
            reasons.append(
                "No usable response remains after sanitization."
            )

        # If an upstream required safety check failed, do not release
        # the candidate answer, even if field removal was attempted.
        if reasons:
            return self._result(
                status=SafetyStatus.BLOCKED,
                reasons=reasons,
                warnings=warnings,
                removed_fields=removed_fields,
            )

        # -----------------------------------------------------------
        # 6. Prepare farmer-facing output
        # -----------------------------------------------------------

        candidate["answer"] = final_answer.strip()

        if not self.preserve_source_metadata:
            candidate.pop("source_ids", None)
            candidate.pop("sources", None)
            candidate.pop("citations", None)

        return self._result(
            status=SafetyStatus.APPROVED,
            response=candidate,
            reasons=[],
            warnings=warnings,
            removed_fields=removed_fields,
        )

    # ---------------------------------------------------------------
    # Safety result helpers
    # ---------------------------------------------------------------

    @staticmethod
    def _get_check(
        safety_results: Dict[str, Any],
        component: str,
    ) -> Dict[str, Any]:
        """Retrieve one component's result."""

        result = safety_results.get(component)

        return result if isinstance(result, dict) else {}

    @staticmethod
    def _is_approved(result: Dict[str, Any]) -> bool:
        """
        Require an explicit approval result.

        A missing component result is not considered approved.
        """

        return (
            isinstance(result, dict)
            and result.get("approved") is True
            and result.get("status") == SafetyStatus.APPROVED.value
        )

    @classmethod
    def _find_failed_checks(
        cls,
        safety_results: Dict[str, Any],
    ) -> List[str]:
        """
        Identify explicitly failed or malformed safety results.

        Required components are determined by intent and content in
        SafetyEngine. This helper checks components that were supplied.
        """

        failed: List[str] = []

        for component, result in safety_results.items():
            if not isinstance(result, dict):
                failed.append(component)
                continue

            if (
                result.get("approved") is not True
                or result.get("status") != SafetyStatus.APPROVED.value
            ):
                failed.append(component)

        return failed

    # ---------------------------------------------------------------
    # Content inspection
    # ---------------------------------------------------------------

    @classmethod
    def _contains_chemical_content(
        cls,
        data: Any,
    ) -> bool:
        """Check whether structured response data contains chemical fields."""

        if isinstance(data, dict):
            for key, value in data.items():
                normalized_key = str(key).lower()

                if normalized_key in cls.CHEMICAL_FIELDS:
                    if cls._has_value(value):
                        return True

                if cls._contains_chemical_content(value):
                    return True

        elif isinstance(data, list):
            return any(
                cls._contains_chemical_content(item)
                for item in data
            )

        return False

    @classmethod
    def _contains_dosage_content(
        cls,
        data: Any,
    ) -> bool:
        """Check whether structured response data contains dosage fields."""

        if isinstance(data, dict):
            for key, value in data.items():
                normalized_key = str(key).lower()

                if normalized_key in cls.DOSAGE_FIELDS:
                    if cls._has_value(value):
                        return True

                if cls._contains_dosage_content(value):
                    return True

        elif isinstance(data, list):
            return any(
                cls._contains_dosage_content(item)
                for item in data
            )

        return False

    # ---------------------------------------------------------------
    # Field removal
    # ---------------------------------------------------------------

    @classmethod
    def _remove_fields(
        cls,
        data: Any,
        fields_to_remove: set,
        removed_fields: List[str],
        prefix: str = "",
    ) -> None:
        """Recursively remove selected fields from dictionaries."""

        if isinstance(data, dict):
            for key in list(data.keys()):
                path = f"{prefix}.{key}" if prefix else str(key)

                if str(key).lower() in fields_to_remove:
                    del data[key]
                    removed_fields.append(path)
                    continue

                cls._remove_fields(
                    data[key],
                    fields_to_remove,
                    removed_fields,
                    path,
                )

        elif isinstance(data, list):
            for index, item in enumerate(data):
                cls._remove_fields(
                    item,
                    fields_to_remove,
                    removed_fields,
                    f"{prefix}[{index}]",
                )

    @classmethod
    def _remove_unverified_source_fields(
        cls,
        candidate: Dict[str, Any],
        removed_fields: List[str],
    ) -> None:
        """
        Remove claims that source verification succeeded.

        Source IDs themselves may be preserved for traceability, but
        they must not be represented as proof of claim verification.
        """

        fields_to_remove = {
            "source_verified",
            "source_evidence_verified",
            "sources_verified",
        }

        cls._remove_fields(
            candidate,
            fields_to_remove,
            removed_fields,
        )

        if (
            "verification_status" in candidate
            and candidate["verification_status"]
            in {"verified", "source_verified", "expert_verified"}
        ):
            candidate["verification_status"] = "verification_required"

    # ---------------------------------------------------------------
    # Text safeguards
    # ---------------------------------------------------------------

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize whitespace without changing the response meaning."""

        return re.sub(r"[ \t]+", " ", text).strip()

    @staticmethod
    def _remove_unverified_chemical_text(text: str) -> str:
        """
        Remove common English phrases containing unverified chemical
        recommendations.

        This is a conservative fallback, not a complete natural-language
        safety detector. The final safety gate must still block any
        response whose required checks failed.
        """

        patterns = [
            r"(?im)^.*\b(?:apply|use|spray|mix)\b.*\b"
            r"(?:pesticide|insecticide|fungicide|herbicide|chemical)\b.*$",
            r"(?im)^.*\b(?:pesticide|insecticide|fungicide|herbicide)\b"
            r".*\b(?:recommended|recommendation|treatment)\b.*$",
        ]

        for pattern in patterns:
            text = re.sub(
                pattern,
                "[Chemical recommendation withheld pending verification.]",
                text,
            )

        return text.strip()

    @staticmethod
    def _remove_unverified_dosage_text(text: str) -> str:
        """
        Replace common English dosage statements with a warning.

        Do not rely on regular expressions alone to detect every dosage
        in multilingual or free-form text.
        """

        patterns = [
            r"(?im)^.*\b(?:dosage|dose|application rate|mixing ratio)\b.*$",
            r"(?im)^.*\b\d+(?:\.\d+)?\s*"
            r"(?:mg|g|kg|ml|l|ppm)\s*(?:/|\bper\b).*$",
        ]

        for pattern in patterns:
            text = re.sub(
                pattern,
                "[Dosage information withheld pending verification.]",
                text,
            )

        return text.strip()

    @staticmethod
    def _remove_unverified_source_claims(text: str) -> str:
        """Remove explicit claims that information has been verified."""

        patterns = [
            r"(?i)\bverified by official sources\b",
            r"(?i)\bofficially verified\b",
            r"(?i)\bscientifically verified\b",
            r"(?i)\bverified agricultural recommendation\b",
        ]

        for pattern in patterns:
            text = re.sub(
                pattern,
                "requiring source verification",
                text,
            )

        return text.strip()

    @staticmethod
    def _remove_unverified_live_claims(
        text: str,
        intent: str,
    ) -> str:
        """
        Replace a current-data answer with a clear unavailable-data message.

        This avoids leaving potentially stale values in the final response.
        """

        if intent == "weather":
            return (
                "Current weather information could not be verified. "
                "Please check an authoritative weather service before "
                "making weather-dependent farming decisions."
            )

        if intent == "mandi_prices":
            return (
                "Current mandi prices could not be verified. "
                "Please consult an authoritative market-price service "
                "for the relevant market and date."
            )

        return text

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
            return ""

        return str(value).strip().lower().replace("-", "_").replace(" ", "_")

    # ---------------------------------------------------------------
    # Result formatter
    # ---------------------------------------------------------------

    @staticmethod
    def _result(
        status: SafetyStatus,
        response: Optional[Dict[str, Any]] = None,
        reasons: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        removed_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Return a consistent result for SafetyEngine."""

        approved = status == SafetyStatus.APPROVED

        return {
            "component": "response_sanitizer",
            "status": status.value,
            "approved": approved,
            "response": response,
            "reasons": reasons or [],
            "warnings": warnings or [],
            "removed_fields": removed_fields or [],
        }


# -------------------------------------------------------------------
# Convenience function
# -------------------------------------------------------------------

def sanitize_response(
    response: Any,
    safety_results: Optional[Dict[str, Any]] = None,
    language: str = "en",
    intent: Optional[str] = None,
) -> Dict[str, Any]:
    """Sanitize a candidate response without manually creating an instance."""

    sanitizer = ResponseSanitizer()

    return sanitizer.sanitize(
        response=response,
        safety_results=safety_results,
        language=language,
        intent=intent,
    )