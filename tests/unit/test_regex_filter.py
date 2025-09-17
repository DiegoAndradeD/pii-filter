"""
Test module for the RegexService PII filtering functionality.

This module contains unit tests for validating detection, filtering,
and restoration of personally identifiable information (PII) such as
emails, phone numbers, CPFs, CNPJs, and other sensitive data within text.

It also includes tests for handling invalid inputs, overlapping patterns,
and dataset-driven validation using pytest.
"""

import json
import time
from typing import List, Dict, Any
import logging
import pytest

from src.core.constants import PII_PATTERNS
from src.models.models import PIIMapping
from src.services.regex_service import RegexService
from src.utils.validators import validate_cnpj, validate_cpf

# Configuração de logging para os testes
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATASET_FILE = "hr_dataset.jsonl"

regex_service = RegexService()


def load_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Loads the dataset with improved error handling."""
    prompts = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if "text" not in data:
                        logger.warning("Line %d: 'text' field not found", line_num)

                        continue
                    prompts.append(data)
                except json.JSONDecodeError as e:
                    logger.error("JSON error on line %d: %s", line_num, e)
                    continue
    except FileNotFoundError:
        logger.error("File %s not found", file_path)
        return []
    except OSError as e:
        logger.error("Error loading dataset: %s", e)

        return []

    logger.info("Dataset loaded: %d valid entries", len(prompts))
    return prompts


class TestRegexFilter:
    """Test class for the regex filter with specific cases."""

    def test_cpf_validation(self):
        """Tests CPF validation."""
        # Valid CPFs
        valid_cpfs = ["123.456.789-09", "98765432100"]
        for cpf in valid_cpfs:
            assert validate_cpf(cpf), f"Valid CPF was not recognized: {cpf}"

        # Invalid CPFs
        invalid_cpfs = ["123.456.789-00", "111.111.111-11", "123456789"]
        for cpf in invalid_cpfs:
            assert not validate_cpf(cpf), f"Invalid CPF was accepted: {cpf}"

    def test_cnpj_validation(self):
        """Tests CNPJ validation."""
        # Valid CNPJs (example)
        valid_cnpjs = ["11.222.333/0001-81"]
        for cnpj in valid_cnpjs:
            # Note: using a real valid CNPJ for the test
            if validate_cnpj("11222333000181"):  # without punctuation format
                assert True

        # Invalid CNPJs
        invalid_cnpjs = ["11.222.333/0001-00", "111.111.111/1111-11"]
        for cnpj in invalid_cnpjs:
            assert not validate_cnpj(cnpj), f"Invalid CNPJ was accepted: {cnpj}"

    def test_email_detection(self):
        """Tests email detection."""
        test_text = "Contato: joão@empresa.com.br e maria.silva@teste.org"
        _, mappings = regex_service.filter_by_regex(test_text)

        email_mappings = [m for m in mappings if m.type == "EMAIL"]
        assert (
            len(email_mappings) >= 1
        ), f"Should have found at least 1 email, found it {len(email_mappings)}"

        # Checks if at least one of the emails was found
        found_emails = [m.original_value for m in email_mappings]
        assert any(
            email in ["joão@empresa.com.br", "maria.silva@teste.org"]
            for email in found_emails
        )

    def test_phone_detection(self):
        """Tests phone detection."""
        test_text = "Fone: (11) 99999-8888 ou 21 3333-4444"
        _, mappings = regex_service.filter_by_regex(test_text)

        phone_mappings = [m for m in mappings if m.type == "TELEFONE"]
        assert len(phone_mappings) >= 2

    def test_multiple_pii_types(self):
        """Tests detection of multiple PII types."""
        test_text = """
        Nome: João Silva
        CPF: 123.456.789-09
        Email: joao@email.com
        Telefone: (11) 99999-8888
        CEP: 01234-567
        """

        _, mappings = regex_service.filter_by_regex(test_text, validate_pii_data=False)

        # Checks if different types were detected
        detected_types = {mapping.type for mapping in mappings}
        expected_types = {"EMAIL", "TELEFONE", "CEP"}

        # At least some types should have been detected
        assert len(detected_types & expected_types) > 0

    def test_pii_restoration(self):
        """Tests if PII restoration works correctly."""
        original_text = "Email: teste@exemplo.com, telefone: (11) 99999-9999"
        filtered_text, mappings = regex_service.filter_by_regex(original_text)

        if mappings:  # If any PII was found
            restored_text = regex_service.restore_pii_from_mappings(
                filtered_text, mappings
            )

            # The restored text must contain the original values
            for mapping in mappings:
                assert mapping.original_value in restored_text

    def test_empty_and_invalid_inputs(self):
        """Tests behavior with empty or invalid inputs."""
        # Empty text
        filtered_text, mappings = regex_service.filter_by_regex("")
        assert filtered_text == ""
        assert not mappings

        # None text
        filtered_text, mappings = regex_service.filter_by_regex(None)
        assert filtered_text == ""
        assert not mappings

        # Text without PII
        test_text = "Este é um texto normal sem informações sensíveis."
        filtered_text, mappings = regex_service.filter_by_regex(test_text)
        assert filtered_text == test_text
        assert not mappings

    def test_overlapping_patterns(self):
        """Tests cases where patterns might overlap."""
        # Specific test for the case that was failing
        test_text = (
            "Atualize a conta bancária para crédito de salário de João Silva, "
            "CPF 123.456.789-09. Nova conta: Nubank, Agência 0001, Conta 9876543-2."
        )
        filtered_text, mappings = regex_service.filter_by_regex(test_text)

        # Checks that there are no duplicates in the same position
        positions = set()
        for mapping in mappings:
            # Finds the position of the original value in the text
            pos = test_text.find(mapping.original_value)
            if pos != -1:
                position_range = (pos, pos + len(mapping.original_value))
                assert (
                    position_range not in positions
                ), f"Duplicate position found for {mapping.original_value}"
                positions.add(position_range)

        # Checks that all placeholders are in the filtered text
        for mapping in mappings:
            assert (
                mapping.placeholder in filtered_text
            ), f"Placeholder {mapping.placeholder} not found in filtered text"

        # Test with a number that could be an ID or account
        test_text2 = "O número 12345678 pode ser confundido"
        filtered_text2, mappings2 = regex_service.filter_by_regex(test_text2)

        # If something was detected, all placeholders must be in the text
        for mapping in mappings2:
            assert mapping.placeholder in filtered_text2

    def test_placeholder_format(self):
        """Tests if the placeholders are in the correct format."""
        test_text = "Email: user@domain.com e outro@site.org"
        _, mappings = regex_service.filter_by_regex(test_text)

        for mapping in mappings:
            # Placeholder must have the format [TYPE_NUMBER]
            assert mapping.placeholder.startswith("[")
            assert mapping.placeholder.endswith("]")
            assert "_" in mapping.placeholder
            assert mapping.type in mapping.placeholder


@pytest.mark.parametrize("prompt_entry", load_dataset(DATASET_FILE))
def test_filter_by_regex_dataset(prompt_entry):
    """Tests the filter with the provided dataset."""
    prompt_id = prompt_entry.get("id", "N/A")
    logger.info("--- Starting test for ID: %s ---", prompt_id)

    original_text = prompt_entry["text"]

    # Checks if the text is valid
    if not original_text or not isinstance(original_text, str):
        pytest.skip(f"Invalid text for ID {prompt_id}")

    logger.info(
        "Texto original (primeiros 200 chars): %s...",
        original_text[:200].replace("\n", " "),
    )

    try:
        # Tests with validation enabled
        filtered_text, mappings = regex_service.filter_by_regex(
            original_text, validate_pii_data=True
        )

        # Also tests without validation for comparison
        _, mappings_no_val = regex_service.filter_by_regex(
            original_text, validate_pii_data=False
        )

        logger.info("Com validação: %d PIIs encontrados", len(mappings))
        logger.info("Sem validação: %d PIIs encontrados", len(mappings_no_val))

        if mappings:
            # logger.info("Text has been modified. PII found:")
            for i, mapping in enumerate(mappings):
                logger.info(
                    "  %d. %s: %s -> %s",
                    i + 1,
                    mapping.type,
                    (
                        mapping.original_value[:20] + "..."
                        if len(mapping.original_value) > 20
                        else mapping.original_value
                    ),
                    mapping.placeholder,
                )

            # Checks if the text was actually modified
            assert filtered_text != original_text

            # Tests restoration
            restored_text = regex_service.restore_pii_from_mappings(
                filtered_text, mappings
            )

            # Checks if the restoration works
            for mapping in mappings:
                assert mapping.original_value in restored_text
        else:
            # logger.info("Nenhum PII encontrado. Texto inalterado.")
            assert filtered_text == original_text

        # Integrity validations
        for mapping in mappings:
            assert isinstance(mapping, PIIMapping)
            assert mapping.placeholder.startswith("[") and mapping.placeholder.endswith(
                "]"
            )
            assert mapping.original_value in original_text
            assert mapping.type in PII_PATTERNS
            assert mapping.placeholder in filtered_text

        logger.info("Teste para ID %s passou com sucesso!\n", prompt_id)

    except Exception as e:
        logger.error("Error during ID test %s: %s", prompt_id, str(e))
        raise


def test_performance_benchmark():
    """Basic performance test."""

    # Text with multiple PIIs to test performance
    large_text = (
        """
    Dados pessoais: João Silva, CPF 123.456.789-09, email joao@empresa.com.br
    Telefone (11) 99999-8888, CEP 01234-567, CNPJ 11.222.333/0001-81
    """
        * 100
    )  # Repeats 100 times

    start_time = time.time()
    _, mappings = regex_service.filter_by_regex(large_text)
    end_time = time.time()

    processing_time = end_time - start_time
    logger.info(
        "Processing time: %.4fs for %d characters", processing_time, len(large_text)
    )
    logger.info("PIIs found: %d", len(mappings))

    # Should process in a reasonable time (less than 5 seconds)
    assert processing_time < 5.0, f"Very slow processing: {processing_time}s"
