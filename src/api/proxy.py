"""
API endpoint for processing user prompts with PII detection, sensitive topic analysis,
and restoration using regex and local LLM services. Streams logs and final response via SSE.
"""

import asyncio
import json
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from src.services.regex_service import RegexService
from src.services.ner_service import NERService
from src.services.local_llm_service import LocalLLMService
from src.services.restoration_service import RestorationService
from src.models.models import ProcessedResponse

router = APIRouter()


@router.post("/process-prompt-stream")
async def process_prompt_stream(request: Request):
    """
    Processes the incoming prompt and streams logs and the final response to the client
    via Server-Sent Events (SSE).

    Steps:
        1. Detect PII using regex
        2. Detect sensitive topics using a local LLM
        3. Simulate an external LLM call
        4. Restore original PII in the response
    """
    body = await request.json()
    original_text = body.get("original_prompt", "")

    async def stream_generator():
        """
        Async generator function to yield SSE events as the processing progresses.
        """
        regex_service = RegexService()
        ner_service = NERService()
        llm_service = LocalLLMService()
        restoration_service = RestorationService()

        def create_sse_event(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        # --- Step 0: Start Processing ---
        yield create_sse_event(
            {"type": "log", "message": "Prompt received. Starting processing..."}
        )
        await asyncio.sleep(0.5)

        # --- Step 1: Regex-based PII Filtering ---
        yield create_sse_event(
            {"type": "log", "message": "Detecting PII using regex..."}
        )
        await asyncio.sleep(0.5)
        regex_filtered_text, regex_mappings = regex_service.filter_by_regex(
            original_text, validate_pii_data=False
        )
        processed_text = regex_filtered_text

        if regex_mappings:
            for mapping in regex_mappings:
                yield create_sse_event(
                    {
                        "type": "log",
                        "message": f"   - PII detected: '{mapping.original_value}' "
                        f"of type {mapping.type} at position {mapping.span}",
                    }
                )
        else:
            yield create_sse_event(
                {"type": "log", "message": "   - No PII detected by regex."}
            )

        yield create_sse_event(
            {
                "type": "log",
                "message": f"   - Total PIIs detected by regex: {len(regex_mappings)}",
            }
        )
        await asyncio.sleep(0.5)

        # --- Step 2: NER-based PII Filtering ---
        yield create_sse_event(
            {"type": "log", "message": "Detecting PII using Named Entity Recognition..."}
        )
        await asyncio.sleep(0.5)
        
        # Pass existing placeholders to avoid conflicts
        existing_placeholders = [mapping.placeholder for mapping in regex_mappings]
        ner_filtered_text, ner_mappings = ner_service.filter_by_ner(
            processed_text, existing_placeholders=existing_placeholders
        )
        processed_text = ner_filtered_text

        if ner_mappings:
            for mapping in ner_mappings:
                yield create_sse_event(
                    {
                        "type": "log",
                        "message": f"   - NER PII detected: '{mapping.original_value}' "
                        f"of type {mapping.type} at position {mapping.span}",
                    }
                )
        else:
            yield create_sse_event(
                {"type": "log", "message": "   - No PII detected by NER."}
            )

        yield create_sse_event(
            {
                "type": "log",
                "message": f"   - Total PIIs detected by NER: {len(ner_mappings)}",
            }
        )
        await asyncio.sleep(0.5)

        # --- Step 3: LLM-based Sensitive Topic Filtering ---
        yield create_sse_event(
            {"type": "log", "message": "Detecting sensitive topics using LLM..."}
        )
        await asyncio.sleep(0.5)
        llm_filtered_text, llm_mappings = llm_service.filter_sensitive_topics(
            processed_text
        )
        processed_text = llm_filtered_text

        if llm_mappings:
            for mapping in llm_mappings:
                yield create_sse_event(
                    {
                        "type": "log",
                        "message": f"   - Sensitive topic detected: '{mapping.original_value}' "
                        f"of type {mapping.type} at position {mapping.span}",
                    }
                )
        else:
            yield create_sse_event(
                {"type": "log", "message": "   - No sensitive topics detected by LLM."}
            )

        yield create_sse_event(
            {
                "type": "log",
                "message": f"   - Total sensitive topics detected: {len(llm_mappings)}",
            }
        )
        await asyncio.sleep(0.5)

        # --- Step 4: Simulated External LLM Call ---
        # TODO: Implement the call to a external LLM
        yield create_sse_event(
            {"type": "log", "message": "Calling external LLM (simulation)..."}
        )
        await asyncio.sleep(0.8)
        llm_external_response = processed_text
        yield create_sse_event(
            {"type": "log", "message": "   - External LLM response received."}
        )
        await asyncio.sleep(0.5)

        # --- Step 5: Restoration of Original PII ---
        yield create_sse_event(
            {"type": "log", "message": "Restoring PII in final response..."}
        )
        await asyncio.sleep(0.5)

        yield create_sse_event(
            {
                "type": "log",
                "message": f"   - Text before restoration:\n{llm_external_response}",
            }
        )
        await asyncio.sleep(0.5)

        all_pii_masked = regex_mappings + ner_mappings + llm_mappings
        all_pii_masked.sort(key=lambda m: m.span[0])
        restoration_data = restoration_service.create_restoration_data(
            regex_mappings=regex_mappings, ner_mappings=ner_mappings, llm_mappings=llm_mappings
        )
        final_response_text = restoration_service.restore_all(
            llm_external_response, restoration_data
        )

        yield create_sse_event(
            {"type": "log", "message": "   - PII successfully restored."}
        )
        await asyncio.sleep(0.5)

        # --- Step 6: Send Final Log ---
        final_payload = ProcessedResponse(
            final_response=final_response_text,
            pii_masked=all_pii_masked,
            sensitive_topics_detected=[m.type for m in llm_mappings],
        )
        yield create_sse_event(
            {"type": "final_response", "payload": final_payload.model_dump()}
        )

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
