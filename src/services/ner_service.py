"""
Service for filtering and restoring PII in text using Named Entity Recognition (NER).
"""

import logging
from typing import Dict, List, Tuple, Any
import spacy

from src.core.constants import (
    NER_ENTITY_TYPE_MAPPING,
    NER_FALSE_POSITIVES,
    NER_PROFESSION_PATTERNS,
)
from src.models.models import PIIMapping

logger = logging.getLogger(__name__)


class NERService:
    """
    Service to find, filter, and restore PII from text using Named Entity Recognition.

    This class encapsulates the logic for:
        1. Finding professions (via EntityRuler) and named entities (people, organizations, places) using spaCy.
        2. Converting entities into PII mappings with placeholders.
        3. Filtering text by replacing entities with placeholders.
        4. Restoring the original text from the filtered text and the map.
    """

    _ENTITY_TYPE_MAPPING: Dict[str, str] = NER_ENTITY_TYPE_MAPPING
    _FALSE_POSITIVES: set = NER_FALSE_POSITIVES
    _PROFESSION_PATTERNS: List[Dict[str, Any]] = NER_PROFESSION_PATTERNS

    def __init__(self, model_name: str = "pt_core_news_lg"):
        """
        NER Service Initialization.

        Args:
            model_name: Name of the spaCy model in Portuguese.
            "pt_core_news_lg" is recommended for better resolution.
        """
        self.logger = logger
        self.model_name = model_name
        self.nlp = None

        try:
            self.nlp = spacy.load(model_name)
            self.logger.info("Loaded spaCy model: %s", model_name)

            if "entity_ruler" not in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe("entity_ruler", before="ner")
                ruler.add_patterns(self._PROFESSION_PATTERNS)
                self.logger.info(
                    "Added EntityRuler with %d profession patterns.",
                    len(self._PROFESSION_PATTERNS),
                )
            else:
                self.logger.warning("EntityRuler already exists in pipeline.")

        except OSError as e:
            self.logger.critical(
                "Could not load spaCy model '%s'. NER Service will be disabled. Error: %s",
                model_name,
                e,
            )
            raise RuntimeError(f"Failed to load spaCy model '{model_name}'.") from e

        self.logger.info(
            "NER Service initialized with pipeline: %s", self.nlp.pipe_names
        )

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts named entities from text using spaCy.

        Args:
            text: Input text to parse
        Returns:
            List of entity dictionaries with type, value, and span information
        """
        if not self.nlp:
            self.logger.warning("NER NLP model is not loaded. Skipping extraction.")
            return []

        entities = []

        try:
            doc = self.nlp(text)

            for ent in doc.ents:
                pii_type = self._ENTITY_TYPE_MAPPING.get(
                    ent.label_, f"ENTIDADE_{ent.label_}"
                )

                ent_text = ent.text.strip()
                ent_text_lower = ent_text.lower()

                if len(ent_text) < 3:
                    continue

                if ent_text.isdigit():
                    continue

                if ent_text_lower in self._FALSE_POSITIVES:
                    continue

                if ":" in ent_text:
                    self.logger.debug(
                        "Skipping entity '%s' as it contains a colon (likely a label).",
                        ent_text,
                    )
                    continue

                if (
                    "[" in ent_text
                    or "]" in ent_text
                    or "_" in ent_text
                    or (ent_text.isupper() and len(ent_text) > 4)
                ):
                    continue

                if any(
                    c.isdigit() for c in ent_text
                ) and not self._is_valid_name_with_numbers(ent_text):
                    if pii_type != "LEI" and pii_type != "EVENTO":
                        continue

                entities.append(
                    {
                        "type": pii_type,
                        "value": ent_text,
                        "span": (ent.start_char, ent.end_char),
                        "spacy_label": ent.label_,
                    }
                )

                self.logger.debug(
                    "Entity detected: '%s' (%s -> %s) at span (%s, %s)",
                    ent.text,
                    ent.label_,
                    pii_type,
                    ent.start_char,
                    ent.end_char,
                )

        except (ValueError, TypeError) as e:
            self.logger.error("Error extracting entities: %s", e, exc_info=True)

        return entities

    def _extract_entities_avoiding_placeholders(
        self, text: str, placeholders: List[str]
    ) -> List[Dict[str, Any]]:
        """Extracts entities while avoiding areas that are already placeholders."""

        placeholder_spans = []
        for placeholder in placeholders:
            start = 0
            while True:
                pos = text.find(placeholder, start)
                if pos == -1:
                    break
                placeholder_spans.append((pos, pos + len(placeholder)))
                start = pos + 1

        all_entities = self._extract_entities(text)

        filtered_entities = []
        for entity in all_entities:
            entity_start, entity_end = entity["span"]

            overlaps = False
            for ph_start, ph_end in placeholder_spans:
                if entity_start < ph_end and entity_end > ph_start:
                    overlaps = True
                    break

            if not overlaps:
                filtered_entities.append(entity)
            else:
                self.logger.debug(
                    "Skipping entity '%s' as it overlaps with an existing placeholder.",
                    entity["value"],
                )

        return filtered_entities

    def _is_valid_name_with_numbers(self, text: str) -> bool:
        """Check if the text containing numbers is a valid name (e.g., 'John II')."""
        text_clean = text.lower().strip()
        valid_patterns = [" ii", " iii", " iv", " v", " jr", " sr", " filho", " neto"]
        return any(text_clean.endswith(pattern) for pattern in valid_patterns)

    def _filter_overlapping_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filters overlapping entities, keeping the longest ones.
        If EntityRuler and NER find the same thing, this function
        helps resolve the conflict.
        """
        if not entities:
            return []

        entities.sort(key=lambda x: (x["span"][0], -(x["span"][1] - x["span"][0])))

        filtered_entities = []
        last_end = -1

        for entity in entities:
            start, end = entity["span"]
            if start >= last_end:
                filtered_entities.append(entity)
                last_end = end

        return filtered_entities

    def filter_by_ner(
        self,
        text: str,
        existing_placeholders: List[str] = None,
    ) -> Tuple[str, List[PIIMapping]]:
        """
        Filters PII from text using Named Entity Recognition.

        Args:
            text: Input text to filter.
            existing_placeholders: List of existing placeholders to avoid conflicts (e.g., from the Regex filter).

        Returns:
            Tuple of (filtered_text, list_of_pii_mappings)
        """
        if not text.strip() or not self.nlp:
            return text, []

        if existing_placeholders:
            entities = self._extract_entities_avoiding_placeholders(
                text, existing_placeholders
            )
        else:
            entities = self._extract_entities(text)

        entities = self._filter_overlapping_entities(entities)

        if not entities:
            self.logger.info("No new entities detected by NER")
            return text, []

        type_counts: Dict[str, int] = {}
        for entity in entities:
            pii_type = entity["type"]
            type_counts[pii_type] = type_counts.get(pii_type, 0) + 1

        current_counts = type_counts.copy()
        entities.sort(key=lambda x: x["span"][0], reverse=True)
        filtered_text = text
        pii_mappings = []

        for entity in entities:
            pii_type = entity["type"]
            original_value = entity["value"]
            start, end = entity["span"]

            count = current_counts[pii_type]
            current_counts[pii_type] -= 1
            placeholder = f"[{pii_type}_{count}]"
            filtered_text = filtered_text[:start] + placeholder + filtered_text[end:]

            pii_mapping = PIIMapping(
                placeholder=placeholder,
                original_value=original_value,
                type=pii_type,
                span=(start, start + len(placeholder)),
            )
            pii_mappings.append(pii_mapping)

            self.logger.debug("Replaced '%s' with '%s'", original_value, placeholder)

        pii_mappings.reverse()

        self.logger.info(
            "NER filtering completed. Found %d entities", len(pii_mappings)
        )

        return filtered_text, pii_mappings

    def restore_from_ner(
        self, filtered_text: str, pii_mappings: List[PIIMapping]
    ) -> str:
        """
        Restores the original text from the filtered text using PII mappings.

        Args:
            filtered_text: Text with placeholders
            pii_mappings: List of PII mappings to restore

        Returns:
            Original text with restored PII
        """
        if not pii_mappings:
            return filtered_text

        restored_text = filtered_text
        pii_mappings.sort(key=lambda m: len(m.placeholder), reverse=True)

        for mapping in pii_mappings:
            restored_text = restored_text.replace(
                mapping.placeholder, mapping.original_value
            )
            self.logger.debug(
                "Restored '%s' to '%s'", mapping.placeholder, mapping.original_value
            )

        return restored_text

    def get_supported_entity_types(self) -> List[str]:
        """
        Retrieves a list of supported PII entity types.

        Returns:
            List of PII type names supported by this service
        """
        return list(set(self._ENTITY_TYPE_MAPPING.values()))
