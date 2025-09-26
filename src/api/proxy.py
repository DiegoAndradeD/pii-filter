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
from src.services.local_llm_service import LocalLLMService
from src.services.regex_service import RegexService
from src.services.restoration_service import RestorationService

router = APIRouter()


@router.post("/process-prompt", response_model=ProcessedResponse)
def process_prompt(request: PromptRequest):
    """
    Processes a text prompt by filtering PII and sensitive topics,
    simulates a call to an external LLM, and restores the original information.
    """
    original_text = request.original_prompt

    # Initialize services
    regex_service = RegexService()
    llm_service = LocalLLMService()
    restoration_service = RestorationService()  # Inicializa o serviço de restauração

    # --- Step 1: Regex Filter ---
    regex_filtered_text, regex_mappings = regex_service.filter_by_regex(
        original_text, validate_pii_data=False
    )
    processed_text = regex_filtered_text

    # --- Step 2: Semantic LLM Filter ---
    llm_filtered_text, llm_mappings = llm_service.filter_sensitive_topics(
        processed_text
    )
    processed_text = llm_filtered_text

    # --- Consolidation of Mappings ---
    all_pii_masked = regex_mappings + llm_mappings
    all_pii_masked.sort(key=lambda m: m.span[0])

    llm_external_response = (
        f"Claro, aqui está o rascunho do plano de melhoria de desempenho para o funcionário com base nas "
        f"informações fornecidas: {processed_text}. É importante abordar o [HISTORICO_DISCIPLINAR_1] "
        f"e levar em conta a situação delicada de [PROBLEMA_PESSOAL_FAMILIAR_1]."
    )

    restoration_data = restoration_service.create_restoration_data(
        regex_mappings=regex_mappings, llm_mappings=llm_mappings
    )

    final_response = restoration_service.restore_all(
        llm_external_response, restoration_data
    )

    return ProcessedResponse(
        final_response=final_response,
        pii_masked=all_pii_masked,
        sensitive_topics_detected=[m.type for m in llm_mappings],
    )
