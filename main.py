from fastapi import FastAPI

from filters.regex_filter import filter_by_regex
from models import PIIMapping, ProcessedResponse, PromptRequest

app = FastAPI(
    title="PII FILTER",
    description="",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "Welcome"}


@app.post("/process-prompt", response_model=ProcessedResponse)
def process_prompt(request: PromptRequest):
    original_text = request.original_prompt
    pii_masked: list[PIIMapping] = []
    sensitive_topics_detected: list[str] = []

    # --- Step 1: Regex Filter ---
    # Applies the regex filter and collects the results
    regex_filtered_text, regex_mapping = filter_by_regex(original_text)
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
