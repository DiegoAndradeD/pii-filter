"""
Factory module for external LLM services.

Provides a helper function `get_llm_service` to instantiate the appropriate
LLM service based on the EXTERNAL_LLM_PROVIDER environment variable.
Defaults to GeminiService if no provider is specified.
"""

import os
import logging

from src.interfaces.external_llm_interface import ExternalLLMInterface
from src.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


def get_llm_service() -> ExternalLLMInterface:
    """
    Factory that instantiates and returns the LLM service based on the
    EXTERNAL_LLM_PROVIDER environment variable.

    Returns GeminiService by default if the variable is not defined.
    """
    provider = os.environ.get("EXTERNAL_LLM_PROVIDER", "gemini").lower()
    logger.info("External LLM provider configured: '%s'", provider)

    if provider == "gemini":
        return GeminiService()
    else:
        logger.error("LLM provider '%s' is not supported.", provider)
        raise ValueError(f"Unknown LLM provider: {provider}")
