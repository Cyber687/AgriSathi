"""
AgriSathi - Crop-Pest Compatibility Validator
"""
from typing import Any, Dict, List, Optional
from safety.safety_rules import SafetyStatus, is_verified_status

class CropPestValidator:
    def __init__(self, knowledge_base_loader: Any = None):
        self.knowledge_base_loader = knowledge_base_loader

    def validate(
        self,
        crop: Optional[str] = None,
        pest: Optional[str] = None,
        recommendation: Optional[Dict[str, Any]] = None,
        records: Optional[List[Dict[str, Any]]] = None,
        require_verified_evidence: bool = True,
    ) -> Dict[str, Any]:
        reasons = []
        warnings = []
        checks = {
            "crop_identified": False,
            "pest_identified": False,
            "records_available": False,
            "crop_match_found": False,
            "pest_match_found": False,
            "relationship_supported": False,
            "verified_evidence_available": False,
            "management_evidence_available": False,
            "sources_available": False,
        }

        if isinstance(recommendation, dict):
            crop = crop or self._first_value(recommendation, ["crop", "crop_name"])
            pest = pest or self._first_value(recommendation, ["target_pest", "pest", "pest_name"])

        crop_text = self._normalize(crop)
        pest_text = self._normalize(pest)

        checks["crop_identified"] = bool(crop_text)
        checks["pest_identified"] = bool(pest_text)

        if not crop_text:
            reasons.append("The target crop has not been identified.")
            return self._result(SafetyStatus.CLARIFICATION_REQUIRED, crop, pest, reasons=reasons, warnings=warnings, checks=checks)

        if records is None:
            records = self._find_records(crop, pest)

        if not records:
            reasons.append("No relevant pest-management records were found for the supplied crop.")
            return self._result(SafetyStatus.VERIFICATION_REQUIRED, crop, pest, reasons=reasons, warnings=warnings, checks=checks)

        checks["records_available"] = True
        matching_records = []
        verified_records = []

        for record in records:
            record_crop = self._extract_crop_text(record)
            
            if self._matches(crop_text, record_crop):
                checks["crop_match_found"] = True
                
                # If a specific pest was asked, check it. Otherwise, accept the crop match.
                if pest_text:
                    record_pest = self._extract_pest_text(record)
                    if self._matches(pest_text, record_pest):
                        checks["pest_match_found"] = True
                        matching_records.append(record)
                    else:
                        continue 
                else:
                    matching_records.append(record)

        checks["relationship_supported"] = bool(matching_records)

        for record in matching_records:
            if is_verified_status(record.get("verification_status")):
                verified_records.append(record)

        if not matching_records:
            reasons.append("The available records do not establish a matching crop-pest relationship.")
        elif require_verified_evidence and not verified_records:
            reasons.append("A matching record exists, but its verification status does not establish verified evidence.")
        else:
            checks["verified_evidence_available"] = True

        evidence_records = verified_records if require_verified_evidence else matching_records
        management_records = [r for r in evidence_records if self._has_management_evidence(r)]
        checks["management_evidence_available"] = bool(management_records)

        if not management_records and not reasons:
            reasons.append("No suitable management guidance was found.")

        source_ids = self._collect_source_ids(evidence_records)
        checks["sources_available"] = bool(source_ids)

        if not source_ids and not reasons:
            reasons.append("No source IDs were found in the supporting records.")

        approved = not reasons and checks["relationship_supported"] and checks["management_evidence_available"] and checks["sources_available"]
        
        status = SafetyStatus.APPROVED if approved else SafetyStatus.VERIFICATION_REQUIRED
        if not approved and not warnings:
            warnings.append("Do not release the recommendation as verified.")

        return self._result(
            status=status, crop=crop, pest=pest, approved=approved,
            reasons=reasons, warnings=warnings, checks=checks,
            source_ids=source_ids, matching_record_ids=self._collect_record_ids(matching_records)
        )

    def _find_records(self, crop: str, pest: str) -> List[Dict[str, Any]]:
        if self.knowledge_base_loader is None:
            return []
        filters = {"crops": [crop]}
        if pest:
            filters["pests"] = [pest]
        try:
            finder = getattr(self.knowledge_base_loader, "find_records", None)
            if callable(finder):
                return finder(category="pests", filters=filters) or []
            getter = getattr(self.knowledge_base_loader, "get_records", None)
            if callable(getter):
                return getter("pests") or []
        except Exception:
            return []
        return []

    @classmethod
    def _extract_crop_text(cls, record: Dict[str, Any]) -> str:
        values = []
        for key in ("crop", "crop_name", "crop_id", "name", "aliases"):
            if record.get(key) is not None: values.append(record.get(key))
        if record.get("crops") is not None: values.append(record.get("crops"))
        return cls._normalize(values)

    @classmethod
    def _extract_pest_text(cls, record: Dict[str, Any]) -> str:
        values = []
        for key in ("pest", "pests", "target_pest", "pest_name", "disease", "pests_and_diseases_as_listed", "symptoms"):
            if record.get(key) is not None: values.append(record.get(key))
        return cls._normalize(values)

    @classmethod
    def _has_management_evidence(cls, record: Dict[str, Any]) -> bool:
        fields = ["management_methods", "management_strategies", "management_strategies_as_listed", "control_methods", "treatment", "guidance"]
        return any(cls._has_value(record.get(field)) for field in fields)

    @classmethod
    def _has_value(cls, value: Any) -> bool:
        if value is None: return False
        if isinstance(value, str): return bool(value.strip())
        if isinstance(value, (list, tuple, set)): return any(cls._has_value(item) for item in value)
        if isinstance(value, dict): return any(cls._has_value(item) for item in value.values())
        return True

    @classmethod
    def _normalize(cls, value: Any) -> str:
        if value is None: return ""
        if isinstance(value, dict): return " ".join(part for part in (cls._normalize(item) for item in value.values()) if part)
        if isinstance(value, (list, tuple, set)): return " ".join(part for part in (cls._normalize(item) for item in value) if part)
        return " ".join(str(value).strip().lower().split())

    @classmethod
    def _matches(cls, query: str, record_text: str) -> bool:
        if not query or not record_text: return False
        import re
        pattern = r"(?<!\w)" + re.escape(query) + r"(?!\w)"
        return bool(re.search(pattern, record_text))

    @staticmethod
    def _first_value(data: Dict[str, Any], keys: List[str]) -> Any:
        for key in keys:
            value = data.get(key)
            if value is not None and value != "": return value
        return None

    @staticmethod
    def _collect_source_ids(records: List[Dict[str, Any]]) -> List[str]:
        source_ids = []
        for record in records:
            values = record.get("source_ids", [])
            if not isinstance(values, (list, tuple, set)): values = [values] if values else []
            for source_id in values:
                if isinstance(source_id, str) and source_id.strip(): source_ids.append(source_id.strip())
        return list(dict.fromkeys(source_ids))

    @staticmethod
    def _collect_record_ids(records: List[Dict[str, Any]]) -> List[str]:
        record_ids = []
        for record in records:
            record_id = record.get("record_id")
            if isinstance(record_id, str) and record_id.strip(): record_ids.append(record_id.strip())
        return list(dict.fromkeys(record_ids))

    @staticmethod
    def _result(status: SafetyStatus, crop: Any = None, pest: Any = None, approved: Optional[bool] = None, reasons: Optional[List[str]] = None, warnings: Optional[List[str]] = None, checks: Optional[Dict[str, bool]] = None, source_ids: Optional[List[str]] = None, matching_record_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        is_approved = status == SafetyStatus.APPROVED if approved is None else approved
        return {
            "component": "crop_pest_validator",
            "status": status.value,
            "approved": is_approved,
            "verification_required": not is_approved,
            "crop": crop,
            "pest": pest,
            "source_ids": source_ids or [],
            "matching_record_ids": matching_record_ids or [],
            "checks": checks or {},
            "reasons": reasons or [],
            "warnings": warnings or [],
        }
