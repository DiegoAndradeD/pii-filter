import json
import logging
import pytest
from filters.regex_filter import filter_by_regex
from models import PIIMapping

logger = logging.getLogger(__name__)

DATASET_FILE = "hr_dataset.jsonl"


def load_dataset(file_path):
    prompts = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            prompts.append(json.loads(line))
    return prompts


@pytest.mark.parametrize("prompt_entry", load_dataset(DATASET_FILE))
def test_filter_by_regex(prompt_entry):
    prompt_id = prompt_entry.get("id", "N/A")
    logger.info("--- Starting test for ID input: %s ---", prompt_id)

    original_text = prompt_entry["text"]
    logger.info("Original text (complete):\n---\n%s\n---", original_text)

    filtered_text, mappings = filter_by_regex(original_text)

    if mappings:
        logger.info("Found %s PIIs. The text has been modified.", len(mappings))

        logger.info("Filtered text (complete):\n---\n%s\n---", filtered_text)

        logger.info("Details of the mappings found:")
        for i, mapping in enumerate(mappings):
            logger.info("  - Mapping %s: %s", i + 1, mapping)

        assert filtered_text != original_text
    else:
        logger.info("No PII found. Text remained unchanged.")

    for mapping in mappings:
        assert isinstance(mapping, PIIMapping)
        assert mapping.placeholder.startswith("[") and mapping.placeholder.endswith("]")
        assert mapping.original_value in original_text
        assert mapping.type in ["CPF", "CNPJ", "EMAIL", "TELEFONE", "CEP"]

    for mapping in mappings:
        assert mapping.placeholder in filtered_text

    logger.info("Assertions for input ID: %s passed successfully.\n", prompt_id)
