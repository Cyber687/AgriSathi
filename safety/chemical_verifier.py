"""
AgriSathi - Chemical Recommendation Verifier

Purpose:
    Evaluates whether a proposed agricultural chemical recommendation
    contains sufficient evidence to proceed through the safety pipeline.

Responsibilities:
    - Check chemical identity and formulation.
    - Check crop and target-pest compatibility.
    - Check source references and verification status.
    - Reject recommendations with missing or unverified evidence.
    - Never invent chemical products, dosage, or application instructions.

Important:
    This module does not independently confirm pesticide registration.
    It relies on supplied evidence and trusted verification metadata.
    Final approval must also pass dosage, crop-pest, source, and safety checks.
"""

from typing import Any, Dict, List, Optional

from safety.safety_rules import (
    SafetyStatus,
    is_verified_status,
)


class ChemicalVerifier:
    """
    Verify the evidence associated with a chemical recommendation.

    Expected recommendation fields may include:

        {
            "chemical_name": "Example product",
            "active_ingredient": "Example ingredient",
            "formulation": "Example formulation",
            "crop": "Example crop",
            "target_pest": "Example pest",
            "verification_status": "verified",
            "crop_compatibility_verified": True,
            "pest_compatibility_verified": True,
            "registration_verified": True,
            "label_directions_verified": True,
            "source_ids": ["SRC001"],
            "evidence": [...]
        }

    These fields are illustrative. A field must only be marked verified
    when an appropriate verification process has actually established it.
    """

    def __init__(
        self,
        knowledge_base_loader: Any = None,
        trusted_source_ids: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize the verifier.

        Args:
            knowledge_base_loader:
                Optional KnowledgeBaseLoader instance.

            trusted_source_ids:
                Optional list of source IDs permitted by application
                policy. Membership alone does not prove that a source
                supports a particular claim.
        """

        self.knowledge_base_loader = knowledge_base_loader

        self.trusted_source_ids = {
            str(source_id).strip()
            for source_id in (trusted_source_ids or [])
            if source_id
        }

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------

    def verify(
        self,
        recommendation: Optional[Dict[str, Any]],
        crop: Optional[str] = None,
        target_pest: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a proposed chemical recommendation.

        Returns a structured result containing:
            status
            approved
            verification_required
            checks
            reasons
            warnings
            chemical_name
            crop
            target_pest
            source_ids

        A recommendation is approved by this module only when its
        required evidence is present and marked verified.
        """

        reasons: List[str] = []
        warnings: List[str] = []

        checks: Dict[str, bool] = {
            "chemical_identity": False,
            "active_ingredient": False,
            "formulation": False,
            "crop_identification": False,
            "target_pest_identification": False,
            "recommendation_verified": False,
            "registration_verified": False,
            "crop_compatibility_verified": False,
            "pest_compatibility_verified": False,
            "label_directions_verified": False,
            "source_ids_present": False,
            "source_evidence_verified": False,
            "claim_evidence_present": False,
        }

        if not isinstance(recommendation, dict):
            return self._result(
                status=SafetyStatus.VERIFICATION_REQUIRED,
                reasons=["A valid chemical recommendation object is required."],
                warnings=warnings,
                checks=checks,
            )

        # -----------------------------------------------------------
        # 1. Identify the chemical and product
        # -----------------------------------------------------------

        chemical_name = self._first_value(
            recommendation,
            ["chemical_name", "product_name", "pesticide_name"],
        )

        active_ingredient = self._first_value(
            recommendation,
            ["active_ingredient", "active_ingredients"],
        )

        formulation = self._first_value(
            recommendation,
            ["formulation", "product_formulation"],
        )

        checks["chemical_identity"] = self._has_value(chemical_name)
        checks["active_ingredient"] = self._has_value(active_ingredient)
        checks["formulation"] = self._has_value(formulation)

        if not checks["chemical_identity"]:
            reasons.append("The chemical or product identity is missing.")

        if not checks["active_ingredient"]:
            reasons.append("The active ingredient has not been identified.")

        if not checks["formulation"]:
            reasons.append("The product formulation has not been identified.")

        # -----------------------------------------------------------
        # 2. Identify crop and target pest
        # -----------------------------------------------------------

        record_crop = self._first_value(
            recommendation,
            ["crop", "crop_name", "crop_id"],
        )

        record_pest = self._first_value(
            recommendation,
            ["target_pest", "pest", "pest_name", "disease"],
        )

        effective_crop = crop or record_crop
        effective_pest = target_pest or record_pest

        checks["crop_identification"] = self._has_value(effective_crop)
        checks["target_pest_identification"] = self._has_value(
            effective_pest
        )

        if not checks["crop_identification"]:
            reasons.append("The target crop has not been identified.")

        if not checks["target_pest_identification"]:
            reasons.append("The target pest or disease has not been identified.")

        # -----------------------------------------------------------
        # 3. Check verification status
        # -----------------------------------------------------------

        verification_status = recommendation.get("verification_status")

        checks["recommendation_verified"] = is_verified_status(
            verification_status
        )

        if not checks["recommendation_verified"]:
            reasons.append(
                "The chemical recommendation does not have an accepted "
                "verified status."
            )

        # -----------------------------------------------------------
        # 4. Check product registration and compatibility
        # -----------------------------------------------------------

        checks["registration_verified"] = (
            recommendation.get("registration_verified") is True
        )

        checks["crop_compatibility_verified"] = (
            recommendation.get("crop_compatibility_verified") is True
        )

        checks["pest_compatibility_verified"] = (
            recommendation.get("pest_compatibility_verified") is True
        )

        checks["label_directions_verified"] = (
            recommendation.get("label_directions_verified") is True
        )

        if not checks["registration_verified"]:
            reasons.append(
                "Applicable product registration has not been verified."
            )

        if not checks["crop_compatibility_verified"]:
            reasons.append(
                "The product's suitability for the specified crop "
                "has not been verified."
            )

        if not checks["pest_compatibility_verified"]:
            reasons.append(
                "The product's suitability for the specified pest "
                "or disease has not been verified."
            )

        if not checks["label_directions_verified"]:
            reasons.append(
                "Applicable product-label directions have not been verified."
            )

        # -----------------------------------------------------------
        # 5. Check source references
        # -----------------------------------------------------------

        source_ids = self._extract_source_ids(recommendation)

        checks["source_ids_present"] = bool(source_ids)

        if not checks["source_ids_present"]:
            reasons.append(
                "No source IDs were supplied for the chemical recommendation."
            )

        source_evidence_verified = (
            recommendation.get("source_evidence_verified") is True
        )

        checks["source_evidence_verified"] = source_evidence_verified

        if not source_evidence_verified:
            reasons.append(
                "Evidence linking the sources to the specific chemical "
                "recommendation has not been verified."
            )

        # -----------------------------------------------------------
        # 6. Check supporting evidence
        # -----------------------------------------------------------

        evidence = recommendation.get("evidence")

        checks["claim_evidence_present"] = self._has_evidence(evidence)

        if not checks["claim_evidence_present"]:
            reasons.append(
                "Specific supporting evidence for the recommendation is missing."
            )

        # -----------------------------------------------------------
        # 7. Check optional trusted-source policy
        # -----------------------------------------------------------

        if self.trusted_source_ids:
            matching_source_ids = set(source_ids).intersection(
                self.trusted_source_ids
            )

            if not matching_source_ids:
                reasons.append(
                    "The recommendation does not reference a source "
                    "permitted by the configured source policy."
                )

        # -----------------------------------------------------------
        # 8. Final decision
        # -----------------------------------------------------------

        approved = all(checks.values()) and not reasons

        if approved:
            status = SafetyStatus.APPROVED
        else:
            status = SafetyStatus.VERIFICATION_REQUIRED

        if not approved:
            warnings.append(
                "Do not release this chemical recommendation as approved. "
                "Resolve the verification findings and run the complete "
                "AgriSathi safety pipeline."
            )

        return self._result(
            status=status,
            approved=approved,
            reasons=reasons,
            warnings=warnings,
            checks=checks,
            chemical_name=chemical_name,
            active_ingredient=active_ingredient,
            formulation=formulation,
            crop=effective_crop,
            target_pest=effective_pest,
            source_ids=source_ids,
        )

    # ---------------------------------------------------------------
    # Supporting methods
    # ---------------------------------------------------------------

    @staticmethod
    def _has_value(value: Any) -> bool:
        """Return True if a value is present and non-empty."""

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
    def _first_value(
        data: Dict[str, Any],
        keys: List[str],
    ) -> Any:
        """Return the first populated field from a list of alternatives."""

        for key in keys:
            value = data.get(key)

            if ChemicalVerifier._has_value(value):
                return value

        return None

    @staticmethod
    def _extract_source_ids(
        recommendation: Dict[str, Any],
    ) -> List[str]:
        """Extract unique source IDs from a recommendation."""

        values = recommendation.get("source_ids", [])

        if not isinstance(values, (list, tuple, set)):
            values = [values] if values else []

        normalized: List[str] = []

        for value in values:
            if isinstance(value, str) and value.strip():
                normalized.append(value.strip())

        return list(dict.fromkeys(normalized))

    @staticmethod
    def _has_evidence(evidence: Any) -> bool:
        """
        Check whether supporting evidence has been supplied.

        Actual evidence quality and claim-to-source matching must be
        assessed by the source-validation component.
        """

        if isinstance(evidence, str):
            return bool(evidence.strip())

        if isinstance(evidence, (list, tuple)):
            return len(evidence) > 0

        if isinstance(evidence, dict):
            return bool(evidence)

        return False

    @staticmethod
    def _result(
        status: SafetyStatus,
        reasons: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        checks: Optional[Dict[str, bool]] = None,
        approved: Optional[bool] = None,
        chemical_name: Any = None,
        active_ingredient: Any = None,
        formulation: Any = None,
        crop: Any = None,
        target_pest: Any = None,
        source_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Build a consistent result for downstream safety components."""

        is_approved = (
            status == SafetyStatus.APPROVED
            if approved is None
            else approved
        )

        return {
            "component": "chemical_verifier",
            "status": status.value,
            "approved": is_approved,
            "verification_required": not is_approved,
            "chemical_name": chemical_name,
            "active_ingredient": active_ingredient,
            "formulation": formulation,
            "crop": crop,
            "target_pest": target_pest,
            "source_ids": source_ids or [],
            "checks": checks or {},
            "reasons": reasons or [],
            "warnings": warnings or [],
        }


# ---------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------

def verify_chemical_recommendation(
    recommendation: Optional[Dict[str, Any]],
    crop: Optional[str] = None,
    target_pest: Optional[str] = None,
    knowledge_base_loader: Any = None,
) -> Dict[str, Any]:
    """
    Verify a chemical recommendation without manually creating
    a ChemicalVerifier instance.
    """

    verifier = ChemicalVerifier(
        knowledge_base_loader=knowledge_base_loader
    )

    return verifier.verify(
        recommendation=recommendation,
        crop=crop,
        target_pest=target_pest,
    )