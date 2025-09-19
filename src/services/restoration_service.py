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
    ner_mappings: List[PIIMapping] = None  # TODO: Implementar quando NER estiver pronto
    # TODO: Adicionar outros tipos de mapeamento conforme necessário


class RestorationService:
    """
    Service responsible for restoring PII from filtered text.

    This service manages the restoration process for multiple filtering layers:
    1. Regex-based PII filtering
    2. NER-based PII filtering (TODO)
    3. Other future filtering methods (TODO)

    The restoration happens in reverse order of filtering to ensure proper reconstruction.
    """

    def __init__(self):
        """Initializes the RestorationService."""
        self.logger = logger
        self.regex_service = RegexService()

    def restore_from_regex(
        self, filtered_text: str, regex_mappings: List[PIIMapping]
    ) -> str:
        """
        Restores PII from regex filtering.

        Args:
            filtered_text (str): Text with regex placeholders
            regex_mappings (List[PIIMapping]): Mappings from regex filtering

        Returns:
            str: Text with regex PII restored
        """
        if not regex_mappings:
            self.logger.debug("No regex mappings to restore")
            return filtered_text

        restored_text = self.regex_service.restore_pii_from_mappings(
            filtered_text, regex_mappings
        )

        self.logger.info("Restored %d regex PII instances", len(regex_mappings))
        return restored_text

    def restore_from_ner(
        self, filtered_text: str, ner_mappings: Optional[List[PIIMapping]]
    ) -> str:
        """
        Restores PII from NER filtering.

        Args:
            filtered_text (str): Text with NER placeholders
            ner_mappings (Optional[List[PIIMapping]]): Mappings from NER filtering

        Returns:
            str: Text with NER PII restored
        """
        if not ner_mappings:
            self.logger.debug("No NER mappings to restore")
            return filtered_text

        # TODO: Implementar quando o filtro NER estiver pronto
        # Por enquanto, retorna o texto sem modificação
        self.logger.warning("NER restoration not implemented yet")
        return filtered_text

    def restore_all(self, filtered_text: str, restoration_data: RestorationData) -> str:
        """
        Restores PII from all filtering layers.

        The restoration happens in reverse order of filtering:
        1. Last applied filter is restored first
        2. Continue until all filters are restored

        Args:
            filtered_text (str): The fully filtered text with all placeholders
            restoration_data (RestorationData): All restoration mappings

        Returns:
            str: The fully restored text with original PII
        """
        restored_text = filtered_text

        try:
            # TODO: Quando mais filtros forem adicionados, a ordem de restauração
            # deve ser o inverso da ordem de aplicação dos filtros

            # Step 1: Restore NER (if implemented and applied last)
            if restoration_data.ner_mappings:
                restored_text = self.restore_from_ner(
                    restored_text, restoration_data.ner_mappings
                )

            # Step 2: Restore Regex (applied first, so restored last)
            restored_text = self.restore_from_regex(
                restored_text, restoration_data.regex_mappings
            )

            self.logger.info("Successfully restored all PII filters")

        except (ValueError, TypeError):
            self.logger.exception("Error during PII restoration")
            return filtered_text

        return restored_text

    def create_restoration_data(
        self,
        regex_mappings: List[PIIMapping],
        ner_mappings: Optional[List[PIIMapping]] = None,
    ) -> RestorationData:
        """
        Helper method to create RestorationData object.

        Args:
            regex_mappings (List[PIIMapping]): Mappings from regex filtering
            ner_mappings (Optional[List[PIIMapping]]): Mappings from NER filtering

        Returns:
            RestorationData: Object containing all restoration mappings
        """
        return RestorationData(
            regex_mappings=regex_mappings, ner_mappings=ner_mappings or []
        )
