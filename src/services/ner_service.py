"""
Service for filtering and restoring PII in text using Named Entity Recognition (NER).
"""

import logging
from typing import Dict, List, Tuple, Any
import spacy
from spacy.lang.pt import Portuguese

from src.models.models import PIIMapping

logger = logging.getLogger(__name__)


class NERService:
    """
    Service to find, filter, and restore PII from text using Named Entity Recognition.

    This class encapsulates the logic for:
    1. Finding named entities (persons, organizations, locations) using spaCy.
    2. Converting entities to PII mappings with placeholders.
    3. Filtering text by replacing entities with placeholders.
    4. Restoring the original text from the filtered text and the map.
    """

    # Mapping from spaCy entity labels to our PII types
    _ENTITY_TYPE_MAPPING: Dict[str, str] = {
        "PERSON": "NOME_PESSOA",
        "PER": "NOME_PESSOA",  # Alternative label
        "ORG": "ORGANIZACAO",
        "GPE": "LOCAL",  # Geopolitical entities (cities, countries)
        "LOC": "LOCAL",  # Locations
        "FAC": "LOCAL",  # Facilities
        "EVENT": "EVENTO",  # Events
        "WORK_OF_ART": "OBRA_ARTE",
        "LAW": "LEI",
        "LANGUAGE": "IDIOMA",
    }

    def __init__(self, model_name: str = "pt_core_news_sm"):
        """
        Initializes the NER Service.

        Args:
            model_name: Name of the spaCy Portuguese model to load.
        """
        self.logger = logger
        self.model_name = model_name

        try:
            # Try to load the Portuguese model
            self.nlp = spacy.load(model_name)
            self.logger.info("Loaded spaCy model: %s", model_name)
        except OSError:
            # Fallback to blank Portuguese model if trained model not available
            self.logger.warning(
                "Could not load %s, using blank Portuguese model", model_name
            )
            self.nlp = Portuguese()

            # Add basic NER component if available
            if "ner" not in self.nlp.pipe_names:
                try:
                    # Try to add a basic NER component
                    self.nlp.add_pipe("ner")
                except Exception as e:
                    self.logger.error("Could not add NER component: %s", e)

        self.logger.info(
            "NER Service initialized with pipeline: %s", self.nlp.pipe_names
        )

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text using spaCy.

        Args:
            text: Input text to analyze

        Returns:
            List of entity dictionaries with type, value, and span information
        """
        entities = []

        try:
            # Process text with spaCy
            doc = self.nlp(text)

            for ent in doc.ents:
                # Map spaCy entity label to our PII type
                pii_type = self._ENTITY_TYPE_MAPPING.get(
                    ent.label_, f"ENTIDADE_{ent.label_}"
                )

                # Filter out very short entities that are likely false positives
                if len(ent.text.strip()) < 3:
                    continue

                # Skip entities that are just numbers or punctuation
                if ent.text.strip().isdigit() or not any(c.isalpha() for c in ent.text):
                    continue

                # Skip common false positives and document terms
                text_lower = ent.text.lower().strip()
                false_positives = {
                    "oi",
                    "olá",
                    "ei",
                    "cpf",
                    "cnpj",
                    "email",
                    "telefone",
                    "rg",
                    "cep",
                    "use",
                    "clt",
                    "cargo",
                    "setor",
                    "cnh",
                    "dados",
                    "nome",
                    "completo",
                    "matrícula",
                    "nascido",
                    "funcionário",
                    "endereço",
                    "salário",
                    "histórico",
                    "login",
                    "rede",
                    "acesso",
                    "ip",
                    "gestão",
                    "assinatura",
                    "artigo",
                    "lei",
                    "código",
                    "sistema",
                    "empresa",
                    "trabalho",
                    "operações",
                    "manutenção",
                    "técnico",
                    "jr",
                    "senior",
                    "pleno",
                    "analista",
                    "coordenador",
                    "diretor",
                    "gerente",
                    "supervisor",
                }
                if text_lower in false_positives:
                    continue

                # Skip entities that look like placeholders or codes
                if (
                    "[" in ent.text
                    or "]" in ent.text
                    or "_" in ent.text
                    or ent.text.isupper()
                    or ent.text.isdigit()
                ):
                    continue

                # Skip single words that are too generic or common
                if len(ent.text.strip()) <= 2 or text_lower in {
                    "de",
                    "da",
                    "do",
                    "em",
                    "na",
                    "no",
                    "e",
                    "é",
                    "meu",
                    "minha",
                    "sua",
                    "seu",
                    "para",
                    "com",
                    "por",
                    "sem",
                    "uma",
                    "um",
                    "das",
                    "dos",
                    "pela",
                    "pelo",
                }:
                    continue

                # Skip entities that contain numbers (likely codes, IDs, etc.)
                if any(
                    c.isdigit() for c in ent.text
                ) and not self._is_valid_name_with_numbers(ent.text):
                    continue

                # Additional validation based on entity type
                if not self._is_valid_entity_for_type(ent.text, ent.label_):
                    continue

                entities.append(
                    {
                        "type": pii_type,
                        "value": ent.text,
                        "span": (ent.start_char, ent.end_char),
                        "confidence": getattr(
                            ent, "_.confidence", 1.0
                        ),  # Default confidence
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

        except Exception as e:
            self.logger.error("Error extracting entities: %s", e)

        return entities

    def _extract_entities_avoiding_placeholders(
        self, text: str, placeholders: List[str]
    ) -> List[Dict[str, Any]]:
        """Extract entities while avoiding areas near existing placeholders."""
        # Find all placeholder positions
        placeholder_spans = []
        for placeholder in placeholders:
            start = 0
            while True:
                pos = text.find(placeholder, start)
                if pos == -1:
                    break
                placeholder_spans.append((pos, pos + len(placeholder)))
                start = pos + 1

        # Extract all entities normally
        all_entities = self._extract_entities(text)

        # Filter out entities that are too close to placeholders
        filtered_entities = []
        for entity in all_entities:
            entity_start, entity_end = entity["span"]

            # Check if entity overlaps or is too close to any placeholder
            too_close = False
            for ph_start, ph_end in placeholder_spans:
                # Add buffer of 10 characters around placeholders
                buffer = 10
                if entity_start <= ph_end + buffer and entity_end >= ph_start - buffer:
                    too_close = True
                    break

            if not too_close:
                filtered_entities.append(entity)

        return filtered_entities

    def _is_valid_name_with_numbers(self, text: str) -> bool:
        """Check if text with numbers is a valid name (like 'João II' or 'São Paulo')."""
        # Allow Roman numerals and ordinal numbers in names
        text_clean = text.lower().strip()
        valid_patterns = ["ii", "iii", "iv", "jr", "sr", "filho", "neto"]
        return any(pattern in text_clean for pattern in valid_patterns)

    def _is_valid_entity_for_type(self, text: str, label: str) -> bool:
        """Validate if the detected entity makes sense for its detected type."""
        text_clean = text.lower().strip()

        # Common job title and descriptive patterns to exclude
        job_patterns = [
            "cargo",
            "função",
            "técnico",
            "analista",
            "gerente",
            "coordenador",
            "assistente",
            "supervisor",
            "estagiário",
            "manutenção",
            "júnior",
            "jr",
            "senior",
            "sr",
            "pleno",
        ]

        # For person names, require at least one uppercase letter and reasonable length
        if label in ["PERSON", "PER"]:
            if len(text.split()) < 2:  # Names should have at least first + last name
                return False
            if not any(c.isupper() for c in text):  # Names should be capitalized
                return False
            # Skip obvious non-names
            if any(pattern in text_clean for pattern in job_patterns):
                return False

        # For organizations, require reasonable length and capitalization
        elif label == "ORG":
            if len(text) < 3:
                return False
            if text_clean in ["cnh", "cpf", "rg"]:  # These are not organizations
                return False
            # Skip job descriptions
            if any(pattern in text_clean for pattern in job_patterns):
                return False

        # For locations, validate they look like place names
        elif label in ["GPE", "LOC", "FAC"]:
            if len(text) < 3:
                return False
            # Skip obvious non-locations
            if text_clean in ["use", "cargo", "setor", "matrícula"]:
                return False
            if any(pattern in text_clean for pattern in job_patterns):
                return False

        # For miscellaneous entities, be very strict
        elif label == "MISC":
            if len(text) < 4:  # Require longer text for misc entities
                return False
            # Skip job descriptions and common administrative terms
            if any(pattern in text_clean for pattern in job_patterns):
                return False
            # Skip common administrative words
            admin_words = ["setor", "operações", "artigo", "disciplinar", "matrícula"]
            if any(word in text_clean for word in admin_words):
                return False

        return True

    def _filter_overlapping_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter out overlapping entities, keeping the longer ones.

        Args:
            entities: List of entity dictionaries

        Returns:
            Filtered list without overlapping entities
        """
        if not entities:
            return []

        # Sort by start position, then by length (longest first)
        entities.sort(key=lambda x: (x["span"][0], -(x["span"][1] - x["span"][0])))

        filtered_entities = []
        last_end = -1

        for entity in entities:
            start, end = entity["span"]

            # If this entity doesn't overlap with the previous one, keep it
            if start >= last_end:
                filtered_entities.append(entity)
                last_end = end

        return filtered_entities

    def filter_by_ner(
        self,
        text: str,
        confidence_threshold: float = 0.5,
        existing_placeholders: List[str] = None,
    ) -> Tuple[str, List[PIIMapping]]:
        """
        Filter PII from text using Named Entity Recognition.

        Args:
            text: Input text to filter
            confidence_threshold: Minimum confidence score for entities (0.0 to 1.0)
            existing_placeholders: List of existing placeholders to avoid conflicts

        Returns:
            Tuple of (filtered_text, list_of_pii_mappings)
        """
        if not text.strip():
            return text, []

        # Skip entities that are near existing placeholders (likely already detected by regex)
        if existing_placeholders:
            entities = self._extract_entities_avoiding_placeholders(
                text, existing_placeholders
            )
        else:
            entities = self._extract_entities(text)

        # Filter by confidence threshold
        entities = [
            e for e in entities if e.get("confidence", 1.0) >= confidence_threshold
        ]

        # Remove overlapping entities
        entities = self._filter_overlapping_entities(entities)

        if not entities:
            self.logger.info("No entities detected by NER")
            return text, []

        # Sort entities by span start position (reverse order for replacement)
        entities.sort(key=lambda x: x["span"][0], reverse=True)

        filtered_text = text
        pii_mappings = []

        # Replace entities with placeholders (from end to start to preserve indices)
        for i, entity in enumerate(entities):
            pii_type = entity["type"]
            original_value = entity["value"]
            start, end = entity["span"]

            # Generate placeholder
            placeholder = f"[{pii_type}_{i+1}]"

            # Replace in text
            filtered_text = filtered_text[:start] + placeholder + filtered_text[end:]

            # Create PII mapping
            pii_mapping = PIIMapping(
                placeholder=placeholder,
                original_value=original_value,
                type=pii_type,
                span=(start, end),
            )
            pii_mappings.append(pii_mapping)

            self.logger.debug("Replaced '%s' with '%s'", original_value, placeholder)

        # Reverse the list to maintain original order
        pii_mappings.reverse()

        self.logger.info(
            "NER filtering completed. Found %d entities", len(pii_mappings)
        )

        return filtered_text, pii_mappings

    def restore_from_ner(
        self, filtered_text: str, pii_mappings: List[PIIMapping]
    ) -> str:
        """
        Restore original text from filtered text using PII mappings.

        Args:
            filtered_text: Text with placeholders
            pii_mappings: List of PII mappings to restore

        Returns:
            Original text with PII restored
        """
        if not pii_mappings:
            return filtered_text

        restored_text = filtered_text

        # Sort mappings by placeholder to ensure consistent replacement
        for mapping in sorted(pii_mappings, key=lambda x: x.placeholder):
            restored_text = restored_text.replace(
                mapping.placeholder, mapping.original_value
            )
            self.logger.debug(
                "Restored '%s' to '%s'", mapping.placeholder, mapping.original_value
            )

        return restored_text

    def get_supported_entity_types(self) -> List[str]:
        """
        Get list of supported entity types.

        Returns:
            List of PII type names supported by this service
        """
        return list(set(self._ENTITY_TYPE_MAPPING.values()))
