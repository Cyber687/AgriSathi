"""
AgriSathi - Dosage Validator

Purpose:
    Validate the evidence and completeness of agricultural dosage
    recommendations before they can be approved.

Responsibilities:
    - Detect missing or malformed dosage information.
    - Require explicit dosage verification.
    - Require supporting source evidence.
    - Check units and application context.
    - Prevent inferred or model-generated dosages from being approved.
    - Distinguish pesticide dosage from fertilizer application rates.

Important:
    This module does not calculate or recommend agricultural dosages.
    It validates supplied information and verification metadata.

    A successful result from this module is not final approval.
    The complete AgriSathi safety pipeline must still be applied.
"""

import re
from typing import Any, Dict, List, Optional

from safety.safety_rules import (
    SafetyStatus,
    is_verified_status,
)


class DosageValidator:
    """
    Validate dosage information in agricultural recommendations.

    Supported input examples:

        {
            "dosage": "2 ml/L",
            "dosage_verified": True,
            "source_verified": True,
            "verification_status": "verified",
            "unit": "ml/L",
            "application_method": "foliar spray",
            "crop": "Example crop",
            "source_ids": ["SRC001"]
        }

    The example is a schema illustration only, not an agricultural
    dosage recommendation.

    Verification flags must only be set by trusted validation
    processes, not directly from untrusted LLM-generated output.
    """

    # Units accepted for recognizing dosage formats.
    # Recognizing a unit does not mean the dosage is appropriate.
    ALLOWED_UNIT_PATTERNS = [
        r"mg\s*/\s*l",
        r"g\s*/\s*l",
        r"kg\s*/\s*ha",
        r"g\s*/\s*ha",
        r"ml\s*/\s*l",
        r"l\s*/\s*ha",
        r"ml\s*/\s*ha",
        r"mg\s*/\s*kg",
        r"g\s*/\s*kg",
        r"kg\s*/\s*acre",
        r"g\s*/\s*acre",
        r"ml\s*/\s*acre",
        r"l\s*/\s*acre",
        r"kg\s*/\s*plant",
        r"g\s*/\s*plant",
        r"g\s*/\s*tree",
        r"kg\s*/\s*tree",
        r"kg\s*/\s*plot",
        r"g\s*/\s*plot",
        r"%",
        r"ppm",
    ]

    DOSAGE_KEYS = [
        "dosage",
        "dose",
        "application_rate",
        "recommended_rate",
        "chemical_dosage",
        "fertilizer_dosage",
        "application_dosage",
        "rate",
    ]

    UNIT_KEYS = [
        "unit",
        "dosage_unit",
        "application_unit",
        "rate_unit",
    ]

    def __init__(
        self,
        knowledge_base_loader: Any = None,
    ) -> None:
        """
        Initialize the validator.

        Args:
            knowledge_base_loader:
                Optional KnowledgeBaseLoader instance. This validator
                does not assume that the loader independently verifies
                dosage claims.
        """

        self.knowledge_base_loader = knowledge_base_loader

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------

    def validate(
        self,
        recommendation: Optional[Dict[str, Any]],
        require_dosage: bool = False,
        require_crop: bool = True,
        require_source: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate dosage information.

        Args:
            recommendation:
                Recommendation or evidence dictionary.

            require_dosage:
                Set True when a dosage is explicitly being recommended.
                Set False when the recommendation does not require a
                dosage, such as general crop information.

            require_crop:
                Require an identified crop for a dosage recommendation.

            require_source:
                Require source IDs and verified source evidence.

        Returns:
            A structured validation result.

        Important:
            If a dosage is present but not verified, it is not approved.
            If no dosage is present and require_dosage is False, the
            validator does not require one to be invented.
        """

        reasons: List[str] = []
        warnings: List[str] = []

        checks: Dict[str, bool] = {
            "input_valid": False,
            "dosage_present": False,
            "dosage_format_valid": False,
            "unit_present": False,
            "unit_recognized": False,
            "dosage_verified": False,
            "source_verified": False,
            "verification_status_valid": False,
            "crop_identified": False,
            "application_context_present": False,
            "not_model_inferred": False,
            "source_ids_present": False,
        }

        if not isinstance(recommendation, dict):
            return self._result(
                status=SafetyStatus.VERIFICATION_REQUIRED,
                reasons=["A valid recommendation object is required."],
                warnings=warnings,
                checks=checks,
            )

        checks["input_valid"] = True

        # -----------------------------------------------------------
        # 1. Extract dosage and unit
        # -----------------------------------------------------------

        dosage_value = self._first_value(
            recommendation,
            self.DOSAGE_KEYS,
        )

        unit_value = self._first_value(
            recommendation,
            self.UNIT_KEYS,
        )

        dosage_present = self._has_value(dosage_value)
        checks["dosage_present"] = dosage_present

        # A dosage is not required for every agricultural response.
        if not dosage_present and not require_dosage:
            return self._result(
                status=SafetyStatus.APPROVED,
                approved=True,
                reasons=[],
                warnings=[
                    "No dosage was supplied. No dosage recommendation "
                    "has been validated or generated."
                ],
                checks=checks,
                dosage=None,
                unit=None,
            )

        if not dosage_present:
            reasons.append(
                "A dosage is required for this recommendation, "
                "but no dosage was supplied."
            )

        # -----------------------------------------------------------
        # 2. Validate dosage format
        # -----------------------------------------------------------

        dosage_text = self._to_text(dosage_value)

        if dosage_present:
            checks["dosage_format_valid"] = self._has_numeric_quantity(
                dosage_text
            )

            if not checks["dosage_format_valid"]:
                reasons.append(
                    "The supplied dosage does not contain a recognizable "
                    "numeric quantity."
                )

        # -----------------------------------------------------------
        # 3. Validate units
        # -----------------------------------------------------------

        # A unit may be explicitly supplied or included in the dosage
        # string, for example "value ml/L". This is format recognition,
        # not confirmation that the unit is appropriate.
        effective_unit = unit_value

        if not self._has_value(effective_unit) and dosage_present:
            effective_unit = self._extract_unit(dosage_text)

        checks["unit_present"] = self._has_value(effective_unit)

        if not checks["unit_present"] and dosage_present:
            reasons.append(
                "The dosage unit is missing."
            )

        checks["unit_recognized"] = self._is_recognized_unit(
            effective_unit
        )

        if checks["unit_present"] and not checks["unit_recognized"]:
            reasons.append(
                "The dosage unit is not recognized by the validator."
            )

        # -----------------------------------------------------------
        # 4. Check explicit dosage verification
        # -----------------------------------------------------------

        checks["dosage_verified"] = (
            recommendation.get("dosage_verified") is True
        )

        if dosage_present and not checks["dosage_verified"]:
            reasons.append(
                "The dosage has not been explicitly verified against "
                "appropriate authoritative evidence."
            )

        # -----------------------------------------------------------
        # 5. Check source verification
        # -----------------------------------------------------------

        checks["source_verified"] = (
            recommendation.get("source_verified") is True
            or recommendation.get("source_evidence_verified") is True
        )

        source_ids = self._extract_source_ids(recommendation)

        checks["source_ids_present"] = bool(source_ids)

        if require_source:
            if not checks["source_ids_present"]:
                reasons.append(
                    "No source IDs were supplied for the dosage."
                )

            if not checks["source_verified"]:
                reasons.append(
                    "The source evidence supporting the dosage "
                    "has not been verified."
                )

        # -----------------------------------------------------------
        # 6. Check verification status
        # -----------------------------------------------------------

        verification_status = recommendation.get(
            "dosage_verification_status",
            recommendation.get("verification_status"),
        )

        checks["verification_status_valid"] = is_verified_status(
            verification_status
        )

        if dosage_present and not checks["verification_status_valid"]:
            reasons.append(
                "The dosage verification status is missing or unverified."
            )

        # -----------------------------------------------------------
        # 7. Check crop identification
        # -----------------------------------------------------------

        crop_value = self._first_value(
            recommendation,
            ["crop", "crop_name", "crop_id"],
        )

        checks["crop_identified"] = self._has_value(crop_value)

        if require_crop and not checks["crop_identified"]:
            reasons.append(
                "The crop associated with the dosage has not been identified."
            )

        # -----------------------------------------------------------
        # 8. Check application context
        # -----------------------------------------------------------

        application_context = self._first_value(
            recommendation,
            [
                "application_method",
                "application_context",
                "application_type",
            ],
        )

        checks["application_context_present"] = self._has_value(
            application_context
        )

        if dosage_present and not checks["application_context_present"]:
            reasons.append(
                "The application method or context has not been specified."
            )

        # -----------------------------------------------------------
        # 9. Prevent inferred dosages
        # -----------------------------------------------------------

        generated_by = self._to_text(
            recommendation.get("generated_by", "")
        ).strip().lower()

        dosage_origin = self._to_text(
            recommendation.get("dosage_origin", "")
        ).strip().lower()

        model_generated = (
            recommendation.get("model_generated_dosage") is True
            or generated_by in {"llm", "language_model", "ai_model"}
            or dosage_origin in {
                "inferred",
                "model_generated",
                "llm_generated",
                "estimated",
                "extrapolated",
            }
        )

        checks["not_model_inferred"] = not model_generated

        if model_generated:
            reasons.append(
                "Model-generated, inferred, estimated, or extrapolated "
                "dosage information cannot be approved."
            )

        # -----------------------------------------------------------
        # 10. Determine outcome
        # -----------------------------------------------------------

        if reasons:
            status = SafetyStatus.VERIFICATION_REQUIRED
            approved = False

            warnings.append(
                "Do not release this dosage as an approved recommendation. "
                "Resolve all findings and rerun the safety pipeline."
            )
        else:
            status = SafetyStatus.APPROVED
            approved = True

        return self._result(
            status=status,
            approved=approved,
            reasons=reasons,
            warnings=warnings,
            checks=checks,
            dosage=dosage_value,
            unit=effective_unit,
            crop=crop_value,
            source_ids=source_ids,
        )

    # ---------------------------------------------------------------
    # Supporting methods
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
    def _to_text(value: Any) -> str:
        """Convert a value into a simple string for inspection."""

        if value is None:
            return ""

        if isinstance(value, (dict, list, tuple, set)):
            return ""

        return str(value).strip()

    @classmethod
    def _first_value(
        cls,
        data: Dict[str, Any],
        keys: List[str],
    ) -> Any:
        """Return the first populated field from a list of alternatives."""

        for key in keys:
            value = data.get(key)

            if cls._has_value(value):
                return value

        return None

    @staticmethod
    def _has_numeric_quantity(value: str) -> bool:
        """
        Check whether the dosage text contains a numeric quantity.

        This only checks syntax. It does not establish that the quantity
        is safe or suitable for a particular crop or product.
        """

        if not value:
            return False

        return bool(
            re.search(
                r"(?<![A-Za-z])\d+(?:\.\d+)?",
                value,
            )
        )

    @classmethod
    def _extract_unit(cls, dosage_text: str) -> Optional[str]:
        """Extract a recognized unit pattern from dosage text."""

        if not dosage_text:
            return None

        normalized = dosage_text.lower().replace("per", "/")

        for pattern in cls.ALLOWED_UNIT_PATTERNS:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)

            if match:
                return match.group(0).replace(" ", "")

        # Recognize common standalone mass and volume units.
        standalone_units = [
            r"\bmg\b",
            r"\bg\b",
            r"\bkg\b",
            r"\bml\b",
            r"\bl\b",
        ]

        for pattern in standalone_units:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)

            if match:
                return match.group(0)

        return None

    @classmethod
    def _is_recognized_unit(cls, unit: Any) -> bool:
        """
        Check whether a unit resembles a supported unit expression.

        This is not unit compatibility validation and must not be used
        to convert or approve a dosage.
        """

        if not cls._has_value(unit):
            return False

        unit_text = cls._to_text(unit).lower().strip()

        unit_text = (
            unit_text.replace("litres", "l")
            .replace("liters", "l")
            .replace("litre", "l")
            .replace("liter", "l")
            .replace("millilitres", "ml")
            .replace("milliliters", "ml")
            .replace("millilitre", "ml")
            .replace("milliliter", "ml")
            .replace("grams", "g")
            .replace("gram", "g")
            .replace("kilograms", "kg")
            .replace("kilogram", "kg")
            .replace("milligrams", "mg")
            .replace("milligram", "mg")
            .replace("hectares", "ha")
            .replace("hectare", "ha")
            .replace("acres", "acre")
        )

        unit_text = re.sub(r"\s+", "", unit_text)

        for pattern in cls.ALLOWED_UNIT_PATTERNS:
            if re.fullmatch(pattern, unit_text, flags=re.IGNORECASE):
                return True

        return unit_text in {
            "mg",
            "g",
            "kg",
            "ml",
            "l",
            "ppm",
            "%",
        }

    @staticmethod
    def _extract_source_ids(
        recommendation: Dict[str, Any],
    ) -> List[str]:
        """Extract unique, non-empty source IDs."""

        source_ids = recommendation.get("source_ids", [])

        if not isinstance(source_ids, (list, tuple, set)):
            source_ids = [source_ids] if source_ids else []

        normalized: List[str] = []

        for source_id in source_ids:
            if isinstance(source_id, str) and source_id.strip():
                normalized.append(source_id.strip())

        return list(dict.fromkeys(normalized))

    @staticmethod
    def _result(
        status: SafetyStatus,
        reasons: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        checks: Optional[Dict[str, bool]] = None,
        approved: Optional[bool] = None,
        dosage: Any = None,
        unit: Any = None,
        crop: Any = None,
        source_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a consistent result for downstream safety components."""

        is_approved = (
            status == SafetyStatus.APPROVED
            if approved is None
            else approved
        )

        return {
            "component": "dosage_validator",
            "status": status.value,
            "approved": is_approved,
            "verification_required": not is_approved,
            "dosage": dosage,
            "unit": unit,
            "crop": crop,
            "source_ids": source_ids or [],
            "checks": checks or {},
            "reasons": reasons or [],
            "warnings": warnings or [],
        }


# ---------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------

def validate_dosage(
    recommendation: Optional[Dict[str, Any]],
    require_dosage: bool = False,
    require_crop: bool = True,
    require_source: bool = True,
    knowledge_base_loader: Any = None,
) -> Dict[str, Any]:
    """
    Validate dosage information without manually creating an instance.
    """

    validator = DosageValidator(
        knowledge_base_loader=knowledge_base_loader
    )

    return validator.validate(
        recommendation=recommendation,
        require_dosage=require_dosage,
        require_crop=require_crop,
        require_source=require_source,
    )