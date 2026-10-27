"""
AgriSathi - Recommendation Engine

Purpose:
    Convert RuleEngine results into structured, evidence-based
    agricultural responses.

Responsibilities:
    - Handle the RuleEngine output contract.
    - Support English and Hindi response templates.
    - Extract evidence from bilingual agricultural records.
    - Preserve source IDs and verification statuses.
    - Handle clarification, missing information, and service failures.
    - Optionally use llama.cpp to rephrase supplied evidence.
    - Flag chemical and dosage information for safety verification.
    - Produce a structured response for SafetyEngine.

Important:
    This module does not independently verify agricultural claims.
    It must not invent missing facts, source references, dosages,
    weather measurements, or market prices.

    Its output is a candidate recommendation, not final approval.
"""

import json
import re
from typing import Any, Dict, List, Optional

from safety.safety_rules import is_verified_status


class RecommendationEngine:
    """Generate structured agricultural recommendations."""

    def __init__(
        self,
        llm_service: Any = None,
    ) -> None:
        """
        Args:
            llm_service:
                Optional service exposing:

                generate(
                    prompt,
                    system_prompt=...,
                    temperature=0.0
                )

                The service may use llama.cpp. It is not required
                for deterministic recommendations.
        """

        self.llm_service = llm_service

    # ---------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------

    def generate_recommendation(
        self,
        rule_result: Dict[str, Any],
        query: Optional[Dict[str, Any]] = None,
        use_llm: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a candidate response from RuleEngine output.

        Args:
            rule_result:
                Dictionary returned by RuleEngine.process_query().

            query:
                Optional parsed query returned by QueryParser.parse().

            use_llm:
                If True, attempt evidence-constrained LLM rephrasing.
                If the LLM is unavailable or produces invalid output,
                deterministic formatting is used.

        Returns:
            Structured recommendation dictionary.

        Main output fields:
            component
            status
            approved
            intent
            language
            answer
            evidence
            sources
            source_ids
            warnings
            requires_clarification
            chemical_verification_required
            dosage_verification_required
            safety_validation_required
            generation_method
        """

        if not isinstance(rule_result, dict):
            return self._error_result(
                "The Rule Engine result must be a dictionary."
            )

        query = query if isinstance(query, dict) else {}

        intent = self._normalize_identifier(
            rule_result.get(
                "intent",
                query.get("intent", "general_agriculture"),
            )
        )

        language = self._normalize_language(
            rule_result.get(
                "language",
                query.get("language", "en"),
            )
        )

        rule_status = str(
            rule_result.get("status", "")
        ).strip().lower()

        warnings = self._collect_warnings(
            rule_result.get("warnings"),
        )

        # -----------------------------------------------------------
        # 1. Handle unsuccessful RuleEngine results
        # -----------------------------------------------------------

        if rule_status in {
            "error",
            "failed",
            "failure",
        }:
            return self._error_result(
                "The agricultural information service encountered an error.",
                intent=intent,
                language=language,
                warnings=warnings,
            )

        if rule_status in {
            "needs_clarification",
        }:
            return self._clarification_result(
                intent=intent,
                language=language,
                query=query,
                warnings=warnings,
            )

        if rule_status in {
            "no_verified_information",
            "no_verified_information_available",
            "no_evidence",
            "not_found",
        }:
            return self._no_evidence_result(
                intent=intent,
                language=language,
                warnings=warnings,
            )

        if rule_status in {
            "external_data_unavailable",
            "live_data_unavailable",
        }:
            return self._external_data_unavailable_result(
                intent=intent,
                language=language,
                warnings=warnings,
            )

        # -----------------------------------------------------------
        # 2. Retrieve candidate records
        # -----------------------------------------------------------

        candidate_records = rule_result.get(
            "candidate_records",
            rule_result.get("matched_records", []),
        )

        if not isinstance(candidate_records, list):
            candidate_records = []

        # -----------------------------------------------------------
        # 3. Handle live-service intents separately
        # -----------------------------------------------------------

        if intent == "weather":
            return self._generate_live_data_response(
                rule_result=rule_result,
                query=query,
                intent=intent,
                language=language,
                warnings=warnings,
                use_llm=use_llm,
            )

        if intent == "mandi_prices":
            return self._generate_live_data_response(
                rule_result=rule_result,
                query=query,
                intent=intent,
                language=language,
                warnings=warnings,
                use_llm=use_llm,
            )

        # -----------------------------------------------------------
        # 4. Handle clarification and missing records
        # -----------------------------------------------------------

        if not candidate_records:
            if rule_result.get("requires_clarification") is True:
                return self._clarification_result(
                    intent=intent,
                    language=language,
                    query=query,
                    warnings=warnings,
                )

            return self._no_evidence_result(
                intent=intent,
                language=language,
                warnings=warnings,
            )

        # -----------------------------------------------------------
        # 5. Extract evidence and source metadata
        # -----------------------------------------------------------

        evidence = self._extract_evidence(
            candidate_records,
            language=language,
        )

        source_ids = self._collect_source_ids(
            rule_result=rule_result,
            records=candidate_records,
            evidence=evidence,
        )

        sources = self._collect_sources(
            rule_result=rule_result,
            records=candidate_records,
        )

        # -----------------------------------------------------------
        # 6. Preserve verification state
        # -----------------------------------------------------------

        verified_records = [
            record
            for record in candidate_records
            if is_verified_status(
                record.get("verification_status")
            )
        ]

        unverified_records = [
            record
            for record in candidate_records
            if not is_verified_status(
                record.get("verification_status")
            )
        ]

        if unverified_records:
            warnings.append(
                self._message(
                    language,
                    "Some retrieved agricultural information has not "
                    "been independently verified. Treat it as unverified.",
                    "प्राप्त कृषि जानकारी के कुछ हिस्सों का स्वतंत्र "
                    "सत्यापन नहीं हुआ है। इसे असत्यापित जानकारी मानें।",
                )
            )

        if not source_ids:
            warnings.append(
                self._message(
                    language,
                    "No source IDs are linked to the retrieved records.",
                    "प्राप्त रिकॉर्ड के साथ कोई स्रोत ID जुड़ी नहीं है।",
                )
            )

        # -----------------------------------------------------------
        # 7. Create deterministic candidate answer
        # -----------------------------------------------------------

        answer = self._format_evidence(
            intent=intent,
            evidence=evidence,
            language=language,
        )

        if not answer:
            return self._no_evidence_result(
                intent=intent,
                language=language,
                warnings=warnings,
            )

        generation_method = "deterministic"

        # -----------------------------------------------------------
        # 8. Optional LLM rephrasing
        # -----------------------------------------------------------

        if use_llm and self.llm_service is not None:
            rewritten = self._rephrase_with_llm(
                answer=answer,
                evidence=evidence,
                intent=intent,
                language=language,
            )

            if rewritten:
                answer = rewritten
                generation_method = "llm_rephrased"

            else:
                warnings.append(
                    self._message(
                        language,
                        "AI rephrasing was unavailable or unsuitable. "
                        "The evidence-based template was retained.",
                        "AI द्वारा पुनर्लेखन उपलब्ध नहीं था या उपयुक्त "
                        "नहीं था। मूल साक्ष्य-आधारित उत्तर रखा गया है।",
                    )
                )

        # -----------------------------------------------------------
        # 9. Identify safety requirements
        # -----------------------------------------------------------

        chemical_required = intent == "pest_management"

        dosage_required = intent == "fertilizer_advice"

        for record in candidate_records:
            if self._record_contains_chemical_information(record):
                chemical_required = True

            if self._record_contains_dosage_information(record):
                dosage_required = True

        # -----------------------------------------------------------
        # 10. Return structured candidate
        # -----------------------------------------------------------

        return {
            "component": "recommendation_engine",
            "status": "candidate",
            "approved": False,
            "intent": intent,
            "language": language,
            "answer": answer,
            "crop": query.get("entities", {}).get("crops", [None])[0] if query.get("entities", {}).get("crops") else None,
            "target_pest": query.get("entities", {}).get("pests", [None])[0] if query.get("entities", {}).get("pests") else None,
            "evidence": evidence,
            "sources": sources,
            "source_ids": source_ids,
            "verification_status": (
                "verified"
                if candidate_records
                and len(verified_records) == len(candidate_records)
                else "needs_source_verification"
            ),
            "record_counts": {
                "total": len(candidate_records),
                "verified": len(verified_records),
                "unverified": len(unverified_records),
            },
            "warnings": list(dict.fromkeys(warnings)),
            "requires_clarification": False,
            "chemical_verification_required": chemical_required,
            "dosage_verification_required": dosage_required,
            "safety_validation_required": True,
            "generation_method": generation_method,
        }

    # ---------------------------------------------------------------
    # Evidence extraction
    # ---------------------------------------------------------------

    def _extract_evidence(
        self,
        records: List[Dict[str, Any]],
        language: str,
    ) -> List[Dict[str, Any]]:
        """Convert knowledge-base records into structured evidence."""

        evidence_items: List[Dict[str, Any]] = []

        for record in records:
            if not isinstance(record, dict):
                continue

            crop = self._localized_value(
                record.get(
                    "name",
                    record.get("crop"),
                ),
                language,
            )

            if not crop:
                crop = self._localized_value(
                    record.get("crop_name"),
                    language,
                )

            pest = self._localized_value(
                record.get(
                    "pest",
                    record.get("pests"),
                ),
                language,
            )

            if not pest:
                pest = self._localized_value(
                    record.get("pests_and_diseases_as_listed"),
                    language,
                )

            guidance_fields = [
                "guidance",
                "recommendation",
                "management_methods",
                "management_strategies",
                "management_strategies_as_listed",
                "fertilizer_requirement_as_listed",
                "soil_and_irrigation_requirements_as_listed",
                "soil_requirements",
                "irrigation_requirement",
                "water_requirement",
                "season",
                "category",
                "description",
            ]

            guidance: List[str] = []

            for field in guidance_fields:
                value = record.get(field)

                localized = self._localized_value(
                    value,
                    language,
                )

                if localized:
                    guidance.append(localized)

            source_ids = self._normalize_source_ids(
                record.get("source_ids")
            )

            record_status = record.get(
                "verification_status",
                "unknown",
            )

            evidence_item = {
                "record_id": record.get("record_id"),
                "crop_id": record.get("crop_id"),
                "crop": crop,
                "pest": pest,
                "guidance": list(dict.fromkeys(guidance)),
                "source_ids": source_ids,
                "verification_status": record_status,
                "verified": is_verified_status(record_status),
            }

            # Preserve the original dataset values for downstream
            # traceability without inventing missing information.
            evidence_item["data_origin"] = record.get("data_origin")

            evidence_items.append(evidence_item)

        return evidence_items

    # ---------------------------------------------------------------
    # Response formatting
    # ---------------------------------------------------------------

    def _format_evidence(
        self,
        intent: str,
        evidence: List[Dict[str, Any]],
        language: str,
    ) -> str:
        """Create a response using only extracted evidence."""

        if not evidence:
            return ""

        headings = {
            "en": {
                "crop_information": "Crop information",
                "fertilizer_advice": "Fertilizer information",
                "pest_management": "Pest and disease information",
                "irrigation": "Irrigation information",
                "general_agriculture": "Agricultural information",
            },
            "hi": {
                "crop_information": "फसल संबंधी जानकारी",
                "fertilizer_advice": "उर्वरक संबंधी जानकारी",
                "pest_management": "कीट और रोग संबंधी जानकारी",
                "irrigation": "सिंचाई संबंधी जानकारी",
                "general_agriculture": "कृषि संबंधी जानकारी",
            },
        }

        language_headings = headings.get(language, headings["en"])

        heading = language_headings.get(
            intent,
            language_headings["general_agriculture"],
        )

        sections: List[str] = [heading]

        for item in evidence:
            crop = item.get("crop")

            if crop:
                sections.append(
                    self._message(
                        language,
                        f"Crop: {crop}",
                        f"फसल: {crop}",
                    )
                )

            for guidance in item.get("guidance", []):
                if guidance:
                    sections.append(guidance)

        answer = "\n".join(
            dict.fromkeys(
                section.strip()
                for section in sections
                if isinstance(section, str) and section.strip()
            )
        )

        # Pest management information is not automatically a verified
        # chemical recommendation.
        if intent == "pest_management":
            answer += "\n\n" + self._message(
                language,
                "Chemical products and application dosages have not "
                "been approved by this component. They require separate "
                "verification against applicable authoritative sources.",
                "इस घटक द्वारा रासायनिक उत्पादों और उनकी खुराक को "
                "स्वीकृति नहीं दी गई है। इनके लिए संबंधित आधिकारिक "
                "स्रोतों से अलग सत्यापन आवश्यक है।",
            )

        return answer.strip()

    # ---------------------------------------------------------------
    # Live-data formatting
    # ---------------------------------------------------------------

    def _generate_live_data_response(
        self,
        rule_result: Dict[str, Any],
        query: Dict[str, Any],
        intent: str,
        language: str,
        warnings: List[str],
        use_llm: bool,
    ) -> Dict[str, Any]:
        """
        Handle live-service results conservatively.

        This method does not fabricate weather or mandi values.
        The final live-data verification must be performed by SafetyEngine.
        """

        external_data = rule_result.get("external_data")

        if not isinstance(external_data, dict):
            external_data = rule_result.get("data")

        if not isinstance(external_data, dict):
            return self._external_data_unavailable_result(
                intent=intent,
                language=language,
                warnings=warnings,
            )

        if external_data.get("status") != "success":
            return self._external_data_unavailable_result(
                intent=intent,
                language=language,
                warnings=warnings,
            )

        # Preserve the external payload without inventing missing values.
        answer = self._format_live_data(
            external_data,
            intent,
            language,
        )

        if not answer:
            return self._external_data_unavailable_result(
                intent=intent,
                language=language,
                warnings=warnings,
            )

        return {
            "component": "recommendation_engine",
            "status": "candidate",
            "approved": False,
            "intent": intent,
            "language": language,
            "answer": answer,
            "evidence": [{
                "record_id": None,
                "crop_id": None,
                "crop": None,
                "pest": None,
                "guidance": [],
                "source_ids": [],
                "verification_status": "requires_live_data_validation",
                "verified": False,
                "external_data": external_data,
            }],
            "sources": [],
            "source_ids": [],
            "verification_status": "requires_live_data_validation",
            "warnings": list(dict.fromkeys(warnings)),
            "requires_clarification": False,
            "chemical_verification_required": False,
            "dosage_verification_required": False,
            "safety_validation_required": True,
            "generation_method": "live_service",
        }

    def _format_live_data(
        self,
        data: Dict[str, Any],
        intent: str,
        language: str,
    ) -> str:
        """Format recognized weather or mandi fields without inference."""

        lines: List[str] = []

        if intent == "weather":
            labels = {
                "en": {
                    "temperature_c": "Temperature",
                    "humidity_percent": "Humidity",
                    "wind_speed_mps": "Wind speed",
                    "rainfall_mm": "Rainfall",
                },
                "hi": {
                    "temperature_c": "तापमान",
                    "humidity_percent": "आर्द्रता",
                    "wind_speed_mps": "हवा की गति",
                    "rainfall_mm": "वर्षा",
                },
            }

            localized_labels = labels.get(language, labels["en"])

            for key, label in localized_labels.items():
                value = data.get(key)

                if value is not None:
                    lines.append(f"{label}: {value}")

            location = data.get("location")

            if location:
                lines.insert(
                    0,
                    self._message(
                        language,
                        f"Weather for {location}",
                        f"{location} के लिए मौसम",
                    ),
                )

        elif intent == "mandi_prices":
            labels = {
                "en": {
                    "minimum_price": "Minimum price",
                    "maximum_price": "Maximum price",
                    "modal_price": "Modal price",
                },
                "hi": {
                    "minimum_price": "न्यूनतम मूल्य",
                    "maximum_price": "अधिकतम मूल्य",
                    "modal_price": "मॉडल मूल्य",
                },
            }

            localized_labels = labels.get(language, labels["en"])

            for key, label in localized_labels.items():
                value = data.get(key)

                if value is not None:
                    lines.append(f"{label}: ₹{value}")

            market = data.get("market")

            if market:
                lines.insert(
                    0,
                    self._message(
                        language,
                        f"Mandi: {market}",
                        f"मंडी: {market}",
                    ),
                )

            unit = data.get("unit")

            if unit:
                lines.append(
                    self._message(
                        language,
                        f"Unit: {unit}",
                        f"इकाई: {unit}",
                    )
                )

        if not lines:
            return ""

        timestamp = (
            data.get("timestamp")
            or data.get("retrieved_at")
            or data.get("retrieval_timestamp")
        )

        if timestamp:
            lines.append(
                self._message(
                    language,
                    f"Data retrieved at: {timestamp}",
                    f"डेटा प्राप्त करने का समय: {timestamp}",
                )
            )

        return "\n".join(lines)

    # ---------------------------------------------------------------
    # LLM rephrasing
    # ---------------------------------------------------------------

    def _rephrase_with_llm(
        self,
        answer: str,
        evidence: List[Dict[str, Any]],
        intent: str,
        language: str,
    ) -> Optional[str]:
        """
        Ask the LLM to rephrase existing evidence.

        This method rejects empty output and output containing obvious
        unsupported numerical claims. It does not replace the SafetyEngine.
        """

        if self.llm_service is None:
            return None

        system_prompt = (
            "You are AgriSathi, a highly experienced and friendly agricultural expert speaking to a farmer. "
            "You have been provided with verified agricultural data from a government database.\n"
            "YOUR JOB:\n"
            "1. Read the verified data provided in the context.\n"
            "2. Explain it to the farmer in a warm, conversational, and easy-to-understand way.\n"
            "3. If there are technical terms (like 'CRI stage' or 'N:P:K'), briefly explain what they mean in simple terms.\n"
            "4. Use bullet points or short paragraphs to make it readable.\n"
            "5. End with a helpful, encouraging note.\n\n"
            "STRICT RULES:\n"
            "- You MUST NOT invent any facts, chemicals, dosages, or prices that are not in the provided context.\n"
            "- If the context does not contain the answer, say: 'I don't have verified information on this specific detail.'\n"
            "- Return ONLY the final response to the farmer. Do not include 'Here is the rewritten text:'."
        )

        prompt = (
            f"Language: {language}\n"
            f"Intent: {intent}\n\n"
            f"Existing answer:\n{answer}\n\n"
            "Evidence supplied by the rule engine:\n"
            f"{json.dumps(evidence, ensure_ascii=False)}\n\n"
            "Rewrite the answer without adding facts."
        )

        try:
            rewritten = self.llm_service.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.0,
            )

        except Exception:
            return None

        if not isinstance(rewritten, str):
            return None

        rewritten = rewritten.strip()

        if not rewritten:
            return None

        if self._contains_new_numerical_claim(
            original=answer,
            rewritten=rewritten,
        ):
            return None

        return rewritten

    @staticmethod
    def _contains_new_numerical_claim(
        original: str,
        rewritten: str,
    ) -> bool:
        """
        Detect obvious newly introduced numbers.

        This conservative heuristic cannot prove that the rewrite is
        factually equivalent. SafetyEngine must still validate the result.
        """

        original_numbers = re.findall(
            r"\d+(?:\.\d+)?",
            original,
        )

        rewritten_numbers = re.findall(
            r"\d+(?:\.\d+)?",
            rewritten,
        )

        original_counts: Dict[str, int] = {}

        for number in original_numbers:
            original_counts[number] = original_counts.get(number, 0) + 1

        rewritten_counts: Dict[str, int] = {}

        for number in rewritten_numbers:
            rewritten_counts[number] = rewritten_counts.get(number, 0) + 1

        for number, count in rewritten_counts.items():
            if count > original_counts.get(number, 0):
                return True

        return False

    # ---------------------------------------------------------------
    # Record and source helpers
    # ---------------------------------------------------------------

    @staticmethod
    def _collect_source_ids(
        rule_result: Dict[str, Any],
        records: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
    ) -> List[str]:
        """Collect unique source IDs from all available evidence."""

        source_ids: List[str] = []

        for container in (rule_result,):
            source_ids.extend(
                RecommendationEngine._normalize_source_ids(
                    container.get("source_ids")
                )
            )

        for record in records:
            if isinstance(record, dict):
                source_ids.extend(
                    RecommendationEngine._normalize_source_ids(
                        record.get("source_ids")
                    )
                )

        for item in evidence:
            source_ids.extend(
                RecommendationEngine._normalize_source_ids(
                    item.get("source_ids")
                )
            )

        return list(dict.fromkeys(source_ids))

    @staticmethod
    def _collect_sources(
        rule_result: Dict[str, Any],
        records: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Collect supplied source metadata without fabricating entries."""

        sources: List[Dict[str, Any]] = []

        rule_sources = rule_result.get("sources", [])

        if isinstance(rule_sources, list):
            sources.extend(
                source
                for source in rule_sources
                if isinstance(source, dict)
            )

        for record in records:
            if not isinstance(record, dict):
                continue

            record_sources = record.get("sources", [])

            if isinstance(record_sources, list):
                sources.extend(
                    source
                    for source in record_sources
                    if isinstance(source, dict)
                )

        # Deduplicate by source_id where available.
        unique: List[Dict[str, Any]] = []
        seen = set()

        for source in sources:
            source_id = source.get("source_id")

            if source_id:
                if source_id in seen:
                    continue

                seen.add(source_id)

            unique.append(source)

        return unique

    @staticmethod
    def _normalize_source_ids(value: Any) -> List[str]:
        """Normalize source IDs to unique, non-empty strings."""

        if value is None:
            return []

        if isinstance(value, str):
            values = [value]
        elif isinstance(value, (list, tuple, set)):
            values = list(value)
        else:
            return []

        normalized = [
            item.strip()
            for item in values
            if isinstance(item, str) and item.strip()
        ]

        return list(dict.fromkeys(normalized))

    # ---------------------------------------------------------------
    # Data interpretation helpers
    # ---------------------------------------------------------------

    @staticmethod
    def _localized_value(
        value: Any,
        language: str,
    ) -> str:
        """
        Extract text from strings or bilingual dictionaries.

        Expected bilingual structure:
            {"en": "...", "hi": "..."}
        """

        if value is None:
            return ""

        if isinstance(value, str):
            return value.strip()

        if isinstance(value, dict):
            preferred = value.get(language)

            if isinstance(preferred, str) and preferred.strip():
                return preferred.strip()

            fallback = value.get("en")

            if isinstance(fallback, str) and fallback.strip():
                return fallback.strip()

            # Do not stringify the entire dictionary into the response.
            return ""

        if isinstance(value, list):
            parts = [
                RecommendationEngine._localized_value(
                    item,
                    language,
                )
                for item in value
            ]

            return "; ".join(
                part for part in parts if part
            )

        return ""

    @staticmethod
    def _record_contains_chemical_information(
        record: Dict[str, Any],
    ) -> bool:
        """Detect explicitly populated chemical fields."""

        fields = [
            "chemical_name",
            "product_name",
            "active_ingredient",
            "chemical_recommendations",
            "chemical_dosage",
            "pesticide_dosage",
        ]

        for field in fields:
            value = record.get(field)

            if value is not None and value != "" and value != []:
                return True

        return False

    @staticmethod
    def _record_contains_dosage_information(
        record: Dict[str, Any],
    ) -> bool:
        """Detect explicitly populated dosage fields."""

        fields = [
            "application_dosage",
            "chemical_dosage",
            "fertilizer_dosage",
            "application_rate",
            "recommended_rate",
            "dosage",
        ]

        for field in fields:
            value = record.get(field)

            if value is not None and value != "" and value != []:
                return True

        return False

    # ---------------------------------------------------------------
    # Result helpers
    # ---------------------------------------------------------------

    @staticmethod
    def _collect_warnings(value: Any) -> List[str]:
        """Normalize warning messages."""

        if value is None:
            return []

        if isinstance(value, str):
            return [value] if value.strip() else []

        if isinstance(value, list):
            return [
                warning.strip()
                for warning in value
                if isinstance(warning, str) and warning.strip()
            ]

        return []

    @staticmethod
    def _normalize_identifier(value: Any) -> str:
        """Normalize intent values."""

        if not isinstance(value, str) or not value.strip():
            return "general_agriculture"

        return (
            value.strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

    @staticmethod
    def _normalize_language(value: Any) -> str:
        """Normalize supported language identifiers."""

        if not isinstance(value, str):
            return "en"

        language = (
            value.strip()
            .lower()
            .replace("_", "-")
            .split("-")[0]
        )

        return language if language in {"en", "hi"} else "en"

    @staticmethod
    def _message(
        language: str,
        english: str,
        hindi: str,
    ) -> str:
        """Select a supported language message."""

        return hindi if language == "hi" else english

    def _clarification_result(
        self,
        intent: str,
        language: str,
        query: Dict[str, Any],
        warnings: List[str],
    ) -> Dict[str, Any]:
        """Return a clarification response."""

        question = self._message(
            language,
            "Please specify the crop and describe the agricultural issue "
            "so I can retrieve relevant information.",
            "कृपया फसल का नाम और कृषि संबंधी समस्या बताएं, "
            "ताकि मैं संबंधित जानकारी खोज सकूँ।",
        )

        return {
            "component": "recommendation_engine",
            "status": "needs_clarification",
            "approved": False,
            "intent": intent,
            "language": language,
            "answer": question,
            "evidence": [],
            "sources": [],
            "source_ids": [],
            "warnings": warnings,
            "requires_clarification": True,
            "chemical_verification_required": False,
            "dosage_verification_required": False,
            "safety_validation_required": True,
            "generation_method": "deterministic",
        }

    def _no_evidence_result(
        self,
        intent: str,
        language: str,
        warnings: List[str],
    ) -> Dict[str, Any]:
        """Return a response when suitable evidence is unavailable."""

        answer = self._message(
            language,
            "I could not find sufficient agricultural information "
            "to provide a reliable recommendation. Please consult "
            "your local Krishi Vigyan Kendra or agricultural officer.",
            "विश्वसनीय सलाह देने के लिए पर्याप्त कृषि जानकारी नहीं मिली। "
            "कृपया अपने स्थानीय कृषि विज्ञान केंद्र या कृषि अधिकारी "
            "से संपर्क करें।",
        )

        return {
            "component": "recommendation_engine",
            "status": "no_evidence",
            "approved": False,
            "intent": intent,
            "language": language,
            "answer": answer,
            "evidence": [],
            "sources": [],
            "source_ids": [],
            "warnings": warnings,
            "requires_clarification": False,
            "chemical_verification_required": False,
            "dosage_verification_required": False,
            "safety_validation_required": True,
            "generation_method": "deterministic",
        }

    def _external_data_unavailable_result(
        self,
        intent: str,
        language: str,
        warnings: List[str],
    ) -> Dict[str, Any]:
        """Return a safe response when live information is unavailable."""

        if intent == "weather":
            answer = self._message(
                language,
                "Current weather information is unavailable. "
                "Please check an authoritative weather service.",
                "वर्तमान मौसम की जानकारी उपलब्ध नहीं है। "
                "कृपया किसी आधिकारिक मौसम सेवा से जानकारी प्राप्त करें।",
            )

        elif intent == "mandi_prices":
            answer = self._message(
                language,
                "Current mandi prices are unavailable. Please check "
                "an authoritative market-price service for your market.",
                "वर्तमान मंडी भाव उपलब्ध नहीं हैं। कृपया अपने बाजार के "
                "लिए किसी आधिकारिक मंडी मूल्य सेवा से जानकारी प्राप्त करें।",
            )

        else:
            answer = self._message(
                language,
                "The requested external information is unavailable.",
                "अनुरोधित बाहरी जानकारी उपलब्ध नहीं है।",
            )

        return {
            "component": "recommendation_engine",
            "status": "external_data_unavailable",
            "approved": False,
            "intent": intent,
            "language": language,
            "answer": answer,
            "evidence": [],
            "sources": [],
            "source_ids": [],
            "warnings": warnings,
            "requires_clarification": False,
            "chemical_verification_required": False,
            "dosage_verification_required": False,
            "safety_validation_required": True,
            "generation_method": "deterministic",
        }

    @staticmethod
    def _error_result(
        message: str,
        intent: str = "general_agriculture",
        language: str = "en",
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Return a structured error result."""

        return {
            "component": "recommendation_engine",
            "status": "error",
            "approved": False,
            "intent": intent,
            "language": language,
            "answer": "",
            "evidence": [],
            "sources": [],
            "source_ids": [],
            "warnings": list(warnings or []) + [message],
            "requires_clarification": False,
            "chemical_verification_required": False,
            "dosage_verification_required": False,
            "safety_validation_required": True,
            "generation_method": "deterministic",
        }


# -------------------------------------------------------------------
# Convenience function
# -------------------------------------------------------------------

def generate_recommendation(
    rule_result: Dict[str, Any],
    query: Optional[Dict[str, Any]] = None,
    llm_service: Any = None,
    use_llm: bool = False,
) -> Dict[str, Any]:
    """Generate a recommendation without manually creating an instance."""

    engine = RecommendationEngine(
        llm_service=llm_service,
    )

    return engine.generate_recommendation(
        rule_result=rule_result,
        query=query,
        use_llm=use_llm,
    )