"""
Local LLM Service module.

This module provides the `LocalLLMService` class, which integrates with a local
Ollama model to detect and replace sensitive information in text. It extracts
sensitive fragments, replaces them with placeholders, and returns mappings
similar to the RegexService.
"""

import json
import logging
from typing import List, Tuple
import requests
from src.core.constants import SENSITIVE_CATEGORIES
from src.models.models import PIIMapping

logger = logging.getLogger(__name__)


class LocalLLMService:
    """
    Service to find, filter, and replace sensitive topics in text using a local LLM via Ollama.
    It extracts the exact sensitive phrases, replaces them with placeholders,
    and returns mappings, mimicking the RegexService behavior.
    """

    def __init__(
        self, model_name: str = "llama3:8b", host: str = "http://localhost:11434"
    ):
        self.model_name = model_name
        self.api_url = f"{host}/api/generate"
        logger.info(
            "LocalLLMService initialized to use Ollama model '%s' at %s",
            self.model_name,
            host,
        )

    def _build_system_prompt(self) -> str:
        """
        Creates a specialized system prompt for the LLM to perform extraction.
        """

        categories_str = ", ".join(SENSITIVE_CATEGORIES)

        return (
            "Você é um especialista em LGPD e RH. Sua tarefa é analisar o texto e EXTRAIR os trechos exatos "
            "que correspondem às seguintes categorias de dados sensíveis e PII contextuais: "
            f"{categories_str}. "
            "Retorne APENAS um objeto JSON com uma chave 'sensitive_fragments', que contém uma lista de objetos. "
            'Cada objeto deve ter duas chaves: "category" (a categoria identificada da lista) e "exact_text" '
            "(o trecho de texto exato que você encontrou). "
            "NÃO extraia PIIs de padrão óbvio como CPF, RG, E-mail, Telefone ou CEP (eles são tratados por outro sistema). "
            "Foque em extrair o CONTEXTO sensível (ex: CONDIÇÃO_DE_SAUDE) e PIIs contextuais (ex: CARGO, SALARIO, ENDERECO_LOGRADOURO, MATRICULA, NOME_DEPENDENTE, CNH, PASSAPORTE). "
            "Se nada for encontrado, retorne uma lista vazia. "
            'Exemplo de resposta: {"sensitive_fragments": [{"category": "CONDIÇÃO_DE_SAUDE", "exact_text": "diagnosticado com TDAH"}, {"category": "CARGO", "exact_text": "Técnico de Manutenção Jr"}]}. '
            "Não adicione explicações ou qualquer texto fora do JSON."
        )

    def _find_placeholder_spans(
        self, text: str, placeholders: List[str]
    ) -> List[Tuple[int, int]]:
        """Helper to find all spans of existing placeholders."""
        placeholder_spans = []
        unique_placeholders = set(placeholders or [])
        if not unique_placeholders:
            return []

        for placeholder in unique_placeholders:
            start = 0
            while True:
                pos = text.find(placeholder, start)
                if pos == -1:
                    break
                placeholder_spans.append((pos, pos + len(placeholder)))
                start = pos + 1
        return placeholder_spans

    def filter_sensitive_topics(
        self, text: str, existing_placeholders: List[str] = None
    ) -> Tuple[str, List[PIIMapping]]:
        """
        Finds and filters sensitive topic phrases from a text using the LLM.
        Avoids filtering text that is already inside an existing placeholder.
        """
        if not text:
            return text, []

        system_prompt = self._build_system_prompt()
        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "prompt": text,
            "format": "json",
            "stream": False,
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=90)
            response.raise_for_status()

            response_content = response.json().get("response", "{}")
            data = json.loads(response_content)

            fragments = data.get("sensitive_fragments", [])

            if not isinstance(fragments, list):
                logger.warning(
                    "LLM returned fragments in a non-list format: %s", fragments
                )
                return text, []

            placeholder_spans = self._find_placeholder_spans(
                text, existing_placeholders
            )

            return self._replace_fragments_with_placeholders(
                text, fragments, placeholder_spans
            )

        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logger.error("Error interacting with Ollama or parsing its response: %s", e)
            return text, []

    def _replace_fragments_with_placeholders(
        self,
        text: str,
        fragments: List[dict],
        placeholder_spans: List[Tuple[int, int]] = None,
    ) -> Tuple[str, List[PIIMapping]]:
        """
        Replaces extracted text fragments with placeholders and creates mappings.
        Skips fragments that overlap with existing placeholder spans.
        """
        modified_text = text
        mappings_found: List[PIIMapping] = []
        if placeholder_spans is None:
            placeholder_spans = []

        found_fragments = []
        for frag in fragments:
            exact_text = frag.get("exact_text")
            category = frag.get("category")
            if not exact_text or not category:
                continue

            start_pos = text.find(exact_text)
            if start_pos == -1:
                logger.warning(
                    "LLM fragment '%s' not found in original text. Skipping.",
                    exact_text,
                )
                continue

            end_pos = start_pos + len(exact_text)
            overlaps = False
            for ph_start, ph_end in placeholder_spans:
                if start_pos < ph_end and end_pos > ph_start:
                    overlaps = True
                    logger.debug(
                        "Skipping LLM fragment '%s' as it overlaps with an existing placeholder.",
                        exact_text,
                    )
                    break

            if overlaps:
                continue

            frag["start_pos"] = start_pos
            found_fragments.append(frag)

        found_fragments.sort(key=lambda x: x["start_pos"], reverse=True)

        counts = {}
        for fragment in found_fragments:
            pii_type = fragment["category"]
            original_value = fragment["exact_text"]
            start = fragment["start_pos"]
            end = start + len(original_value)

            counts[pii_type] = counts.get(pii_type, 0) + 1
            placeholder = f"[{pii_type}_{counts[pii_type]}]"

            mapping = PIIMapping(
                placeholder=placeholder,
                original_value=original_value,
                type=pii_type,
                span=(start, end),
            )
            mappings_found.append(mapping)

            modified_text = modified_text[:start] + placeholder + modified_text[end:]

        mappings_found.reverse()
        return modified_text, mappings_found
