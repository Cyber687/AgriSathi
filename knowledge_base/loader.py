"""
AgriSathi - Knowledge Base Loader

Loads and searches agricultural information stored in JSON files.

Supported knowledge-base files:
    crops.json
    fertilizers.json
    pests.json
    irrigation.json
    sources.json

Responsibilities:
    - Load JSON files safely.
    - Validate the basic structure of loaded data.
    - Search agricultural records by crop, pest, symptoms,
      location, and other fields.
    - Retrieve source metadata.
    - Return records compatible with the AgriSathi Rule Engine.

This module does not independently verify the scientific
accuracy of agricultural recommendations.
"""

import json
from pathlib import Path
from typing import Any, Optional


class KnowledgeBaseLoader:
    """
    Loads and searches the AgriSathi agricultural knowledge base.
    """

    DEFAULT_FILES = {
        "crops": "crops.json",
        "fertilizers": "fertilizers.json",
        "pests": "pests.json",
        "irrigation": "irrigation.json",
        "sources": "sources.json",
    }

    def __init__(
        self,
        base_dir: Optional[str] = None,
        auto_load: bool = True,
    ):
        """
        Args:
            base_dir:
                Directory containing the JSON knowledge-base files.
                Defaults to the directory containing this file.

            auto_load:
                Automatically load JSON files during initialization.
        """

        if base_dir is None:
            self.base_dir = Path(__file__).resolve().parent
        else:
            self.base_dir = Path(base_dir).expanduser().resolve()

        self.data: dict[str, list[dict[str, Any]]] = {
            category: []
            for category in self.DEFAULT_FILES
        }

        self.load_errors: dict[str, str] = {}
        self.loaded_files: list[str] = []

        if auto_load:
            self.load_all()

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    @staticmethod
    def _normalize(value: Any) -> str:
        """
        Normalize values for case-insensitive searching.

        Handles strings, numbers, lists, and dictionaries.
        """

        if value is None:
            return ""

        if isinstance(value, str):
            return " ".join(value.casefold().split())

        if isinstance(value, (int, float)):
            return str(value).casefold()

        if isinstance(value, list):
            return " ".join(
                KnowledgeBaseLoader._normalize(item)
                for item in value
            )

        if isinstance(value, dict):
            return " ".join(
                KnowledgeBaseLoader._normalize(item)
                for item in value.values()
            )

        return str(value).casefold()

    @staticmethod
    def _matches(value: Any, query: str) -> bool:
        """Check whether a query appears in a value."""

        normalized_value = KnowledgeBaseLoader._normalize(value)
        normalized_query = KnowledgeBaseLoader._normalize(query)

        if not normalized_query:
            return True

        return normalized_query in normalized_value

    @staticmethod
    def _as_list(value: Any) -> list:
        """Convert a value into a list for filtering."""

        if value is None:
            return []

        if isinstance(value, list):
            return value

        return [value]

    # --------------------------------------------------
    # Load individual JSON files
    # --------------------------------------------------

    def load_category(
        self,
        category: str,
        filename: Optional[str] = None,
    ) -> dict:
        """
        Load a single knowledge-base category.

        Args:
            category:
                crops, fertilizers, pests, irrigation, or sources.

            filename:
                Optional custom JSON filename.

        Returns:
            A status dictionary describing the loading operation.
        """

        category = category.strip().lower()

        if category not in self.DEFAULT_FILES:
            return {
                "status": "error",
                "category": category,
                "message": "Unknown knowledge-base category.",
                "count": 0,
            }

        selected_filename = (
            filename or self.DEFAULT_FILES[category]
        )

        file_path = (self.base_dir / selected_filename).resolve()

        # Prevent custom filenames from escaping the KB directory.
        if not file_path.is_relative_to(self.base_dir):
            message = "The requested file must be inside the knowledge-base directory."

            self.load_errors[category] = message

            return {
                "status": "error",
                "category": category,
                "message": message,
                "count": 0,
            }

        if not file_path.is_file():
            message = f"Knowledge-base file not found: {selected_filename}"

            self.data[category] = []
            self.load_errors[category] = message

            return {
                "status": "error",
                "category": category,
                "message": message,
                "count": 0,
            }

        try:
            with file_path.open("r", encoding="utf-8-sig") as file:
                raw_data = json.load(file)

        except json.JSONDecodeError as exc:
            message = (
                f"Invalid JSON in {selected_filename}: "
                f"line {exc.lineno}, column {exc.colno}."
            )

            self.data[category] = []
            self.load_errors[category] = message

            return {
                "status": "error",
                "category": category,
                "message": message,
                "count": 0,
            }

        except OSError as exc:
            message = f"Unable to read {selected_filename}: {exc}"

            self.data[category] = []
            self.load_errors[category] = message

            return {
                "status": "error",
                "category": category,
                "message": message,
                "count": 0,
            }

        # Accept either a JSON array or an object containing
        # a "records" array.
        if isinstance(raw_data, list):
            records = raw_data

        elif isinstance(raw_data, dict):
            records = raw_data.get("records")

            if records is None:
                message = (
                    f"{selected_filename} must contain a JSON array "
                    "or an object with a 'records' array."
                )

                self.data[category] = []
                self.load_errors[category] = message

                return {
                    "status": "error",
                    "category": category,
                    "message": message,
                    "count": 0,
                }

        else:
            message = (
                f"{selected_filename} must contain a JSON array "
                "or an object with a 'records' array."
            )

            self.data[category] = []
            self.load_errors[category] = message

            return {
                "status": "error",
                "category": category,
                "message": message,
                "count": 0,
            }

        if not isinstance(records, list):
            message = (
                f"The records field in {selected_filename} "
                "must be a JSON array."
            )

            self.data[category] = []
            self.load_errors[category] = message

            return {
                "status": "error",
                "category": category,
                "message": message,
                "count": 0,
            }

        # Keep dictionary records only. Do not silently convert
        # malformed entries into agricultural recommendations.
        invalid_count = sum(
            1 for record in records
            if not isinstance(record, dict)
        )

        valid_records = [
            record for record in records
            if isinstance(record, dict)
        ]

        self.data[category] = valid_records

        if invalid_count:
            self.load_errors[category] = (
                f"{invalid_count} non-object record(s) were skipped."
            )
        else:
            self.load_errors.pop(category, None)

        if selected_filename not in self.loaded_files:
            self.loaded_files.append(selected_filename)

        return {
            "status": "success",
            "category": category,
            "filename": selected_filename,
            "count": len(valid_records),
            "skipped_records": invalid_count,
            "message": "Knowledge-base file loaded.",
        }

    # --------------------------------------------------
    # Load all knowledge-base files
    # --------------------------------------------------

    def load_all(self) -> dict:
        """
        Load every configured knowledge-base file.
        """

        results = {}

        for category, filename in self.DEFAULT_FILES.items():
            results[category] = self.load_category(
                category=category,
                filename=filename,
            )

        successful = sum(
            1 for result in results.values()
            if result["status"] == "success"
        )

        return {
            "status": (
                "success"
                if successful == len(self.DEFAULT_FILES)
                else "partial"
                if successful > 0
                else "error"
            ),
            "loaded_categories": successful,
            "total_categories": len(self.DEFAULT_FILES),
            "results": results,
            "errors": self.load_errors.copy(),
        }

    # --------------------------------------------------
    # Get all records for a category
    # --------------------------------------------------

    def get_records(
        self,
        category: str,
    ) -> list[dict[str, Any]]:
        """
        Return a copy of all records for a category.

        This method is compatible with the existing Rule Engine.
        """

        category = category.strip().lower()

        if category not in self.data:
            return []

        return [
            record.copy()
            for record in self.data[category]
        ]

    # --------------------------------------------------
    # Search records
    # --------------------------------------------------

    def find_records(
        self,
        category: str,
        filters: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """
        Search records using the filters expected by the Rule Engine.

        Supported filters:
            crops
            pests
            symptoms
            location
            state
            district
            market
            language
            keywords

        Additional record fields can be searched by using
        the "keywords" filter.
        """

        category = category.strip().lower()

        if category not in self.data:
            return []

        records = self.data[category]

        if not filters:
            return [
                record.copy()
                for record in records
            ]

        filters = {
            str(key).strip().lower(): value
            for key, value in filters.items()
        }

        results = []

        for record in records:
            matched = True

            # Match crop names and aliases.
            crop_filters = self._as_list(
                filters.get("crops")
            )

            if crop_filters:
                crop_value = record.get(
                    "crop",
                    record.get("crops", [])
                )

                aliases = record.get("aliases", [])

                searchable_crops = [
                    crop_value,
                    aliases,
                ]

                if not any(
                    self._matches(searchable_crops, crop)
                    for crop in crop_filters
                ):
                    matched = False

            # Match pest names and aliases.
            pest_filters = self._as_list(
                filters.get("pests")
            )

            if matched and pest_filters:
                pest_value = record.get(
                    "pest",
                    record.get("pests", [])
                )

                aliases = record.get("aliases", [])

                searchable_pests = [
                    pest_value,
                    aliases,
                ]

                if not any(
                    self._matches(searchable_pests, pest)
                    for pest in pest_filters
                ):
                    matched = False

            # Match reported symptoms.
            symptom_filters = self._as_list(
                filters.get("symptoms")
            )

            if matched and symptom_filters:
                record_symptoms = record.get(
                    "symptoms",
                    record.get("symptom", [])
                )

                if not all(
                    self._matches(record_symptoms, symptom)
                    for symptom in symptom_filters
                ):
                    matched = False

            # Optional location-related filters.
            for field in ("location", "state", "district", "market"):
                if not matched:
                    break

                requested_value = filters.get(field)

                if requested_value:
                    record_value = record.get(
                        field,
                        record.get("locations", [])
                    )

                    if not self._matches(
                        record_value,
                        str(requested_value)
                    ):
                        matched = False

            # Optional language filter.
            if matched and filters.get("language"):
                requested_language = filters["language"]

                record_language = record.get(
                    "language",
                    record.get("languages", [])
                )

                if not self._matches(
                    record_language,
                    str(requested_language)
                ):
                    matched = False

            # General keyword search across record fields.
            keyword_filters = self._as_list(
                filters.get("keywords")
            )

            if matched and keyword_filters:
                searchable_record = self._normalize(record)

                if not all(
                    self._matches(
                        searchable_record,
                        str(keyword)
                    )
                    for keyword in keyword_filters
                ):
                    matched = False

            if matched:
                results.append(record.copy())

        return results

    # --------------------------------------------------
    # Retrieve source information
    # --------------------------------------------------

    def get_source(
        self,
        source_id: str,
    ) -> Optional[dict[str, Any]]:
        """
        Find a source by its ID.

        Supported ID fields:
            source_id
            id
        """

        if not source_id:
            return None

        for record in self.data["sources"]:
            record_id = record.get(
                "source_id",
                record.get("id")
            )

            if str(record_id) == str(source_id):
                return record.copy()

        return None

    def get_sources_for_record(
        self,
        record: dict,
    ) -> list[dict[str, Any]]:
        """
        Resolve source IDs attached to a knowledge-base record.

        Supported fields:
            source_ids
            information_source_ids
        """

        source_ids = record.get(
            "source_ids",
            record.get("information_source_ids", [])
        )

        if not isinstance(source_ids, list):
            source_ids = [source_ids] if source_ids else []

        resolved_sources = []

        for source_id in source_ids:
            source = self.get_source(str(source_id))

            if source is not None:
                resolved_sources.append(source)

        return resolved_sources

    # --------------------------------------------------
    # Knowledge-base status
    # --------------------------------------------------

    def get_status(self) -> dict:
        """
        Return loading status and record counts.

        Useful for application startup diagnostics.
        """

        record_counts = {
            category: len(records)
            for category, records in self.data.items()
        }

        return {
            "base_directory": str(self.base_dir),
            "loaded_files": self.loaded_files.copy(),
            "record_counts": record_counts,
            "load_errors": self.load_errors.copy(),
        }


# ------------------------------------------------------
# Convenience function
# ------------------------------------------------------

def load_knowledge_base(
    base_dir: Optional[str] = None,
) -> KnowledgeBaseLoader:
    """
    Create a loader and load all configured JSON files.
    """

    return KnowledgeBaseLoader(
        base_dir=base_dir,
        auto_load=True,
    )