"""Validation functions for Brazilian PII (CPF, CNPJ, CEP, phone) and other sensitive data."""

import re


def is_plausible_cpf(cpf: str) -> bool:
    """
    Checks whether a CPF is 'plausible' for masking purposes.
    This ignores the check digit calculation but filters
    out obvious garbage, such as CPFs with all repeated digits.
    """
    # Remove any non-numeric characters
    cpf = re.sub(r"\D", "", cpf)

    # A plausible CPF must have exactly 11 digits
    if len(cpf) != 11:
        return False

    # CPFs with all digits equal are invalid and likely
    # test data, examples, or garbage
    if cpf == cpf[0] * 11:
        return False

    # If it reaches this point, it has 11 digits and is not a repeated sequence.
    # Good enough to be considered plausible PII.
    return True


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
        result = is_plausible_cpf(value)
    elif pii_type == "CNH":
        result = validate_cnh(value)
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


def validate_cnh(cnh: str) -> bool:
    """Validates a Brazilian CNH (driver's license) number using the official DENATRAN algorithm.

    Args:
        cnh (str): The CNH string, which can contain punctuation.

    Returns:
        bool: True if the CNH is valid, False otherwise.
    """
    # Remove any non-digit characters from the input string.
    cnh = re.sub(r"\D", "", cnh)

    # A valid CNH must have 11 digits. Also, CNHs with all same digits are invalid.
    if len(cnh) != 11 or cnh == cnh[0] * 11:
        return False

    # Calculate the first check digit (dv1)
    soma = 0
    for i in range(9):
        soma += int(cnh[i]) * (9 - i)

    dv1 = soma % 11
    if dv1 >= 10:
        dv1 = 0

    # Calculate the second check digit (dv2)
    soma = 0
    for i in range(9):
        soma += int(cnh[i]) * (1 + i)

    dv2 = soma % 11
    if dv2 >= 10:
        dv2 = 0

    # The CNH is valid if the calculated digits match the last two digits of the CNH.
    return int(cnh[9]) == dv1 and int(cnh[10]) == dv2
