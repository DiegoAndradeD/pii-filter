"""
Gemini LLM Service implementation.

Provides a concrete implementation of BaseLLMService to interact with
Google's Gemini API.
"""

import logging
import os
from typing import Optional
from google.api_core import exceptions
import google.generativeai as genai

from src.services.base_llm_service import BaseLLMService

logger = logging.getLogger(__name__)


class GeminiService(BaseLLMService):
    """
    Concrete implementation of BaseLLMService for Google Gemini.
    Context injection is handled by the base class.
    """

    def __init__(self, model_name: str = "models/gemini-2.5-flash"):
        self.logger = logger
        self.model_name = model_name
        self.model = None

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.logger.critical("Environment variable GEMINI_API_KEY is not set.")
            raise ValueError("Gemini API key not found.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)
        self.logger.info(
            "GeminiService successfully initialized for model '%s'.", self.model_name
        )

    def _send_request(self, full_prompt: str) -> Optional[str]:
        """
        Sends the context-injected prompt to the Gemini API and returns the response text.
        """
        if not self.model:
            self.logger.error("Gemini model has not been initialized.")
            return "Error: External LLM service is not configured."

        try:
            response = self.model.generate_content(full_prompt)

            if not response.parts:
                self.logger.warning(
                    "Gemini response was blocked. Finish reason: %s",
                    response.prompt_feedback.block_reason,
                )
                return "Your request could not be processed due to security policies."

            self.logger.info("Successfully received response from Gemini.")
            return response.text

        except exceptions.GoogleAPIError as err:
            self.logger.exception("A Google API error occurred: %s", err)
            return "Sorry, there was an issue communicating with the Gemini API."

        except (AttributeError, ValueError, TypeError) as err:
            logger.exception(
                "Unexpected error while processing Gemini response: %s", err
            )
            return "Sorry, an unexpected error occurred while processing the response."
