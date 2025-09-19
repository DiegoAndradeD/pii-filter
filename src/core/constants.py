"""
The dictionary of regex patterns designed to detect Brazilian PII formats.
Each pattern is compiled for better performance.
"""

import re
from typing import Dict


PII_PATTERNS: Dict[str, re.Pattern] = {
    "CPF": re.compile(r"\b(?:\d{3}\.?\d{3}\.?\d{3}-?\d{2})\b"),
    "CNPJ": re.compile(r"\b(?:\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})\b"),
    "EMAIL": re.compile(
        r"\b[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b",
        re.IGNORECASE,
    ),
    "TELEFONE": re.compile(r"\(\d{2}\)\s\d{4,5}[-\s]?\d{4}"),
    "CEP": re.compile(r"\b\d{5}-?\d{3}\b"),
    "RG": re.compile(r"\bRG\s*:?\s*\d{1,2}\.?\d{3}\.?\d{3}-?[0-9X]\b", re.IGNORECASE),
    "CARTAO_CREDITO": re.compile(r"\b(?:\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})\b"),
    "PIS": re.compile(r"\b\d{3}\.?\d{5}\.?\d{2}-?\d\b"),
    "TITULO_ELEITOR": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "CONTA_BANCARIA": re.compile(
        r"\b(?:conta|cc|c/c)\s*:?\s*\d{4,8}[-\s]?\d{1,2}\b", re.IGNORECASE
    ),
}


PORTUGUESE_STOP_WORDS = [
    "a",
    "o",
    "e",
    "de",
    "do",
    "da",
    "em",
    "um",
    "uma",
    "que",
    "para",
    "com",
    "não",
    "se",
    "os",
    "as",
    "por",
    "no",
    "na",
    "dos",
    "das",
    "como",
    "mais",
    "mas",
]
