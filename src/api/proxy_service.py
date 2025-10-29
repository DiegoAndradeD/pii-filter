"""
Proxy service module.

This module defines the ProxyService class, which orchestrates the process of
detecting, filtering, and restoring Personally Identifiable Information (PII)
in text data. It integrates multiple services, such as regex-based detection,
sensitive topic detection, external LLM processing, and text restoration.
"""

import asyncio
from typing import List, Tuple

from src.interfaces.proxy_service_interface import (
    IExternalLLM,
    IRegexService,
    IRestorationService,
    ISensitiveTopicDetector,
    INERService,
)
from src.models.models import PIIMapping
from src.utils.sse_utils import create_sse_event


class ProxyService:
    """
    Coordinates the detection, filtering, and restoration of
    Personally Identifiable Information (PII).
    Dependencies are injected to promote low coupling and improve testability.
    """

    def __init__(
        self,
        regex_service: IRegexService,
        ner_service: INERService,
        sensitive_topic_detector: ISensitiveTopicDetector,
        external_llm: IExternalLLM,
        restoration_service: IRestorationService,
    ):
        """
        Initializes the ProxyService with its required dependencies.

        Args:
            regex_service (IRegexService): Service responsible for PII detection
            using regex patterns.
            sensitive_topic_detector (ISensitiveTopicDetector): Service to detect
            sensitive topics using local models.
            external_llm (IExternalLLM): External Large Language Model service.
            restoration_service (IRestorationService): Service that restores masked
            PII into processed text.
        """
        self.regex_service = regex_service
        self.ner_service = ner_service
        self.sensitive_topic_detector = sensitive_topic_detector
        self.external_llm = external_llm
        self.restoration_service = restoration_service

    async def detect_pii_with_regex(
        self, original_text: str
    ) -> Tuple[str, List[PIIMapping], List[str]]:
        """
        Detects PII using regex patterns and returns the filtered text,
        detected mappings, and event logs.

        Args:
            original_text (str): The original input text to analyze.

        Returns:
            Tuple[str, List[PIIMapping], List[str]]: A tuple containing:
                - The text with PII filtered.
                - A list of detected PII mappings.
                - A list of Server-Sent Events (SSE) log messages.
        """
        events = [
            create_sse_event({"type": "log", "message": "Detecting PII using regex..."})
        ]

        # Detect and filter PII in the text
        filtered_text, mappings = self.regex_service.filter_by_regex(
            original_text, validate_pii_data=True
        )

        # Log detection results
        if mappings:
            for m in mappings:
                events.append(
                    create_sse_event(
                        {
                            "type": "log",
                            "message": f"   - PII detected: '{m.original_value}' of type {m.type} at position {m.span}",
                        }
                    )
                )
        else:
            events.append(
                create_sse_event(
                    {"type": "log", "message": "   - No PII detected by regex."}
                )
            )

        events.append(
            create_sse_event(
                {"type": "log", "message": f"   - Total PIIs detected: {len(mappings)}"}
            )
        )
        return filtered_text, mappings, events

    async def detect_pii_with_ner(
        self, text: str, existing_placeholders: List[str]
    ) -> Tuple[str, List[PIIMapping], List[str]]:
        """
        Detects PII using NER models and returns the filtered text,
        detected mappings, and event logs.

        Args:
            text (str): The text to analyze (already processed by regex).
            existing_placeholders (List[str]): Placeholders from regex step.

        Returns:
            Tuple[str, List[PIIMapping], List[str]]: A tuple containing:
                - The text with NER PIIs filtered.
                - A list of detected NER mappings.
                - A list of Server-Sent Events (SSE) log messages.
        """
        events = [
            create_sse_event(
                {"type": "log", "message": "Detecting PII using NER (spaCy)..."}
            )
        ]

        # Detect and filter PII in the text
        # We use asyncio.to_thread because spaCy (NERService) is synchronous and can
        # block the event loop.
        filtered_text, mappings = await asyncio.to_thread(
            self.ner_service.filter_by_ner, text, existing_placeholders
        )

        # Log detection results
        if mappings:
            for m in mappings:
                events.append(
                    create_sse_event(
                        {
                            "type": "log",
                            "message": f"   - NER PII detected: '{m.original_value}' of type {m.type}",
                        }
                    )
                )
        else:
            events.append(
                create_sse_event(
                    {"type": "log", "message": "   - No new PII detected by NER."}
                )
            )

        events.append(
            create_sse_event(
                {
                    "type": "log",
                    "message": f"   - Total NER PIIs detected: {len(mappings)}",
                }
            )
        )
        return filtered_text, mappings, events

    async def detect_sensitive_topics(
        self, text: str
    ) -> Tuple[str, List[PIIMapping], List[str]]:
        """
        Detects sensitive topics in the text using a local LLM-based model.

        Args:
            text (str): The text to analyze for sensitive content.

        Returns:
            Tuple[str, List[PIIMapping], List[str]]: A tuple containing:
                - The filtered text with sensitive topics replaced.
                - A list of detected sensitive topic mappings.
                - A list of Server-Sent Events (SSE) log messages.
        """
        events = [
            create_sse_event(
                {"type": "log", "message": "Detecting sensitive topics using LLM..."}
            )
        ]

        # Detect sensitive topics
        filtered_text, mappings = self.sensitive_topic_detector.filter_sensitive_topics(
            text
        )

        # Log detection results
        if mappings:
            for m in mappings:
                events.append(
                    create_sse_event(
                        {
                            "type": "log",
                            "message": f"   - Sensitive topic detected: '{m.original_value}' of type {m.type} at position {m.span}",
                        }
                    )
                )
        else:
            events.append(
                create_sse_event(
                    {
                        "type": "log",
                        "message": "   - No sensitive topics detected by LLM.",
                    }
                )
            )

        events.append(
            create_sse_event(
                {
                    "type": "log",
                    "message": f"   - Total sensitive topics detected: {len(mappings)}",
                }
            )
        )
        return filtered_text, mappings, events

    async def call_external_llm(self, processed_text: str) -> Tuple[str, List[str]]:
        """
        Sends the processed text to an external LLM and returns the response with event logs.

        Args:
            processed_text (str): The text after PII filtering and sensitive topic removal.

        Returns:
            Tuple[str, List[str]]: A tuple containing:
                - The raw LLM response text.
                - A list of Server-Sent Events (SSE) log messages.
        """
        events = [
            create_sse_event(
                {
                    "type": "log",
                    "message": f"Calling external LLM ({self.external_llm.__class__.__name__})...",
                }
            )
        ]

        # Execute the LLM request in a separate thread to avoid blocking the event loop
        llm_response = await asyncio.to_thread(
            self.external_llm.send_prompt, processed_text
        )

        # Log the LLM response
        events.append(
            create_sse_event(
                {"type": "log", "message": "   - External LLM response received."}
            )
        )
        events.append(
            create_sse_event(
                {
                    "type": "log",
                    "message": f"   - LLM Response (before restoration):\n{llm_response}",
                }
            )
        )
        return llm_response, events

    async def restore_pii(
        self,
        llm_response: str,
        regex_mappings: List,
        ner_mappings: List,
        llm_mappings: List,
    ) -> Tuple[str, List[str]]:
        """
        Restores original PII values into the final LLM response and returns
        the restored text with event logs.

        Args:
            llm_response (str): The LLM output with masked placeholders.
            regex_mappings (List): PII mappings detected by regex.
            ner_mappings (List): PII mappings detected by NER. # <-- ADICIONAR
            llm_mappings (List): PII or sensitive topic mappings detected by the local LLM.

        Returns:
            Tuple[str, List[str]]: A tuple containing:
                - The final response text with original PII restored.
                - A list of Server-Sent Events (SSE) log messages.
        """
        events = [
            create_sse_event(
                {"type": "log", "message": "Restoring PII in final response..."}
            )
        ]
        events.append(
            create_sse_event(
                {
                    "type": "log",
                    "message": f"   - Text before restoration:\n{llm_response}",
                }
            )
        )

        # Generate restoration data and restore all PII placeholders
        restoration_data = self.restoration_service.create_restoration_data(
            regex_mappings=regex_mappings,
            ner_mappings=ner_mappings,
            llm_mappings=llm_mappings,
        )
        final_response_text = self.restoration_service.restore_all(
            llm_response, restoration_data
        )

        # Log restoration completion
        events.append(
            create_sse_event(
                {"type": "log", "message": "   - PII successfully restored."}
            )
        )
        return final_response_text, events
