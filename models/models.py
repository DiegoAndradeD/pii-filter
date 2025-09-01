"""Pydantic models for handling prompt requests and PII processing."""

from typing import List
from pydantic import BaseModel


class PromptRequest(BaseModel):
    """Represents an incoming prompt request."""

    original_prompt: str  # The raw prompt text sent by the user


class PIIMapping(BaseModel):
    """Maps detected PII to placeholders."""

    placeholder: str  # Placeholder replacing the sensitive data
    original_value: str  # The original sensitive value
    type: str  # Type of PII detected (e.g., email, SSN)


class ProcessedResponse(BaseModel):
    """Represents the processed response after PII masking and sensitive topic detection."""

    final_response: str  # Final text after masking
    pii_masked: List[PIIMapping]  # List of PII items that were masked
    sensitive_topics_detected: List[
        str
    ]  # List of sensitive topics identified in the text
