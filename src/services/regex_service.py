"""
Service for filtering and restoring PII in text by regex patterns.
"""

import logging
from typing import Dict, List, Tuple, Any

from src.core.constants import PII_PATTERNS
from src.models.models import PIIMapping
from src.utils.normalizers import normalize_pii_value
from src.utils.validators import validate_pii

# It's good practice to set up the logger at the module scope.
# The class will then use an instance of this logger.
logger = logging.getLogger(__name__)


class RegexService:
    """
    Service to find, filter, and restore PII from text using Regex.

    This class encapsulates the logic for:
    1. Finding all PII matches based on defined patterns.
    2. Validating matches to reduce false positives.
    3. Handling overlapping matches by prioritizing more specific PII types.
    4. Replacing PII with placeholders and generating a mapping.
    5. Restoring the original text from the filtered text and the map.
    """

    # Priority is defined as a class attribute, as it's a configuration constant.
    # Types with a lower number have higher priority.
    _TYPE_PRIORITY: Dict[str, int] = {
        "CPF": 1,
        "CNPJ": 1,
        "EMAIL": 1,
        "PIS": 1,
        "TITULO_ELEITOR": 1,
        "CARTAO_CREDITO": 2,
        "CEP": 3,
        "TELEFONE": 4,
        "CONTA_BANCARIA": 5,
        "RG": 6,  # RG has lower priority as its pattern can be more generic.
    }

    def __init__(self):
        """Initializes the RegexService."""
        self.logger = logger

    def _find_all_matches(
        self, text: str, validate_pii_data: bool
    ) -> List[Dict[str, Any]]:
        """Finds all valid PII matches in the text."""
        all_matches = []
        for pii_type, pattern in PII_PATTERNS.items():
            try:
                for match in pattern.finditer(text):
                    pii_value = match.group(0)
                    if validate_pii_data and not validate_pii(pii_type, pii_value):
                        self.logger.debug(
                            "Invalid PII detected and ignored: %s = %s",
                            pii_type,
                            pii_value,
                        )
                        continue

                    all_matches.append(
                        {
                            "match": match,
                            "type": pii_type,
                            "value": pii_value,
                            "normalized_value": normalize_pii_value(
                                pii_type, pii_value
                            ),
                        }
                    )
            except (ValueError, TypeError) as e:
                self.logger.error("Error processing pattern %s: %s", pii_type, e)
                continue
        return all_matches

    def _handle_overlaps(
        self, all_matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Resolves PII overlaps by selecting the highest-priority match."""
        if not all_matches:
            return []

        # Sorts matches by their start position for sequential processing.
        all_matches.sort(key=lambda x: x["match"].start())

        unique_matches = []
        i = 0
        while i < len(all_matches):
            current_match = all_matches[i]
            _, current_end = current_match["match"].span()

            # Groups all matches that overlap with the current one.
            overlapping_matches = [current_match]
            j = i + 1
            while j < len(all_matches):
                next_match = all_matches[j]
                if next_match["match"].start() < current_end:
                    overlapping_matches.append(next_match)
                    j += 1
                else:
                    break

            # Selects the best match from the group based on priority.
            best_match = min(
                overlapping_matches,
                key=lambda m: self._TYPE_PRIORITY.get(m["type"], 99),
            )
            unique_matches.append(best_match)

            # Skips to the next index after the overlapping group.
            i = j
        return unique_matches

    def _replace_pii_with_placeholders(
        self, text: str, matches: List[Dict[str, Any]]
    ) -> Tuple[str, List[PIIMapping]]:
        """Replaces PII matches with placeholders and creates the mappings."""
        modified_text = text
        mappings_found: List[PIIMapping] = []

        # Sorts in reverse order to avoid index issues during replacement.
        matches.sort(key=lambda x: x["match"].start(), reverse=True)

        # Counts occurrences to create unique placeholders (e.g., [CPF_1], [CPF_2]).
        total_counts: Dict[str, int] = {}
        for item in reversed(matches):
            pii_type = item["type"]
            total_counts[pii_type] = total_counts.get(pii_type, 0) + 1

        current_counts = total_counts.copy()

        for item in matches:
            match = item["match"]
            pii_type = item["type"]
            pii_value = item["value"]

            # Creates a unique placeholder (e.g., [CPF_2], [CPF_1]).
            placeholder = f"[{pii_type}_{current_counts[pii_type]}]"
            current_counts[pii_type] -= 1

            mapping = PIIMapping(
                placeholder=placeholder,
                original_value=pii_value,
                type=pii_type,
                span=match.span(),
            )
            mappings_found.append(mapping)

            try:
                modified_text = (
                    modified_text[: match.start()]
                    + placeholder
                    + modified_text[match.end() :]
                )
            except (ValueError, TypeError) as e:
                self.logger.error("Error substituting text for %s: %s", pii_type, e)
                continue

        mappings_found.reverse()
        return modified_text, mappings_found

    def filter_by_regex(
        self, text: str, validate_pii_data: bool = True
    ) -> Tuple[str, List[PIIMapping]]:
        """
        Finds and filters PII from a text using regular expressions.

        Args:
            text (str): The input text to be filtered.
            validate_pii_data (bool): If True, performs algorithmic validation
                on potential PII matches to reduce false positives.

        Returns:
            Tuple[str, List[PIIMapping]]: A tuple containing:
                - The modified text with PII replaced by placeholders.
                - A list of PIIMapping objects, linking each placeholder to its
                  original value.
        """
        if not text or not isinstance(text, str):
            self.logger.warning("Invalid text provided for filtering. Returning empty.")
            return text or "", []

        # Step 1: Find all potential matches.
        all_matches = self._find_all_matches(text, validate_pii_data)

        if not all_matches:
            self.logger.info("No valid PII found in the text.")
            return text, []

        # Step 2: Handle overlaps.
        unique_matches = self._handle_overlaps(all_matches)

        # Step 3: Generate placeholders and perform replacements.
        modified_text, mappings = self._replace_pii_with_placeholders(
            text, unique_matches
        )

        self.logger.info(
            "Processing complete: %d PII instances filtered.", len(mappings)
        )
        return modified_text, mappings

    def restore_pii_from_mappings(
        self, filtered_text: str, mappings: List[PIIMapping]
    ) -> str:
        """
        Restores the original PII into a text that contains placeholders.

        Args:
            filtered_text (str): The text containing PII placeholders (e.g., "[CPF_1]").
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
                self.logger.error(
                    "Error restoring mapping %s: %s", mapping.placeholder, e
                )
                continue

        self.logger.info("%d PII instances restored in the text.", len(mappings))
        return restored_text
