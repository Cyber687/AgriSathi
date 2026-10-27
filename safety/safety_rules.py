"""
AgriSathi - Agricultural Safety Rules

Purpose:
    Defines centralized safety policies for agricultural recommendations.

Responsibilities:
    - Identify recommendations requiring additional verification.
    - Prevent unverified chemical and dosage recommendations.
    - Require appropriate evidence for crop-pest recommendations.
    - Validate source and live-data requirements.
    - Provide consistent safety decisions to other modules.

Important:
    This module defines policy rules. It does not independently establish
    whether a pesticide, dosage, source, or agricultural claim is correct.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Set


class SafetyStatus(str, Enum):
    """Possible outcomes of a safety evaluation."""

    APPROVED = "approved"
    BLOCKED = "blocked"
    VERIFICATION_REQUIRED = "verification_required"
    CLARIFICATION_REQUIRED = "clarification_required"


class SafetySeverity(str, Enum):
    """Severity levels for safety findings."""

    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------
# General configuration
# ---------------------------------------------------------------------

SUPPORTED_LANGUAGES: Set[str] = {
    "en",
    "hi",
}

SUPPORTED_INTENTS: Set[str] = {
    "crop_information",
    "fertilizer_advice",
    "pest_management",
    "irrigation",
    "weather",
    "mandi_prices",
    "general_agriculture",
    "needs_clarification",
}

# These fields must not be interpreted as proof of verification.
UNVERIFIED_STATUSES: Set[str] = {
    "unverified",
    "needs_source_verification",
    "not_verified",
    "verification_required",
    "unknown",
    "pending",
}

# Only these statuses may be considered verified by default.
# The source validator must still verify the supporting evidence.
VERIFIED_STATUSES: Set[str] = {
    "verified",
    "source_verified",
    "expert_verified",
}


# ---------------------------------------------------------------------
# Chemical safety rules
# ---------------------------------------------------------------------

CHEMICAL_SAFETY_RULES: Dict[str, Any] = {
    "require_verified_product": True,
    "require_crop_compatibility": True,
    "require_target_pest_compatibility": True,
    "require_authoritative_source": True,
    "require_applicable_label_directions": True,
    "block_unverified_chemical_recommendations": True,
    "block_unknown_chemical_dosages": True,
    "allow_inferred_dosage": False,
    "allow_inferred_mixing_instructions": False,
    "allow_inferred_waiting_periods": False,
    "allow_unverified_application_frequency": False,
    "allow_unverified_pre_harvest_interval": False,
    "require_relevant_product_formulation": True,
}


# ---------------------------------------------------------------------
# Dosage validation rules
# ---------------------------------------------------------------------

DOSAGE_SAFETY_RULES: Dict[str, Any] = {
    "require_explicit_evidence": True,
    "require_authoritative_source": True,
    "require_matching_crop": True,
    "require_matching_target_pest": True,
    "require_matching_product": True,
    "require_matching_formulation": True,
    "require_validated_unit": True,
    "allow_missing_units": False,
    "allow_unit_conversion_without_validation": False,
    "allow_extrapolation_from_another_crop": False,
    "allow_extrapolation_from_another_pest": False,
    "allow_extrapolation_from_another_formulation": False,
    "allow_model_generated_dosage": False,
    "allow_dosage_inference": False,
}


# ---------------------------------------------------------------------
# Crop and pest compatibility rules
# ---------------------------------------------------------------------

CROP_PEST_SAFETY_RULES: Dict[str, Any] = {
    "require_crop_identification": True,
    "require_target_pest_identification": True,
    "require_supported_crop_pest_relationship": True,
    "allow_assumed_crop_pest_relationship": False,
    "allow_unverified_chemical_control": False,
    "require_relevant_management_evidence": True,
    "allow_unrelated_crop_recommendations": False,
}


# ---------------------------------------------------------------------
# Source verification rules
# ---------------------------------------------------------------------

SOURCE_SAFETY_RULES: Dict[str, Any] = {
    "require_source_for_agricultural_claims": True,
    "require_valid_source_reference": True,
    "require_evidence_for_chemical_claims": True,
    "require_evidence_for_dosage_claims": True,
    "require_evidence_for_crop_pest_claims": True,
    "allow_fabricated_sources": False,
    "allow_unverified_sources_as_verified": False,
    "allow_missing_source_ids_for_verified_claims": False,
}


# ---------------------------------------------------------------------
# Live data rules
# ---------------------------------------------------------------------

LIVE_DATA_SAFETY_RULES: Dict[str, Any] = {
    "require_live_weather_for_current_weather_claims": True,
    "require_live_market_data_for_current_mandi_prices": True,
    "require_retrieval_timestamp": True,
    "require_location_for_location_specific_data": True,
    "allow_fabricated_weather_values": False,
    "allow_fabricated_market_prices": False,
    "allow_stale_data_as_current": False,
}


# ---------------------------------------------------------------------
# Recommendation rules
# ---------------------------------------------------------------------

RECOMMENDATION_SAFETY_RULES: Dict[str, Any] = {
    "require_evidence_based_recommendations": True,
    "require_source_attribution": True,
    "preserve_uncertainty": True,
    "preserve_verification_status": True,
    "allow_invented_agricultural_facts": False,
    "allow_invented_crop_requirements": False,
    "allow_invented_fertilizer_dosages": False,
    "allow_invented_pesticide_dosages": False,
    "allow_unsupported_guarantees": False,
    "allow_llm_to_override_safety": False,
    "require_final_response_validation": True,
}


# ---------------------------------------------------------------------
# Required checks by recommendation type
# ---------------------------------------------------------------------

REQUIRED_CHECKS_BY_INTENT: Dict[str, List[str]] = {
    "crop_information": [
        "source_validation",
        "claim_evidence_validation",
    ],
    "fertilizer_advice": [
        "source_validation",
        "claim_evidence_validation",
        "nutrient_recommendation_validation",
    ],
    "pest_management": [
        "source_validation",
        "claim_evidence_validation",
        "crop_pest_validation",
    ],
    "irrigation": [
        "source_validation",
        "claim_evidence_validation",
        "water_requirement_validation",
    ],
    "weather": [
        "live_data_validation",
        "location_validation",
        "timestamp_validation",
    ],
    "mandi_prices": [
        "live_data_validation",
        "market_record_validation",
        "timestamp_validation",
    ],
    "general_agriculture": [
        "source_validation",
        "claim_evidence_validation",
    ],
    "needs_clarification": [
        "clarification_validation",
    ],
}


# ---------------------------------------------------------------------
# Safety policy helper functions
# ---------------------------------------------------------------------

def normalize_status(value: Any) -> str:
    """
    Normalize a verification or safety status.

    Returns an empty string when the supplied value is missing.
    """

    if value is None:
        return ""

    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def is_verified_status(value: Any) -> bool:
    """
    Determine whether a status belongs to the recognized verified set.

    This checks the status label only. It does not prove that the
    underlying evidence or source is valid.
    """

    return normalize_status(value) in VERIFIED_STATUSES


def is_unverified_status(value: Any) -> bool:
    """Determine whether a status explicitly indicates unverified data."""

    status = normalize_status(value)

    if not status:
        return True

    return (
        status in UNVERIFIED_STATUSES
        or status not in VERIFIED_STATUSES
    )


def get_required_checks(intent: Optional[str]) -> List[str]:
    """
    Return the safety checks required for an intent.

    Unknown intents receive conservative default checks.
    """

    normalized_intent = normalize_status(intent)

    if normalized_intent in REQUIRED_CHECKS_BY_INTENT:
        return list(REQUIRED_CHECKS_BY_INTENT[normalized_intent])

    return [
        "source_validation",
        "claim_evidence_validation",
    ]


def get_rules_for_intent(intent: Optional[str]) -> Dict[str, Any]:
    """
    Return the relevant policy configuration for an intent.
    """

    normalized_intent = normalize_status(intent)

    rules: Dict[str, Any] = {
        "intent": normalized_intent,
        "required_checks": get_required_checks(normalized_intent),
        "chemical_safety": CHEMICAL_SAFETY_RULES,
        "dosage_safety": DOSAGE_SAFETY_RULES,
        "source_safety": SOURCE_SAFETY_RULES,
        "recommendation_safety": RECOMMENDATION_SAFETY_RULES,
    }

    if normalized_intent == "pest_management":
        rules["crop_pest_safety"] = CROP_PEST_SAFETY_RULES

    if normalized_intent in {"weather", "mandi_prices"}:
        rules["live_data_safety"] = LIVE_DATA_SAFETY_RULES

    return rules


# ---------------------------------------------------------------------
# Basic safety decision helpers
# ---------------------------------------------------------------------

def should_block_unverified_chemical(
    chemical_recommendation: bool,
    verification_status: Any,
) -> bool:
    """
    Determine whether a chemical recommendation must be blocked.

    An unverified chemical recommendation is not approved for release.
    """

    if not chemical_recommendation:
        return False

    if not is_verified_status(verification_status):
        return True

    return False


def should_block_unverified_dosage(
    dosage_present: bool,
    dosage_verified: bool,
    source_verified: bool,
) -> bool:
    """
    Determine whether dosage information must be blocked.

    A dosage is blocked if it is present but either the dosage itself
    or its supporting source has not been verified.
    """

    if not dosage_present:
        return False

    return not (dosage_verified and source_verified)


def should_require_clarification(
    crop_identified: bool,
    pest_identified: bool,
    intent: Optional[str],
) -> bool:
    """
    Determine whether clarification is required.

    Pest-management requests require crop and pest identification
    before a crop-specific chemical recommendation can be considered.
    """

    normalized_intent = normalize_status(intent)

    if normalized_intent == "needs_clarification":
        return True

    if normalized_intent == "pest_management":
        return not (crop_identified and pest_identified)

    return False


def is_supported_language(language: Optional[str]) -> bool:
    """Check whether the requested language is supported."""

    if not language:
        return False

    normalized_language = str(language).strip().lower()

    # Accept locale-style identifiers such as hi-IN and en-IN.
    base_language = normalized_language.split("-")[0].split("_")[0]

    return base_language in SUPPORTED_LANGUAGES


# ---------------------------------------------------------------------
# Configuration export
# ---------------------------------------------------------------------

def get_safety_configuration() -> Dict[str, Any]:
    """
    Return the complete safety configuration.

    The returned structure can be consumed by SafetyEngine.
    """

    return {
        "supported_languages": sorted(SUPPORTED_LANGUAGES),
        "supported_intents": sorted(SUPPORTED_INTENTS),
        "verified_statuses": sorted(VERIFIED_STATUSES),
        "unverified_statuses": sorted(UNVERIFIED_STATUSES),
        "chemical_safety": CHEMICAL_SAFETY_RULES,
        "dosage_safety": DOSAGE_SAFETY_RULES,
        "crop_pest_safety": CROP_PEST_SAFETY_RULES,
        "source_safety": SOURCE_SAFETY_RULES,
        "live_data_safety": LIVE_DATA_SAFETY_RULES,
        "recommendation_safety": RECOMMENDATION_SAFETY_RULES,
        "required_checks_by_intent": REQUIRED_CHECKS_BY_INTENT,
    }