"""
API router for processing prompts with PII detection, sensitive topic analysis,
external LLM interaction, and PII restoration. Responses and logs are streamed
to the client via Server-Sent Events (SSE).

This module defines dependency providers for FastAPI, a streaming generator
for orchestration, and the endpoint for processing prompts.
"""

import asyncio
from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse

from src.api.proxy_service import ProxyService
from src.core.llm_factory import get_llm_service
from src.interfaces.proxy_service_interface import (
    IExternalLLM,
    IRegexService,
    IRestorationService,
    ISensitiveTopicDetector,
    INERService,
)
from src.services.regex_service import RegexService
from src.services.local_llm_service import LocalLLMService
from src.services.restoration_service import RestorationService
from src.services.ner_service import NERService
from src.models.models import ProcessedResponse
from src.utils.sse_utils import create_sse_event

router = APIRouter()


def get_regex_service() -> IRegexService:
    """Provides a concrete implementation of IRegexService."""
    return RegexService()


def get_sensitive_topic_detector() -> ISensitiveTopicDetector:
    """Provides a concrete implementation of ISensitiveTopicDetector."""
    return LocalLLMService()


def get_ner_service() -> INERService:  # <-- ADICIONAR ESTA FUNÇÃO
    """Provides a concrete implementation of INERService."""
    # The NERService may fail to load the spaCy model.
    # Ideally, this would be a Singleton handled at app startup.
    # For now, we instantiate it directly.
    try:
        return NERService()
    except RuntimeError as e:
        # If the spaCy model cannot be loaded, the app should not
        # accept this dependency.
        print(f"CRITICAL ERROR: Failed to initialize NERService. {e}")
        raise e


def get_external_llm() -> IExternalLLM:
    """Provides a concrete instance of an external LLM via the factory."""
    return get_llm_service()


def get_restoration_service() -> IRestorationService:
    """Provides a concrete implementation of IRestorationService."""
    return RestorationService()


def get_proxy_service(
    regex_service: IRegexService = Depends(get_regex_service),
    ner_service: INERService = Depends(get_ner_service),
    sensitive_topic_detector: ISensitiveTopicDetector = Depends(
        get_sensitive_topic_detector
    ),
    external_llm: IExternalLLM = Depends(get_external_llm),
    restoration_service: IRestorationService = Depends(get_restoration_service),
) -> ProxyService:
    """
    Constructs a ProxyService with all dependencies injected via FastAPI.

    Args:
        regex_service (IRegexService): Regex-based PII detection service.
        sensitive_topic_detector (ISensitiveTopicDetector): Sensitive topic detection service.
        external_llm (IExternalLLM): External LLM service.
        restoration_service (IRestorationService): Service for restoring PII.

    Returns:
        ProxyService: Fully initialized proxy service.
    """
    return ProxyService(
        regex_service=regex_service,
        ner_service=ner_service,
        sensitive_topic_detector=sensitive_topic_detector,
        external_llm=external_llm,
        restoration_service=restoration_service,
    )


async def stream_generator(original_text: str, proxy_service: ProxyService):
    """
    SSE generator that orchestrates the PII/sensitive topic detection
    workflow, external LLM call, and PII restoration using ProxyService.

    Args:
        original_text (str): The prompt text to process.
        proxy_service (ProxyService): The orchestrating service.

    Yields:
        str: Server-Sent Event formatted messages including logs and final response.
    """
    # Step 0: Start
    yield create_sse_event(
        {"type": "log", "message": "Prompt received. Starting processing..."}
    )
    await asyncio.sleep(0.5)

    # Step 1: PII detection with regex
    regex_filtered_text, regex_mappings, pii_events = (
        await proxy_service.detect_pii_with_regex(original_text)
    )
    for event in pii_events:
        yield event
    await asyncio.sleep(0.5)

    # Step 2: PII detection with NER
    ner_filtered_text, ner_mappings, ner_events = (
        await proxy_service.detect_pii_with_ner(
            regex_filtered_text, [m.placeholder for m in regex_mappings]
        )
    )
    for event in ner_events:
        yield event
    await asyncio.sleep(0.5)

    # Step 3: Sensitive topic detection using LLM
    llm_filtered_text, llm_mappings, topic_events = (
        await proxy_service.detect_sensitive_topics(ner_filtered_text)
    )
    for event in topic_events:
        yield event
    await asyncio.sleep(0.5)

    yield create_sse_event(
        {
            "type": "log",
            "message": f"Final filtered text (sending to external LLM)\n{llm_filtered_text}",
        }
    )

    # Step 4: External LLM call
    # Skipping the external LLM call to avoid extra costs and because we are on the free plan.
    # Uncomment the following lines if you want to enable external LLM:
    llm_external_response, llm_events = await proxy_service.call_external_llm(
        llm_filtered_text
    )
    for event in llm_events:
        yield event

    # Using local output as external LLM output placeholder
    # llm_external_response = llm_filtered_text
    # yield create_sse_event(
    #     {"type": "log", "message": "Skipping external LLM call (free plan)."}
    # )
    await asyncio.sleep(0.5)

    # Step 4: PII restoration
    final_response_text, restore_events = await proxy_service.restore_pii(
        llm_external_response, regex_mappings, ner_mappings, llm_mappings
    )
    for event in restore_events:
        yield event
    await asyncio.sleep(0.5)

    # Step 5: Send final response
    all_pii_masked = sorted(
        regex_mappings + ner_mappings + llm_mappings, key=lambda m: m.span[0]
    )
    final_payload = ProcessedResponse(
        final_response=final_response_text,
        pii_masked=all_pii_masked,
        sensitive_topics_detected=[m.type for m in llm_mappings],
    )
    yield create_sse_event(
        {"type": "final_response", "payload": final_payload.model_dump()}
    )


@router.post("/process-prompt-stream")
async def process_prompt_stream(
    request: Request,
    proxy_service: ProxyService = Depends(get_proxy_service),
):
    """
    Endpoint to process a prompt and stream logs and final response via SSE.

    The orchestration logic is delegated to ProxyService, which handles
    PII detection, sensitive topic analysis, LLM calls, and PII restoration.

    Args:
        request (Request): FastAPI request object containing the JSON payload.
        proxy_service (ProxyService): Injected ProxyService instance.

    Returns:
        StreamingResponse: SSE stream of logs and the final processed response.
    """
    body = await request.json()
    original_text = body.get("original_prompt", "")

    return StreamingResponse(
        stream_generator(original_text, proxy_service), media_type="text/event-stream"
    )
