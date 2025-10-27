"""
External LLM Interface module.

Defines the abstract contract for any external LLM service implementation.
All concrete LLM services must implement this interface to ensure
compatibility with the application.
"""

import abc
from typing import Optional


class ExternalLLMInterface(abc.ABC):
    """
    Interface (contract) for any external LLM service.

    Defines the essential methods that an LLM service implementation
    must provide to be compatible with the application.
    """

    @abc.abstractmethod
    def send_prompt(self, prompt: str) -> Optional[str]:
        """
        Sends a prompt to the language model and returns its response.

        Args:
            prompt (str): The text prompt to send to the LLM.

        Returns:
            Optional[str]: The LLM's response as a string, or an error message
                           if communication fails or content is blocked.
        """
