"""
Unit tests for Brazilian document validation (CPF and CNPJ).

This module uses pytest to ensure that the validation functions
for CPFs and CNPJs accept valid inputs and reject invalid ones.
"""

from src.utils.validators import validate_cnpj, validate_cpf


class TestDocumentValidation:
    """Test suite for CPF and CNPJ validation."""

    def test_cpf_validation(self):
        """Tests CPF validation."""
        valid_cpfs = ["123.456.789-09", "98765432100"]
        for cpf in valid_cpfs:
            assert validate_cpf(cpf), f"Valid CPF was not recognized: {cpf}"

        invalid_cpfs = ["123.456.789-00", "111.111.111-11", "123456789"]
        for cpf in invalid_cpfs:
            assert not validate_cpf(cpf), f"Invalid CPF was accepted: {cpf}"

    def test_cnpj_validation(self):
        """Tests CNPJ validation."""
        valid_cnpjs = ["11.222.333/0001-81", "11222333000181"]
        for cnpj in valid_cnpjs:
            assert validate_cnpj(cnpj), f"Valid CNPJ was not recognized: {cnpj}"

        invalid_cnpjs = ["11.222.333/0001-00", "00000000000000", "12345678"]
        for cnpj in invalid_cnpjs:
            assert not validate_cnpj(cnpj), f"Invalid CNPJ was accepted: {cnpj}"
