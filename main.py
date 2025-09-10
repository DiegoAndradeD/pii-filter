"""FastAPI service for processing prompts and filtering PII (Personally Identifiable Information)."""

from fastapi import FastAPI

from models.models import PIIMapping, ProcessedResponse, PromptRequest
from services.regex_service import RegexService
from services.ner_service import NERService # Import the new NERService

app = FastAPI(
    title="PII FILTER",
    description="API para detecção e mascaramento de PII em português.",
    version="0.1.0",
)

# Initialize services globally or within a dependency injection system
# For simplicity, initializing here. In a larger app, consider FastAPI's Depends.
regex_service = RegexService()
ner_service = NERService() # Initialize NERService

@app.get("/")
def read_root():
    """Simple health check endpoint that returns a welcome message."""
    return {"message": "Welcome to the PII Filter API!"}


@app.post("/process-prompt", response_model=ProcessedResponse)
def process_prompt(request: PromptRequest):
    """
    Processes a text prompt by filtering PII and detecting sensitive topics.

    Steps:
    1. Applies regex-based PII filtering using RegexService.
    2. Applies NER-based PII filtering using NERService.
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

    # --- Step 1: Regex Filter ---
    # This step validates PII data algorithmically (e.g., CPF checksum)
    regex_filtered_text, regex_mapping = regex_service.filter_by_regex(original_text, validate_pii_data=True)
    
    # The text for the next filter is the output of the previous one
    text_after_regex = regex_filtered_text
    pii_masked.extend(regex_mapping)

    # --- Step 2: NER Filter ---
    # NER is applied to the text that has already been processed by regex.
    # This ensures that regex-detectable PII (like CPF, CNPJ) are already masked,
    # and NER focuses on names, locations, organizations, etc.
    ner_filtered_text, ner_mapping = ner_service.filter_by_ner(text_after_regex)
    
    # The final text is the output of the NER filter
    final_processed_text = ner_filtered_text
    pii_masked.extend(ner_mapping) # Add NER mappings to the list

    # --- Next Steps (to be implemented) ---
    # TODO: Call the Topic filter/external LLM
    # TODO: Call the external LLM
    # TODO: De-sanitize the LLM response (using the combined pii_masked list)

    return ProcessedResponse(
        final_response=final_processed_text,
        pii_masked=pii_masked,
        sensitive_topics_detected=sensitive_topics_detected,
    )

