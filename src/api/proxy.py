"""
Prompt processing API endpoint.

This module defines the FastAPI route for processing prompts.
It applies a multi-step pipeline:
1. Regex-based filtering for PII.
2. LLM-based semantic filtering for sensitive topics.
3. (Future) NER-based filtering.
Finally, it consolidates the masked mappings and returns a processed response.
"""

from fastapi import APIRouter

from src.models.models import ProcessedResponse, PromptRequest
from src.services import local_llm_service
from src.services.regex_service import RegexService

router = APIRouter()


@router.post("/process-prompt", response_model=ProcessedResponse)
def process_prompt(request: PromptRequest):
    """
    Processes a text prompt by filtering PII and sensitive topics.
    """
    original_text = request.original_prompt

    # Initialize services
    regex_service = RegexService()
    llm_service = local_llm_service.LocalLLMService()

    # --- Step 1: Regex Filter ---
    # Start with the original text
    regex_filtered_text, regex_mappings = regex_service.filter_by_regex(
        original_text, validate_pii_data=False
    )

    # The text for the next step is already partially filtered
    processed_text = regex_filtered_text

    # --- Step 2: Semantic LLM Filter ---
    # The LLM also filters the text and returns mappings
    # IMPORTANT: For better context, the LLM analyzes the original text,
    # but replacements are applied to 'processed_text' to maintain order.
    # The current implementation in llm_service already handles this.
    # In a pure pipeline, we would pass 'processed_text', but this would lose context.
    # Therefore, we pass the original text for analysis but apply masks on the already filtered text.

    # Apply LLM filtering on the regex-processed text
    llm_filtered_text, llm_mappings = llm_service.filter_sensitive_topics(
        processed_text
    )
    processed_text = llm_filtered_text

    # --- Step 3: NER Filter (Future) ---
    # ...

    # --- Consolidation of Results ---
    all_pii_masked = regex_mappings + llm_mappings

    # Sort all mappings by starting position for consistency
    all_pii_masked.sort(key=lambda m: m.span[0])

    # (TODO: Call external LLM with the final 'processed_text')
    llm_external_response = (
        f"Simulated external LLM response for the safe text: {processed_text}"
    )

    # (TODO: Restore the external LLM response)
    # final_response = restoration_service.restore_all(llm_external_response, all_pii_masked)
    # For now, return the response without restoration to observe the masking result
    final_response = llm_external_response

    return ProcessedResponse(
        final_response=final_response,
        pii_masked=all_pii_masked,
        sensitive_topics_detected=[
            m.type for m in llm_mappings
        ],  # List of sensitive topics detected
    )
