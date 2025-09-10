
import logging
from typing import List, Tuple, Any, Dict

import spacy

from models.models import PIIMapping

logger = logging.getLogger(__name__)

class NERService:
    """
    Service for detecting and masking PII using Named Entity Recognition (NER).
    """
    def __init__(self):
        try:
            self.nlp = spacy.load("pt_core_news_lg")
            logger.info("SpaCy 'pt_core_news_lg' model loaded successfully.")
        except OSError:
            logger.error(
                "SpaCy model 'pt_core_news_lg' not found. "
                "Please run: python -m spacy download pt_core_news_lg"
            )
            raise

    def filter_by_ner(self, text: str) -> Tuple[str, List[PIIMapping]]:
        """
        Finds and filters PII from text using NER.

        Args:
            text (str): The input text to be filtered.

        Returns:
            Tuple[str, List[PIIMapping]]: A tuple containing:
                - The modified text with PII replaced by placeholders.
                - A list of PIIMapping objects, linking each placeholder to its
                  original value.
        """
        if not text or not isinstance(text, str):
            logger.warning("Invalid text provided for NER filtering. Returning empty.")
            return text or "", []

        doc = self.nlp(text)
        modified_text = list(text)  # Convert to list for mutable character replacement
        mappings_found: List[PIIMapping] = []
        
        # We need to track the shift in indices due to replacements
        # This approach replaces from end to start to avoid index issues
        entities_to_mask = []
        for ent in doc.ents:
            # Consider common PII entity types. You can expand or refine this list.
            # SpaCy's 'pt_core_news_lg' typically identifies:
            # PER (Pessoa), LOC (Localização), ORG (Organização), MISC (Diversos)
            # For PII, PER, LOC, ORG are most relevant.
            if ent.label_ in ["PER", "LOC", "ORG"]:
                entities_to_mask.append(ent)

        # Sort entities by their start position in reverse order
        entities_to_mask.sort(key=lambda x: x.start_char, reverse=True)

        # Count occurrences for unique placeholders
        type_counts: Dict[str, int] = {}
        for ent in entities_to_mask:
            entity_type = ent.label_
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

        current_type_counts = type_counts.copy()

        for ent in entities_to_mask:
            original_value = ent.text
            entity_type = ent.label_
            
            # Create a unique placeholder, e.g., [PER_1], [LOC_2]
            placeholder = f"[{entity_type}_{current_type_counts[entity_type]}]"
            current_type_counts[entity_type] -= 1

            mappings_found.append(
                PIIMapping(
                    placeholder=placeholder,
                    original_value=original_value,
                    type=entity_type,
                )
            )
            
            # Replace the entity in the modified_text list
            modified_text[ent.start_char : ent.end_char] = list(placeholder)

        final_text = "".join(modified_text)
        
        # The mappings list was built in reverse order, so we reverse it back.
        mappings_found.reverse()

        logger.info(
            "NER processing complete: %d PII instances filtered.", len(mappings_found)
        )
        return final_text, mappings_found

    def restore_pii_from_mappings(
        self, filtered_text: str, mappings: List[PIIMapping]
    ) -> str:
        """
        Restores the original PII into a text that contains placeholders.
        This function is generic and can be used for both regex and NER mappings.

        Args:
            filtered_text (str): The text containing PII placeholders (e.g., "[PER_1]").
            mappings (List[PIIMapping]): A list of PIIMapping objects that link each
                placeholder to its original value.

        Returns:
            str: The fully restored text with the original PII.
        """
        restored_text = filtered_text
        for mapping in mappings:
            try:
                restored_text = restored_text.replace(
                    mapping.placeholder, mapping.original_value
                )
            except (ValueError, TypeError) as e:
                logger.error(
                    "Error restoring mapping %s: %s", mapping.placeholder, e
                )
                continue

        logger.info("%d PII instances restored in the text.", len(mappings))
        return restored_text

