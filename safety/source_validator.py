"""
AgriSathi - Source Validator

Purpose:
    Validate source references and supporting evidence for agricultural
    recommendations.

Responsibilities:
    - Load source metadata from sources.json or KnowledgeBaseLoader.
    - Check whether referenced source IDs exist.
    - Check source metadata and URL format.
    - Check whether evidence is provided for claims.
    - Check whether evidence explicitly supports the relevant claims.
    - Identify unverified records and unsupported claims.
    - Return structured results for SafetyEngine.

Important:
    A valid source ID does not prove that a source supports a claim.
    Source existence, source authenticity, and claim support are distinct
    checks.

    This module does not independently browse the internet or verify
    the truth of a source's contents. Any claim marked as supported
    must have been checked against actual source material by a trusted
    verification process.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from safety.safety_rules import (
    SafetyStatus,
    is_verified_status,
)


class SourceValidator:
    """Validate source references and evidence for AgriSathi responses."""

    def __init__(
        self,
        sources_file: Optional[str] = None,
        knowledge_base_loader: Any = None,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Initialize the source validator.

        Args:
            sources_file:
                Optional path to knowledge_base/sources.json.

            knowledge_base_loader:
                Optional initialized KnowledgeBaseLoader instance.

            sources:
                Optional list of source dictionaries. When supplied,
                this takes precedence over loading a file.
        """

        self.sources_file = Path(sources_file) if sources_file else None
        self.knowledge_base_loader = knowledge_base_loader

        self.sources: Dict[str, Dict[str, Any]] = {}
        self.load_errors: List[str] = []

        if sources is not None:
            self._load_from_list(sources)
        elif self.sources_file is not None:
            self._load_from_file(self.sources_file)
        elif self.knowledge_base_loader is not None:
            self._load_from_loader()

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------

    def validate(
        self,
        recommendation: Optional[Dict[str, Any]] = None,
        claims: Optional[List[Any]] = None,
        source_ids: Optional[List[str]] = None,
        require_sources: bool = True,
        require_claim_evidence: bool = True,
        require_verified_record: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate source references and supporting evidence.

        Args:
            recommendation:
                Optional recommendation or response dictionary.

            claims:
                Optional list of claim dictionaries or strings.

                A claim dictionary may contain:
                    {
                        "claim": "Claim text",
                        "source_ids": ["SRC001"],
                        "evidence": "Relevant excerpt",
                        "verified": True
                    }

                The verified flag must come from a trusted review process.

            source_ids:
                Optional source IDs to validate directly.

            require_sources:
                Require at least one valid source for a sourced response.

            require_claim_evidence:
                Require claim-specific evidence for supplied claims.

            require_verified_record:
                Require the recommendation's verification status to be
                one of the recognized verified statuses.

        Returns:
            A dictionary containing the validation status, source details,
            claim-level findings, reasons, and warnings.
        """

        reasons: List[str] = list(self.load_errors)
        warnings: List[str] = []

        checks: Dict[str, bool] = {
            "sources_loaded": bool(self.sources),
            "source_ids_present": False,
            "all_sources_exist": False,
            "source_metadata_valid": False,
            "source_urls_valid": False,
            "claim_evidence_present": False,
            "claims_supported": False,
            "record_verified": False,
        }

        if recommendation is not None and not isinstance(
            recommendation, dict
        ):
            return self._result(
                status=SafetyStatus.VERIFICATION_REQUIRED,
                reasons=["The recommendation must be a dictionary."],
                warnings=warnings,
                checks=checks,
            )

        recommendation = recommendation or {}

        # -----------------------------------------------------------
        # 1. Collect source IDs
        # -----------------------------------------------------------

        collected_source_ids = self._normalize_source_ids(source_ids)

        if not collected_source_ids:
            collected_source_ids.extend(
                self._normalize_source_ids(
                    recommendation.get("source_ids")
                )
            )

        if not collected_source_ids:
            collected_source_ids.extend(
                self._source_ids_from_evidence(
                    recommendation.get("evidence")
                )
            )

        collected_source_ids = list(dict.fromkeys(collected_source_ids))

        checks["source_ids_present"] = bool(collected_source_ids)

        if require_sources and not collected_source_ids:
            reasons.append(
                "No source IDs were provided for the recommendation."
            )

        # -----------------------------------------------------------
        # 2. Validate source IDs and metadata
        # -----------------------------------------------------------

        source_results: List[Dict[str, Any]] = []

        all_sources_exist = bool(collected_source_ids)
        all_metadata_valid = bool(collected_source_ids)
        all_urls_valid = bool(collected_source_ids)

        for source_id in collected_source_ids:
            source = self.sources.get(source_id)

            if source is None:
                all_sources_exist = False
                all_metadata_valid = False
                all_urls_valid = False

                source_results.append({
                    "source_id": source_id,
                    "exists": False,
                    "metadata_valid": False,
                    "url_valid": False,
                    "reasons": [
                        "The source ID does not exist in the loaded registry."
                    ],
                })

                reasons.append(
                    f"Source ID '{source_id}' was not found in sources.json."
                )

                continue

            metadata_valid = self._metadata_is_valid(source)
            url_valid = self._url_is_valid(source.get("url"))

            if not metadata_valid:
                all_metadata_valid = False
                reasons.append(
                    f"Source '{source_id}' has incomplete metadata."
                )

            if not url_valid:
                all_urls_valid = False
                reasons.append(
                    f"Source '{source_id}' has an invalid or missing URL."
                )

            source_results.append({
                "source_id": source_id,
                "exists": True,
                "metadata_valid": metadata_valid,
                "url_valid": url_valid,
                "name": source.get("name"),
                "url": source.get("url"),
                "information_categories": source.get(
                    "information_categories", []
                ),
            })

        checks["all_sources_exist"] = all_sources_exist
        checks["source_metadata_valid"] = all_metadata_valid
        checks["source_urls_valid"] = all_urls_valid

        # -----------------------------------------------------------
        # 3. Validate record verification status
        # -----------------------------------------------------------

        record_status = recommendation.get("verification_status")

        checks["record_verified"] = is_verified_status(record_status)

        if require_verified_record and not checks["record_verified"]:
            reasons.append(
                "The recommendation's verification status is missing "
                "or does not indicate verified information."
            )

        # -----------------------------------------------------------
        # 4. Validate claims and supporting evidence
        # -----------------------------------------------------------

        if claims is None:
            claims = self._extract_claims(recommendation)

        if not isinstance(claims, list):
            claims = []

        claim_results: List[Dict[str, Any]] = []

        if claims:
            checks["claim_evidence_present"] = any(
                self._claim_has_evidence(claim)
                for claim in claims
            )

            every_claim_supported = True

            for index, claim in enumerate(claims, start=1):
                result = self._validate_claim(
                    claim=claim,
                    index=index,
                    known_source_ids=collected_source_ids,
                )

                claim_results.append(result)

                if not result["supported"]:
                    every_claim_supported = False

                    reasons.extend(
                        result["reasons"]
                    )

            checks["claims_supported"] = (
                every_claim_supported and bool(claim_results)
            )

            if require_claim_evidence:
                if not checks["claim_evidence_present"]:
                    reasons.append(
                        "The claims have no supporting evidence excerpts "
                        "or evidence references."
                    )

                if not checks["claims_supported"]:
                    reasons.append(
                        "One or more claims lack verified supporting evidence."
                    )

        else:
            checks["claim_evidence_present"] = False
            checks["claims_supported"] = False

            if require_claim_evidence:
                reasons.append(
                    "No individual claims were provided for evidence validation."
                )

        # -----------------------------------------------------------
        # 5. Determine final component status
        # -----------------------------------------------------------

        checks_passed = (
            (checks["all_sources_exist"] or not require_sources)
            and (checks["source_metadata_valid"] or not require_sources)
            and (checks["source_urls_valid"] or not require_sources)
            and (
                checks["record_verified"]
                or not require_verified_record
            )
            and (
                checks["claims_supported"]
                if require_claim_evidence
                else True
            )
        )

        approved = checks_passed and not reasons

        if approved:
            status = SafetyStatus.APPROVED
        else:
            status = SafetyStatus.VERIFICATION_REQUIRED

        if not approved:
            warnings.append(
                "Do not mark the recommendation as source-verified. "
                "Review the findings and validate the actual supporting "
                "documents before release."
            )

        return self._result(
            status=status,
            approved=approved,
            reasons=list(dict.fromkeys(reasons)),
            warnings=warnings,
            checks=checks,
            source_ids=collected_source_ids,
            source_results=source_results,
            claim_results=claim_results,
        )

    # ---------------------------------------------------------------
    # Source loading
    # ---------------------------------------------------------------

    def _load_from_file(self, path: Path) -> None:
        """Load sources from the project's JSON source registry."""

        import json

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                source_list = data.get("sources", [])
            elif isinstance(data, list):
                source_list = data
            else:
                raise ValueError(
                    "The source registry must be a JSON object or array."
                )

            if not isinstance(source_list, list):
                raise ValueError(
                    "The 'sources' field must contain a JSON array."
                )

            self._load_from_list(source_list)

        except (OSError, ValueError, TypeError) as exc:
            self.load_errors.append(
                f"Unable to load source registry '{path}': {exc}"
            )

    def _load_from_loader(self) -> None:
        """
        Attempt to retrieve source records from KnowledgeBaseLoader.

        Supports loaders exposing get_records('sources').
        """

        getter = getattr(
            self.knowledge_base_loader,
            "get_records",
            None,
        )

        if not callable(getter):
            self.load_errors.append(
                "The knowledge-base loader does not expose get_records()."
            )
            return

        try:
            source_list = getter("sources")

            if isinstance(source_list, list):
                self._load_from_list(source_list)
            else:
                self.load_errors.append(
                    "The loader did not return a source list."
                )

        except Exception as exc:
            self.load_errors.append(
                f"Unable to retrieve sources from the knowledge base: {exc}"
            )

    def _load_from_list(self, source_list: List[Any]) -> None:
        """Index source entries by their source_id."""

        for source in source_list:
            if not isinstance(source, dict):
                self.load_errors.append(
                    "A source entry is not a JSON object."
                )
                continue

            source_id = source.get("source_id")

            if not isinstance(source_id, str) or not source_id.strip():
                self.load_errors.append(
                    "A source entry is missing a valid source_id."
                )
                continue

            source_id = source_id.strip()

            if source_id in self.sources:
                self.load_errors.append(
                    f"Duplicate source ID detected: '{source_id}'."
                )
                continue

            self.sources[source_id] = source

    # ---------------------------------------------------------------
    # Claim validation
    # ---------------------------------------------------------------

    def _validate_claim(
        self,
        claim: Any,
        index: int,
        known_source_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Validate the supplied evidence metadata for one claim.

        The 'verified' flag is trusted only as an assertion from the
        upstream verification process. This method cannot independently
        establish whether the quoted material proves the claim.
        """

        reasons: List[str] = []

        if isinstance(claim, str):
            claim_text = claim.strip()
            evidence = None
            claim_source_ids: List[str] = []
            verified = False

        elif isinstance(claim, dict):
            claim_text = str(
                claim.get("claim", claim.get("text", ""))
            ).strip()

            evidence = claim.get(
                "evidence",
                claim.get("evidence_excerpt"),
            )

            claim_source_ids = self._normalize_source_ids(
                claim.get("source_ids")
            )

            verified = claim.get("verified") is True

        else:
            return {
                "claim_index": index,
                "supported": False,
                "reasons": ["The claim has an unsupported data format."],
            }

        if not claim_text:
            reasons.append("The claim text is missing.")

        if not self._has_value(evidence):
            reasons.append(
                "No evidence excerpt or evidence reference was provided."
            )

        if not claim_source_ids:
            claim_source_ids = list(known_source_ids)

        if not claim_source_ids:
            reasons.append(
                "The claim has no associated source IDs."
            )

        missing_sources = [
            source_id
            for source_id in claim_source_ids
            if source_id not in self.sources
        ]

        if missing_sources:
            reasons.append(
                "The claim references unknown source IDs: "
                + ", ".join(missing_sources)
                + "."
            )

        if not verified:
            reasons.append(
                "The claim has not been explicitly verified against "
                "its supporting source material."
            )

        supported = (
            bool(claim_text)
            and self._has_value(evidence)
            and bool(claim_source_ids)
            and not missing_sources
            and verified
            and not reasons
        )

        return {
            "claim_index": index,
            "claim": claim_text,
            "source_ids": claim_source_ids,
            "evidence_present": self._has_value(evidence),
            "verified": verified,
            "supported": supported,
            "reasons": reasons,
        }

    # ---------------------------------------------------------------
    # Utility functions
    # ---------------------------------------------------------------

    @staticmethod
    def _normalize_source_ids(value: Any) -> List[str]:
        """Normalize source IDs into a list of unique strings."""

        if value is None:
            return []

        if isinstance(value, str):
            values = [value]
        elif isinstance(value, (list, tuple, set)):
            values = list(value)
        else:
            return []

        normalized = []

        for item in values:
            if isinstance(item, str) and item.strip():
                normalized.append(item.strip())

        return list(dict.fromkeys(normalized))

    @classmethod
    def _source_ids_from_evidence(cls, evidence: Any) -> List[str]:
        """Extract source IDs from structured evidence objects."""

        source_ids: List[str] = []

        if isinstance(evidence, dict):
            source_ids.extend(
                cls._normalize_source_ids(
                    evidence.get("source_ids")
                )
            )

            source_ids.extend(
                cls._normalize_source_ids(
                    evidence.get("information_source_ids")
                )
            )

        elif isinstance(evidence, list):
            for item in evidence:
                if isinstance(item, dict):
                    source_ids.extend(
                        cls._normalize_source_ids(
                            item.get("source_ids")
                        )
                    )

                    source_ids.extend(
                        cls._normalize_source_ids(
                            item.get("information_source_ids")
                        )
                    )

        return list(dict.fromkeys(source_ids))

    @staticmethod
    def _metadata_is_valid(source: Dict[str, Any]) -> bool:
        """Check the minimum required metadata fields."""

        source_id = source.get("source_id")
        name = source.get("name")
        categories = source.get("information_categories")

        return (
            isinstance(source_id, str)
            and bool(source_id.strip())
            and isinstance(name, str)
            and bool(name.strip())
            and isinstance(categories, list)
            and bool(categories)
        )

    @staticmethod
    def _url_is_valid(value: Any) -> bool:
        """
        Check URL syntax.

        This does not confirm that the website exists, is reachable,
        belongs to the named organization, or supports a particular claim.
        """

        if not isinstance(value, str) or not value.strip():
            return False

        try:
            parsed = urlparse(value.strip())

            return (
                parsed.scheme in {"https", "http"}
                and bool(parsed.netloc)
                and "." in parsed.netloc
                and not any(character.isspace() for character in value)
            )

        except ValueError:
            return False

    @staticmethod
    def _has_value(value: Any) -> bool:
        """Check whether an evidence value is present."""

        if value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        if isinstance(value, (list, tuple, set)):
            return len(value) > 0

        if isinstance(value, dict):
            return bool(value)

        return True

    @classmethod
    def _extract_claims(
        cls,
        recommendation: Dict[str, Any],
    ) -> List[Any]:
        """
        Extract claims from common recommendation structures.

        A general answer string is not automatically treated as a
        collection of verified claims.
        """

        claims = recommendation.get("claims")

        if isinstance(claims, list):
            return claims

        evidence = recommendation.get("evidence")

        if isinstance(evidence, list):
            extracted: List[Any] = []

            for item in evidence:
                if isinstance(item, dict):
                    extracted.append({
                        "claim": item.get(
                            "claim",
                            item.get("text", ""),
                        ),
                        "source_ids": item.get(
                            "source_ids",
                            item.get("information_source_ids", []),
                        ),
                        "evidence": item.get(
                            "evidence",
                            item.get("evidence_excerpt"),
                        ),
                        "verified": item.get("verified") is True,
                    })

            return extracted

        return []

    @staticmethod
    def _claim_has_evidence(claim: Any) -> bool:
        """Determine whether a claim contains an evidence field."""

        if not isinstance(claim, dict):
            return False

        evidence = claim.get(
            "evidence",
            claim.get("evidence_excerpt"),
        )

        if evidence is None:
            return False

        if isinstance(evidence, str):
            return bool(evidence.strip())

        if isinstance(evidence, (dict, list)):
            return bool(evidence)

        return False

    # ---------------------------------------------------------------
    # Result formatting
    # ---------------------------------------------------------------

    @staticmethod
    def _result(
        status: SafetyStatus,
        reasons: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        checks: Optional[Dict[str, bool]] = None,
        approved: Optional[bool] = None,
        source_ids: Optional[List[str]] = None,
        source_results: Optional[List[Dict[str, Any]]] = None,
        claim_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Build a consistent response for downstream safety components."""

        is_approved = (
            status == SafetyStatus.APPROVED
            if approved is None
            else approved
        )

        return {
            "component": "source_validator",
            "status": status.value,
            "approved": is_approved,
            "verification_required": not is_approved,
            "source_ids": source_ids or [],
            "source_results": source_results or [],
            "claim_results": claim_results or [],
            "checks": checks or {},
            "reasons": reasons or [],
            "warnings": warnings or [],
        }


# -------------------------------------------------------------------
# Convenience function
# -------------------------------------------------------------------

def validate_sources(
    recommendation: Optional[Dict[str, Any]] = None,
    claims: Optional[List[Any]] = None,
    source_ids: Optional[List[str]] = None,
    sources_file: Optional[str] = None,
    knowledge_base_loader: Any = None,
    require_sources: bool = True,
    require_claim_evidence: bool = True,
    require_verified_record: bool = True,
) -> Dict[str, Any]:
    """Validate source references without manually creating an instance."""

    validator = SourceValidator(
        sources_file=sources_file,
        knowledge_base_loader=knowledge_base_loader,
    )

    return validator.validate(
        recommendation=recommendation,
        claims=claims,
        source_ids=source_ids,
        require_sources=require_sources,
        require_claim_evidence=require_claim_evidence,
        require_verified_record=require_verified_record,
    )