import re
from typing import Dict, List, Tuple
from models import PIIMapping


PII_PATTERNS: Dict[str, re.Pattern] = {
    "CPF": re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),
    "CNPJ": re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"),
    "EMAIL": re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
    "TELEFONE": re.compile(r"(?:\(?\d{2}\)?\s?)?(?:9\s?)?\d{4,5}-\d{4}"),
    "CEP": re.compile(r"\b\d{5}-\d{3}\b"),
}


def filter_by_regex(text: str) -> Tuple[str, List[PIIMapping]]:
    mappings_found = []
    modified_text = text

    all_matches = []

    for pii_type, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(text):
            all_matches.append({"match": match, "type": pii_type})

    all_matches.sort(key=lambda x: x["match"].start(), reverse=True)

    placeholder_counts = {pii_type: 0 for pii_type in PII_PATTERNS}
    for item in all_matches:
        match = item["match"]
        pii_type = item["type"]

        pii_value = match.group(0)

        placeholder_counts[pii_type] += 1
        placeholder = f"[{pii_type}_{placeholder_counts[pii_type]}]"

        mappings_found.append(
            PIIMapping(placeholder=placeholder, original_value=pii_value, type=pii_type)
        )

        modified_text = (
            modified_text[: match.start()] + placeholder + modified_text[match.end() :]
        )
    mappings_found.reverse()

    return modified_text, mappings_found
