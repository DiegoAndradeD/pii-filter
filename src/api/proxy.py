# app/api/proxy.py
from fastapi import APIRouter

from src.models.models import PIIMapping, ProcessedResponse, PromptRequest
from src.services.regex_service import RegexService

router = APIRouter()


@router.post("/process-prompt", response_model=ProcessedResponse)
def process_prompt(request: PromptRequest):
    """
    Processes a text prompt by filtering PII and detecting sensitive topics.

    Steps:
    1. Applies regex-based PII filtering using RegexService.
    2. (TODO) Apply NER filter.
    3. (TODO) Detect sensitive topics using external LLM.
    4. (TODO) De-sanitize LLM response.
    """
    original_text = request.original_prompt
    pii_masked: list[PIIMapping] = []
    sensitive_topics_detected: list[str] = []
    regex_service = RegexService()

    # --- Step 1: Regex Filter ---
    regex_filtered_text, regex_mapping = regex_service.filter_by_regex(
        original_text, validate_pii_data=False
    )
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
