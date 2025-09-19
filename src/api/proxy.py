# src/api/proxy.py
from fastapi import APIRouter

from src.models.models import PIIMapping, ProcessedResponse, PromptRequest
from src.services.regex_service import RegexService
from src.services.restoration_service import RestorationService

router = APIRouter()


@router.post("/process-prompt", response_model=ProcessedResponse)
def process_prompt(request: PromptRequest):
    """
    Processes a text prompt by filtering PII and detecting sensitive topics.

    Steps:
    1. Apply regex-based PII filtering using RegexService.
    2. (TODO) Apply NER filter.
    3. (TODO) Detect sensitive topics using external LLM.
    4. (TODO) Call external LLM with filtered text.
    5. Restore PII in the final response using RestorationService.
    """
    original_text = request.original_prompt
    pii_masked: list[PIIMapping] = []
    sensitive_topics_detected: list[str] = []

    # Initialize services
    regex_service = RegexService()
    restoration_service = RestorationService()

    # --- Step 1: Regex Filter ---
    regex_filtered_text, regex_mappings = regex_service.filter_by_regex(
        original_text, validate_pii_data=False
    )
    processed_text = regex_filtered_text
    pii_masked.extend(regex_mappings)

    # --- Step 2: NER Filter (TODO) ---
    # ner_filtered_text, ner_mappings = ner_service.filter_by_ner(processed_text)
    # processed_text = ner_filtered_text
    # pii_masked.extend(ner_mappings)
    ner_mappings = []  # Placeholder até implementar

    # --- Step 3: Topic Detection (TODO) ---
    # sensitive_topics_detected = topic_service.detect_sensitive_topics(processed_text)

    # --- Step 4: External LLM Call (TODO) ---
    # Por enquanto, simula uma resposta do LLM
    llm_response = f"Resposta processada: {processed_text}"

    # --- Step 5: Restore PII using RestorationService ---
    restoration_data = restoration_service.create_restoration_data(
        regex_mappings=regex_mappings, ner_mappings=ner_mappings
    )

    final_response = restoration_service.restore_all(llm_response, restoration_data)

    return ProcessedResponse(
        final_response=final_response,
        pii_masked=pii_masked,
        sensitive_topics_detected=sensitive_topics_detected,
    )
