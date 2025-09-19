"""Pydantic models for handling prompt requests and PII processing."""

from dataclasses import dataclass
from typing import List, Tuple
from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """Represents an incoming prompt request."""

    original_prompt: str  # The raw prompt text sent by the user


class PIIMapping(BaseModel):
    """Maps detected PII to placeholders."""

    placeholder: str = Field(
        ..., description="Placeholder replacing the sensitive data."
    )
    original_value: str = Field(..., description="The original sensitive value.")
    type: str = Field(..., description="Type of PII detected (e.g., CPF, EMAIL).")

    # --- ESTA É A LINHA QUE PROVAVELMENTE ESTÁ FALTANDO ---
    span: Tuple[int, int] = Field(
        ..., description="The start and end position of the PII in the text."
    )


class ProcessedResponse(BaseModel):
    """Represents the processed response after PII masking and sensitive topic detection."""

    final_response: str  # Final text after masking
    pii_masked: List[PIIMapping]  # List of PII items that were masked
    sensitive_topics_detected: List[
        str
    ]  # List of sensitive topics identified in the text


@dataclass
class PIIGroundTruth:
    """Represents a ground truth PII annotation."""

    pii_type: str
    value: str
    span: Tuple[int, int]
