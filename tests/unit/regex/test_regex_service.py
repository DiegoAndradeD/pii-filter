"""
Unit and scenario tests for the RegexService.

This test suite focuses on testing the RegexService in isolation with specific,
controlled inputs to verify its behavior across different scenarios, including
happy paths, edge cases, and invalid data.
"""

import re
from unittest.mock import MagicMock
import pytest
from src.services.regex_service import RegexService


class TestRegexService:
    """Test suite for specific RegexService scenarios."""

    regex_service: RegexService = None

    def setup_method(self):
        """
        Pytest special method executed before each test in this class.
        Ensures each test starts with a fresh, clean instance of the service.
        """
        self.regex_service = RegexService()

    # --- Group 1: Standard Cases ("Happy Path") ---

    def test_detects_simple_cpf(self):
        """
        Verifies that a single, well-formatted CPF is correctly identified.
        """
        prompt = "The client's CPF is 123.456.789-00 and their code is 987."

        _filtered_text, mappings = self.regex_service.filter_by_regex(
            prompt, validate_pii_data=False
        )

        assert len(mappings) == 1, "Should have found exactly 1 PII."

        detected_pii = mappings[0]
        assert detected_pii.type == "CPF"
        assert detected_pii.original_value == "123.456.789-00"

    def test_detects_simple_email(self):
        """
        Verifies that a single, well-formatted email is correctly identified.
        """

        prompt = (
            "For more information, please send an email to contact@mycompany.com.br."
        )

        _filtered_text, mappings = self.regex_service.filter_by_regex(prompt)

        assert len(mappings) == 1, "Should have found exactly 1 PII."

        detected_pii = mappings[0]
        assert detected_pii.type == "EMAIL"
        assert detected_pii.original_value == "contact@mycompany.com.br"

    def test_detects_simple_telefone(self):
        """
        Verifies that a single, well-formatted mobile phone number is identified.
        """

        prompt = "The emergency phone number is (11) 98765-4321."

        _filtered_text, mappings = self.regex_service.filter_by_regex(prompt)

        assert len(mappings) == 1, "Should have found exactly 1 PII."

        detected_pii = mappings[0]
        assert detected_pii.type == "TELEFONE"
        assert detected_pii.original_value == "(11) 98765-4321"

    def test_detects_multiple_pii_types_in_one_prompt(self):
        """
        Verifies that the service can find multiple, different PII types
        in a single prompt.
        """

        prompt = "John's registration has the CPF 111.222.333-44, e-mail john@test.com, and phone (21) 99999-8888."

        _filtered_text, mappings = self.regex_service.filter_by_regex(
            prompt, validate_pii_data=False
        )

        assert len(mappings) == 3, "Should have found exactly 3 PIIs."

        detected_types = {pii.type for pii in mappings}
        expected_types = {"CPF", "EMAIL", "TELEFONE"}

        assert (
            detected_types == expected_types
        ), "The detected PII types do not match the expected ones."

    def test_detects_cpf_without_punctuation(self):
        """Verifies that a CPF without any punctuation is still detected."""
        prompt = "Please inform CPF 12345678900 to proceed."
        _filtered_text, mappings = self.regex_service.filter_by_regex(
            prompt, validate_pii_data=False
        )
        assert len(mappings) == 1
        assert mappings[0].type == "CPF"
        assert mappings[0].original_value == "12345678900"

    @pytest.mark.parametrize(
        "phone_number",
        [
            "+55 (11) 98765-4321",  # With country code
            "(21) 3456-7890",  # Landline without 9th digit
            "(85) 91234 5678",  # With space instead of hyphen
        ],
    )
    def test_detects_telefone_with_variations(self, phone_number):
        """Verifies that different valid phone formats are detected."""
        prompt = f"The contact number is {phone_number}."
        _filtered_text, mappings = self.regex_service.filter_by_regex(prompt)
        assert len(mappings) == 1, f"Failed to detect phone number: {phone_number}"
        assert mappings[0].type == "TELEFONE"
        assert mappings[0].original_value == phone_number

    @pytest.mark.parametrize(
        "email_address",
        [
            "joao.silva@rh.my-company.com.br",  # With subdomain and hyphen
            "contact+newsletter@gmail.com",  # With a '+' alias
            "user_123@domain.co",  # With underscore and short TLD
        ],
    )
    def test_detects_email_with_variations(self, email_address):
        """Verifies that different valid email formats are detected."""
        prompt = f"The user's email is {email_address}."
        _filtered_text, mappings = self.regex_service.filter_by_regex(prompt)
        assert len(mappings) == 1, f"Failed to detect email: {email_address}"
        assert mappings[0].type == "EMAIL"
        assert mappings[0].original_value == email_address

    def test_detects_rg_with_lowercase_prefix(self):
        """Verifies that the RG pattern is case-insensitive."""
        prompt = "Please provide the document rg: 12.345.678-9."
        _filtered_text, mappings = self.regex_service.filter_by_regex(prompt)
        assert len(mappings) == 1
        assert mappings[0].type == "RG"
        assert mappings[0].original_value == "rg: 12.345.678-9"

    # UPDATED: This test is no longer expected to fail.
    # It now verifies the new, improved functionality.
    def test_detects_rg_without_prefix(self):
        """
        Verifies that the improved regex can find an RG number even if it
        doesn't have the 'RG:' prefix.
        """
        prompt = "He presented the document 45.678.901-X as identification."
        _filtered_text, mappings = self.regex_service.filter_by_regex(prompt)

        assert len(mappings) == 1, "Should have found the RG number without a prefix."
        assert mappings[0].type == "RG"
        assert mappings[0].original_value == "45.678.901-X"

    def test_ignores_protocol_number_similar_to_cpf(self):
        """
        Verifies that a protocol number that resembles a CPF is not detected,
        thanks to the word boundary `\b` in the regex.
        """
        prompt = "The cancellation protocol is 987.654.321-88/2025."
        _filtered_text, mappings = self.regex_service.filter_by_regex(prompt)
        assert (
            len(mappings) == 0
        ), "Should not detect a CPF that is part of a larger protocol number."

    def test_ignores_product_code_similar_to_phone(self):
        """
        Verifies that a simple numeric code is not incorrectly flagged as a phone number.
        """
        prompt = "The product code for this item is 2024-1234."
        _filtered_text, mappings = self.regex_service.filter_by_regex(prompt)
        assert len(mappings) == 0, "Should not detect a product code as a phone number."

    def test_detects_pii_adjacent_to_punctuation(self):
        """
        Verifies that PIIs are still found even when they are directly next to
        punctuation like colons or commas, testing the `\b` word boundary.
        """
        prompt = "Please confirm the data. CPF:123.456.789-00,e-mail:user@domain.com."
        _filtered_text, mappings = self.regex_service.filter_by_regex(
            prompt, validate_pii_data=False
        )

        assert (
            len(mappings) == 2
        ), "Should detect both CPF and Email adjacent to punctuation."

        detected_types = {pii.type for pii in mappings}
        assert "CPF" in detected_types
        assert "EMAIL" in detected_types

    @pytest.mark.parametrize(
        "invalid_cpf",
        [
            "123.456.789-0",  # Too short
            "123.456.789-001",  # Too long
            "123.456.789",  # Missing last digits
        ],
    )
    def test_ignores_structurally_invalid_cpf(self, invalid_cpf):
        """
        Verifies that the regex for CPF does not match strings with an incorrect
        number of digits.
        """
        prompt = f"User typed the following CPF: {invalid_cpf}."
        _filtered_text, mappings = self.regex_service.filter_by_regex(prompt)
        assert (
            len(mappings) == 0
        ), f"Structurally invalid CPF was detected: {invalid_cpf}"

    def test_ignores_mathematically_invalid_cpf_when_validation_is_on(self):
        """
        Verifies that a CPF with all same digits (which is mathematically invalid)
        is rejected when the validator is active.
        """
        prompt = "The number 111.111.111-11 is not a valid CPF."
        # validate_pii_data=True is the default, but we make it explicit here for clarity.
        _filtered_text, mappings = self.regex_service.filter_by_regex(
            prompt, validate_pii_data=True
        )
        assert (
            len(mappings) == 0
        ), "Mathematically invalid CPF should be rejected by the validator."

    def test_detects_mathematically_invalid_cpf_when_validation_is_off(self):
        """
        Verifies that a CPF with all same digits IS DETECTED when the validator
        is explicitly turned off. This confirms the regex itself is working.
        """
        prompt = "The number 111.111.111-11 is not a valid CPF."
        _filtered_text, mappings = self.regex_service.filter_by_regex(
            prompt, validate_pii_data=False
        )
        assert (
            len(mappings) == 1
        ), "Invalid CPF should be found by the regex if validation is off."
        assert mappings[0].type == "CPF"

    @pytest.mark.parametrize(
        "invalid_email",
        [
            "user.domain.com",  # Missing '@'
            "@domain.com",  # Missing local part
            "user@.com",  # Missing domain name
            "user@domain.",  # Missing top-level domain
        ],
    )
    def test_ignores_invalid_email_formats(self, invalid_email):
        """
        Verifies that common invalid email formats are not detected.
        """
        prompt = f"The user entered the following email: {invalid_email}."
        _filtered_text, mappings = self.regex_service.filter_by_regex(prompt)
        assert len(mappings) == 0, f"Invalid email format was detected: {invalid_email}"

    def test_handles_repeated_pii_correctly(self):
        """
        Verifies that all occurrences of a repeated PII are found and that they
        receive unique placeholders.
        """
        prompt = "Main contact: (11) 98888-7777. If unavailable, call the secondary number: (11) 98888-7777."
        filtered_text, mappings = self.regex_service.filter_by_regex(prompt)

        assert len(mappings) == 2, "Should have found 2 phone numbers."

        # Verify that both found items are the same phone number
        assert mappings[0].type == "TELEFONE"
        assert mappings[1].type == "TELEFONE"
        assert mappings[0].original_value == "(11) 98888-7777"

        # Verify that the placeholders are unique
        placeholders = {pii.placeholder for pii in mappings}
        assert len(placeholders) == 2, "Placeholders for repeated PII should be unique."

        # Verify that the text was correctly filtered with both unique placeholders
        assert "[TELEFONE_1]" in filtered_text
        assert "[TELEFONE_2]" in filtered_text

    def test_overlap_handler_selects_highest_priority(self):
        """
        Directly tests the `_handle_overlaps` method to ensure it correctly
        chooses the PII type with the highest priority (lowest number)
        when two patterns match the same text.
        """
        # We need to simulate `re.Match` objects for the test
        # A mock object is perfect for this
        mock_match = MagicMock(spec=re.Match)
        mock_match.start.return_value = 10
        mock_match.end.return_value = 20
        mock_match.span.return_value = (10, 20)

        # Simulate two overlapping detections for the same text span
        # TELEFONE has priority 4, RG has priority 6.
        # The method should choose TELEFONE.
        all_matches = [
            {
                "match": mock_match,
                "type": "RG",  # Lower priority (6)
                "value": "123456789",
            },
            {
                "match": mock_match,
                "type": "TELEFONE",  # Higher priority (4)
                "value": "123456789",
            },
        ]

        # Execute the private method we want to test
        unique_matches = self.regex_service._handle_overlaps(all_matches)

        # Verify
        assert len(unique_matches) == 1, "Overlap handler should return only one match."
        assert (
            unique_matches[0]["type"] == "TELEFONE"
        ), "The match with the highest priority should be chosen."
