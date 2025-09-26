"""
Service for restoring PII in text from multiple filters.
This service manages the restoration process for all PII filtering layers.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

from src.models.models import PIIMapping
from src.services.regex_service import RegexService

logger = logging.getLogger(__name__)


@dataclass
class RestorationData:
    """
    Data structure to hold all restoration mappings from different filters.
    """

    regex_mappings: List[PIIMapping]
    llm_mappings: List[PIIMapping]
    ner_mappings: List[PIIMapping] = None


class RestorationService:
    """
    Service responsible for restoring PII and sensitive info from filtered text.
    """

    def __init__(self):
        """Initializes the RestorationService."""
        self.logger = logger
        self.regex_service = RegexService()

    def _generic_restore(self, text: str, mappings: List[PIIMapping]) -> str:
        """
        Generic helper function to restore placeholders from a list of mappings.
        """
        restored_text = text
        # Iterate through the list of mappings and replace each placeholder with the original value.
        for mapping in mappings:
            try:
                restored_text = restored_text.replace(
                    mapping.placeholder, mapping.original_value
                )
            except (ValueError, TypeError) as e:
                self.logger.error(
                    "Error restoring mapping %s: %s", mapping.placeholder, e
                )
                continue
        return restored_text

    def restore_all(self, filtered_text: str, restoration_data: RestorationData) -> str:
        """
        Restores PII and sensitive info from all filtering layers in reverse order.
        """
        restored_text = filtered_text
        try:
            # Restoration order: reverse of the filtering order.
            # Applied filters: 1. Regex, 2. LLM
            # Restoration: 1. LLM, 2. Regex

            # Step 1: Restore LLM placeholders (last applied filter)
            if restoration_data.llm_mappings:
                restored_text = self._generic_restore(
                    restored_text, restoration_data.llm_mappings
                )
                self.logger.info(
                    "Restored %d LLM topic instances",
                    len(restoration_data.llm_mappings),
                )

            # Step 2: Restore NER placeholders
            if restoration_data.ner_mappings:
                # NER restoration logic here...
                pass

            # Step 3: Restore Regex placeholders (first applied filter)
            if restoration_data.regex_mappings:
                # Reuse existing logic from RegexService
                restored_text = self.regex_service.restore_pii_from_mappings(
                    restored_text, restoration_data.regex_mappings
                )

            self.logger.info("Successfully restored all filters")
        except (ValueError, TypeError, RuntimeError) as e:
            self.logger.exception("A restoration error occurred: %s", e)
            return filtered_text  # Return the filtered text in case of a critical error

        return restored_text

    def create_restoration_data(
        self,
        regex_mappings: List[PIIMapping],
        llm_mappings: Optional[List[PIIMapping]] = None,
        ner_mappings: Optional[List[PIIMapping]] = None,
    ) -> RestorationData:
        """
        Helper method to create the RestorationData object.
        """
        return RestorationData(
            regex_mappings=regex_mappings or [],
            llm_mappings=llm_mappings or [],
            ner_mappings=ner_mappings or [],
        )
