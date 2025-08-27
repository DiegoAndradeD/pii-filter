from typing import List
from pydantic import BaseModel


class PromptRequest(BaseModel):
    original_prompt: str


class PIIMapping(BaseModel):
    placeholder: str
    original_value: str
    type: str


class ProcessedResponse(BaseModel):
    final_response: str
    pii_masked: List[PIIMapping]
    sensitive_topics_detected: List[str]
