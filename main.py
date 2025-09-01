"""FastAPI service for processing prompts and filtering PII (Personally Identifiable Information)."""

from fastapi import FastAPI

from models.models import PIIMapping, ProcessedResponse, PromptRequest
from services.regex_service import RegexService


app = FastAPI(
    title="PII FILTER",
    description="",
    version="0.1.0",
)


@app.get("/")
def read_root():
    """Simple health check endpoint that returns a welcome message."""
    return {"message": "Welcome"}


@app.post("/process-prompt", response_model=ProcessedResponse)
def process_prompt(request: PromptRequest):
    """
    Processes a text prompt by filtering PII and detecting sensitive topics.

    Steps:
    1. Applies regex-based PII filtering using RegexService.
    2. (TODO) Apply NER filter.
    3. (TODO) Detect sensitive topics using external LLM.
    4. (TODO) De-sanitize LLM response.

    Args:
        request (PromptRequest): The incoming prompt request.

    Returns:
        ProcessedResponse: The prompt text with PII masked and detected sensitive topics.
    """
    original_text = request.original_prompt
    pii_masked: list[PIIMapping] = []
    sensitive_topics_detected: list[str] = []
    regex_service = RegexService()

    # --- Step 1: Regex Filter ---
    regex_filtered_text, regex_mapping = regex_service.filter_by_regex(original_text)
    original_text = regex_filtered_text
    pii_masked.extend(regex_mapping)

    # --- Next Steps (to be implemented) ---
    # TODO: Call the NER filter
    # TODO: Call the Topic filter/external LLM
    # TODO: Call the external LLM
    # TODO: De-sanitize the LLM response

    return ProcessedResponse(
        final_response=original_text,
        pii_masked=pii_masked,
        sensitive_topics_detected=sensitive_topics_detected,
    )
