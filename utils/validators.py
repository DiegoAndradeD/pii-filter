"""Validation functions for Brazilian PII (CPF, CNPJ, CEP, phone) and other sensitive data."""

import re


def validate_cpf(cpf: str) -> bool:
    """Validates a Brazilian CPF number using the official checksum algorithm.

    Args:
        cpf (str): The CPF string, which can contain punctuation.

    Returns:
        bool: True if the CPF is valid, False otherwise.
    """
    # Remove any non-digit characters from the input string.
    cpf = re.sub(r"\D", "", cpf)

    # A valid CPF must have 11 digits. Also, CPFs with all same digits are invalid.
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    # Calculate the first check digit.
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    primeiro_digito = (soma * 10) % 11
    if primeiro_digito == 10:
        primeiro_digito = 0

    # Calculate the second check digit.
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    segundo_digito = (soma * 10) % 11
    if segundo_digito == 10:
        segundo_digito = 0

    # The CPF is valid if the calculated digits match the last two digits of the CPF.
    return int(cpf[9]) == primeiro_digito and int(cpf[10]) == segundo_digito


def validate_cnpj(cnpj: str) -> bool:
    """Validates a Brazilian CNPJ number using the official checksum algorithm.

    Args:
        cnpj (str): The CNPJ string, which can contain punctuation.

    Returns:
        bool: True if the CNPJ is valid, False otherwise.
    """
    # Remove any non-digit characters.
    cnpj = re.sub(r"\D", "", cnpj)

    # A valid CNPJ must have 14 digits. CNPJs with all same digits are invalid.
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    # Calculate the first check digit.
    peso = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * peso[i] for i in range(12))
    primeiro_digito = 11 - (soma % 11)
    if primeiro_digito >= 10:
        primeiro_digito = 0

    # Calculate the second check digit.
    peso = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * peso[i] for i in range(13))
    segundo_digito = 11 - (soma % 11)
    if segundo_digito >= 10:
        segundo_digito = 0

    # The CNPJ is valid if the calculated digits match the last two digits.
    return int(cnpj[12]) == primeiro_digito and int(cnpj[13]) == segundo_digito


def validate_pii(pii_type: str, value: str) -> bool:
    """
    Dispatches to a specific validation function based on the PII type.

    This acts as a second layer of validation after a regex match to reduce
    false positives.

    Args:
        pii_type (str): The type of PII to validate (e.g., "CPF", "EMAIL").
        value (str): The detected PII value.

    Returns:
        bool: True if the value is valid for its type, False otherwise.
    """
    result = True  # default for unknown types

    if pii_type == "CPF":
        result = validate_cpf(value)
    elif pii_type == "CNPJ":
        result = validate_cnpj(value)
    elif pii_type == "EMAIL":
        parts = value.split("@")
        if len(parts) != 2:
            result = False
        else:
            local, domain = parts
            result = bool(local and domain and ".." not in value)
    elif pii_type == "CEP":
        digits_only = re.sub(r"\D", "", value)
        result = len(digits_only) == 8
    elif pii_type == "TELEFONE":
        digits_only = re.sub(r"\D", "", value)
        result = 10 <= len(digits_only) <= 13

    return result
