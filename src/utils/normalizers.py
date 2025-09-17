"""Functions to normalize and process PII (Personally Identifiable Information) values."""

import re


def normalize_pii_value(pii_type: str, value: str) -> str:
    """
    Normalizes a PII value to a standard format.

    This is useful for consistent storage and comparison.

    Args:
        pii_type (str): The type of PII to normalize.
        value (str): The PII value to be normalized.

    Returns:
        str: The normalized PII value.
    """
    if pii_type in ["CPF", "CNPJ", "RG", "PIS", "TELEFONE"]:
        # For document numbers and phones, remove all non-digit characters.
        return re.sub(r"\D", "", value)
    elif pii_type == "EMAIL":
        # Convert emails to lowercase for consistency.
        return value.lower()
    elif pii_type == "CEP":
        # Standardize CEP to the "XXXXX-XXX" format.
        digits = re.sub(r"\D", "", value)
        return f"{digits[:5]}-{digits[5:]}"
    else:
        # Return other types as is.
        return value
