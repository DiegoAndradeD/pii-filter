"""
Service for restoring PII in text from multiple filters.
This service manages the restoration process for all PII filtering layers.
"""

import logging
import re
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
    ner_mappings: List[PIIMapping]
    llm_mappings: List[PIIMapping]


class RestorationService:
    """
    Service responsible for restoring PII and sensitive info from filtered text.

    Restoration Order (reverse of filtering):
    1. Regex Filter   -> Applied FIRST  -> Restored LAST
    2. NER Filter     -> Applied SECOND -> Restored SECOND
    3. LLM Filter     -> Applied LAST   -> Restored FIRST
    """

    def __init__(self):
        """Initializes the RestorationService."""
        self.logger = logger
        self.regex_service = RegexService()

    def _generic_restore(self, text: str, mappings: List[PIIMapping]) -> str:
        """
        Generic helper function to restore placeholders from a list of mappings.
        Processes mappings in reverse order to handle potential nested placeholders.
        """
        if not mappings:
            return text

        restored_text = text
        sorted_mappings = sorted(
            mappings, key=lambda m: m.span[0] if m.span else 0, reverse=True
        )

        for mapping in sorted_mappings:
            try:
                if mapping.placeholder not in restored_text:
                    self.logger.warning(
                        "Placeholder %s not found in text during restoration",
                        mapping.placeholder,
                    )
                    continue

                restored_text = restored_text.replace(
                    mapping.placeholder, mapping.original_value
                )
            except (ValueError, TypeError) as e:
                self.logger.error(
                    "Error restoring mapping %s: %s", mapping.placeholder, e
                )
                continue

        return restored_text

    def _check_restoration_integrity(self, text: str) -> bool:
        """
        Checks if there are still unrestored placeholders in the text.
        Returns True if the text is intact (without placeholders), False otherwise.
        """
        placeholder_pattern = re.compile(r"\[[A-Z_]+_\d+\]")
        remaining_placeholders = placeholder_pattern.findall(text)

        if remaining_placeholders:
            self.logger.warning(
                "Restoration incomplete. Remaining placeholders: %s",
                remaining_placeholders,
            )
            return False

        return True

    def restore_all(self, filtered_text: str, restoration_data: RestorationData) -> str:
        """
        Restores PII and sensitive info from all filtering layers in reverse order.

        Args:
            filtered_text: Text with all placeholders applied
            restoration_data: Object containing all mappings from the 3 filters

        Returns:
            Fully restored text with original PII values
        """
        if not filtered_text:
            self.logger.warning("Empty text provided for restoration")
            return filtered_text

        restored_text = filtered_text

        try:
            if restoration_data.llm_mappings:
                restored_text = self._generic_restore(
                    restored_text, restoration_data.llm_mappings
                )
                self.logger.info(
                    "Restored %d LLM topic instances",
                    len(restoration_data.llm_mappings),
                )

            if restoration_data.ner_mappings:
                restored_text = self._generic_restore(
                    restored_text, restoration_data.ner_mappings
                )
                self.logger.info(
                    "Restored %d NER PII instances",
                    len(restoration_data.ner_mappings),
                )

            if restoration_data.regex_mappings:
                restored_text = self.regex_service.restore_pii_from_mappings(
                    restored_text, restoration_data.regex_mappings
                )

            if not self._check_restoration_integrity(restored_text):
                self.logger.error(
                    "Restoration integrity check failed. Some placeholders remain."
                )

            self.logger.info("Successfully restored all filters")

        except (ValueError, TypeError, RuntimeError) as e:
            self.logger.exception("A restoration error occurred: %s", e)
            return filtered_text

        return restored_text

    def create_restoration_data(
        self,
        regex_mappings: Optional[List[PIIMapping]] = None,
        ner_mappings: Optional[List[PIIMapping]] = None,
        llm_mappings: Optional[List[PIIMapping]] = None,
    ) -> RestorationData:
        """
        Helper method to create the RestorationData object.

        Args:
            regex_mappings: Mappings from the Regex filter
            ner_mappings: Mappings from the NER filter
            llm_mappings: Mappings from the LLM filter

        Returns:
            RestorationData object with all mappings
        """
        return RestorationData(
            regex_mappings=regex_mappings or [],
            ner_mappings=ner_mappings or [],
            llm_mappings=llm_mappings or [],
        )
