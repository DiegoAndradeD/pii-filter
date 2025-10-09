"""
Base module for LLM services.

Defines an abstract BaseLLMService class that implements common logic
for sending prompts with PII-safe context to external LLM services.
"""

import abc
import logging
from typing import Optional
from src.interfaces.external_llm_interface import ExternalLLMInterface

logger = logging.getLogger(__name__)


class BaseLLMService(ExternalLLMInterface, abc.ABC):
    """
    Base class for LLM services.

    Implements the Template Method pattern to inject a PII-safe context
    into all prompts before sending them to the specific service.
    """

    _SYSTEM_PROMPT = """
    Atenção: Você é um assistente de IA. O prompt que você receberá a seguir já foi processado por um sistema de segurança para proteger a privacidade do usuário. Informações Pessoais Identificáveis (PII) foram substituídas por placeholders (ex: [CPF_1], [NOME_2], [EMAIL_3]).

    Suas instruções são:
    1.  Foque exclusivamente no conteúdo da pergunta do usuário e forneça uma resposta direta e útil.
    2.  NÃO comente sobre os placeholders ou sobre o processo de filtragem que ocorreu. Aja como se a pergunta fosse natural.
    3.  É ESSENCIAL que você utilize os mesmos placeholders exatos que recebeu caso precise se referir a eles na sua resposta. Não os altere, não os explique e não gere novos.

    A seguir, o prompt do usuário:
    ---
    """

    def send_prompt(self, prompt: str) -> Optional[str]:
        """
        Final method that adds context and calls the specific implementation.
        Child classes should NOT override this method.
        """
        full_prompt = f"{self._SYSTEM_PROMPT}\n{prompt}"
        logger.info(
            "Sending prompt with system context to the underlying LLM service..."
        )

        return self._send_request(full_prompt)

    @abc.abstractmethod
    def _send_request(self, full_prompt: str) -> Optional[str]:
        """
        Method that child classes must implement to send the full prompt
        (with context) to their specific API.
        """
