"""
Service for filtering and restoring PII in text using Named Entity Recognition (NER).
"""

import logging
from typing import Dict, List, Tuple, Any
import spacy


from src.models.models import PIIMapping

logger = logging.getLogger(__name__)


class NERService:
    """
    Service to find, filter, and restore PII from text using Named Entity Recognition.

    This class encapsulates the logic for:
        1. Finding professions (via EntityRuler) and named entities (people, organizations, places) using spaCy.
        2. Converting entities into PII mappings with placeholders.
        3. Filtering text by replacing entities with placeholders.
        4. Restoring the original text from the filtered text and the map.
    """

    _ENTITY_TYPE_MAPPING: Dict[str, str] = {
        "PERSON": "NOME_PESSOA",
        "PER": "NOME_PESSOA",
        "ORG": "ORGANIZACAO",
        "EVENT": "EVENTO",
        "WORK_OF_ART": "OBRA_ARTE",
        "LAW": "LEI",
        "LANGUAGE": "IDIOMA",
        "PROFISSAO": "PROFISSAO",
    }

    _FALSE_POSITIVES: set = {
        "oi",
        "olá",
        "ei",
        "bom dia",
        "boa tarde",
        "boa noite",
        "use",
        "cpf",
        "cnpj",
        "email",
        "telefone",
        "rg",
        "cep",
        "clt",
        "cnh",
        "ip",
        "mac",
        "mac address",
        "endereço",
        "detalhes",
        "fraude",
        "evidências",
        "digitais",
        "informações",
        "adicionais",
        "cúmplices",
        "dados",
        "contato",
        "documentos",
        "cargo",
        "departamento",
        "matrícula",
        "salário",
        "investigação",
        "relatório",
        "confidencial",
        "operação",
        "assunto",
        "urgente",
        "funcionário",
        "principal",
        "sr",
        "sra",
        "dr",
        "rh",
        "ti",
    }

    # Lista de profissões para o EntityRuler
    _PROFESSION_PATTERNS: List[Dict[str, Any]] = [
        {"label": "PROFISSAO", "pattern": "analista de sistemas"},
        {"label": "PROFISSAO", "pattern": "engenheiro de software"},
        {"label": "PROFISSAO", "pattern": "gerente de projetos"},
        {"label": "PROFISSAO", "pattern": "médico"},
        {"label": "PROFISSAO", "pattern": "advogado"},
        {"label": "PROFISSAO", "pattern": "professor"},
        {"label": "PROFISSAO", "pattern": "técnico em enfermagem"},
        {"label": "PROFISSAO", "pattern": "técnico de"},
        {"label": "PROFISSAO", "pattern": "analista"},
        {"label": "PROFISSAO", "pattern": "gerente"},
        {"label": "PROFISSAO", "pattern": "coordenador"},
        {"label": "PROFISSAO", "pattern": "diretor"},
        {"label": "PROFISSAO", "pattern": "supervisor"},
        {"label": "PROFISSAO", "pattern": "assistente"},
        {"label": "PROFISSAO", "pattern": "estagiário"},
        {"label": "PROFISSAO", "pattern": "consultor"},
        {"label": "PROFISSAO", "pattern": "desenvolvedor"},
    ]

    def __init__(self, model_name: str = "pt_core_news_lg"):
        """
        Inicializa o NER Service.

        Args:
            model_name: Nome do modelo spaCy em português.
                        Recomenda-se "pt_core_news_lg" para melhor precisão.
        """
        self.logger = logger
        self.model_name = model_name
        self.nlp = None

        try:
            # Carrega o modelo spaCy
            self.nlp = spacy.load(model_name)
            self.logger.info("Loaded spaCy model: %s", model_name)

            # --- NOVO: Adicionar EntityRuler para Profissões ---
            # Adiciona o 'entity_ruler' ao pipeline ANTES do 'ner'
            if "entity_ruler" not in self.nlp.pipe_names:
                ruler = self.nlp.add_pipe("entity_ruler", before="ner")
                ruler.add_patterns(self._PROFESSION_PATTERNS)
                self.logger.info(
                    "Added EntityRuler with %d profession patterns.",
                    len(self._PROFESSION_PATTERNS),
                )
            else:
                self.logger.warning("EntityRuler already exists in pipeline.")
            # --- FIM DO NOVO ---

        except OSError as e:
            # "Fail-fast": Se o modelo não puder ser carregado, o serviço
            # deve falhar explicitamente em vez de operar em modo degradado.
            self.logger.critical(
                "Could not load spaCy model '%s'. NER Service will be disabled. Error: %s",
                model_name,
                e,
            )
            # Lança uma exceção clara para quem estiver inicializando o serviço
            raise RuntimeError(f"Failed to load spaCy model '{model_name}'.") from e

        self.logger.info(
            "NER Service initialized with pipeline: %s", self.nlp.pipe_names
        )

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extrai entidades nomeadas do texto usando spaCy.

        Args:
            text: Texto de entrada para analisar

        Returns:
            Lista de dicionários de entidades com tipo, valor e informações de span
        """
        if not self.nlp:
            self.logger.warning("NER NLP model is not loaded. Skipping extraction.")
            return []

        entities = []

        try:
            doc = self.nlp(text)

            for ent in doc.ents:
                pii_type = self._ENTITY_TYPE_MAPPING.get(
                    ent.label_, f"ENTIDADE_{ent.label_}"
                )

                ent_text = ent.text.strip()
                ent_text_lower = ent_text.lower()

                # --- Filtros/Heurísticas Simplificados ---

                # 1. Filtrar entidades muito curtas
                if len(ent_text) < 3:
                    continue

                # 2. Pular entidades que são apenas números
                if ent_text.isdigit():
                    continue

                # 3. Pular falsos positivos conhecidos
                if ent_text_lower in self._FALSE_POSITIVES:
                    continue

                # 4. Pular entidades que parecem placeholders
                if (
                    "[" in ent_text
                    or "]" in ent_text
                    or "_" in ent_text
                    or (
                        ent_text.isupper() and len(ent_text) > 4
                    )  # Muitas siglas (ex: CLT) já estão nos falsos positivos
                ):
                    continue

                # 5. Pular entidades que contêm números mas não são nomes válidos
                if any(
                    c.isdigit() for c in ent_text
                ) and not self._is_valid_name_with_numbers(ent_text):
                    if (
                        pii_type != "LEI" and pii_type != "EVENTO"
                    ):  # Permite números em LEI/EVENTO
                        continue

                # 6. Remover validação por tipo (ex: _is_valid_entity_for_type)
                #    Confiamos mais no modelo 'large' e no EntityRuler.

                entities.append(
                    {
                        "type": pii_type,
                        "value": ent_text,
                        "span": (ent.start_char, ent.end_char),
                        "spacy_label": ent.label_,
                    }
                )

                self.logger.debug(
                    "Entity detected: '%s' (%s -> %s) at span (%s, %s)",
                    ent.text,
                    ent.label_,
                    pii_type,
                    ent.start_char,
                    ent.end_char,
                )

        except (ValueError, TypeError) as e:
            self.logger.error("Error extracting entities: %s", e, exc_info=True)

        return entities

    def _extract_entities_avoiding_placeholders(
        self, text: str, placeholders: List[str]
    ) -> List[Dict[str, Any]]:
        """Extrai entidades evitando áreas que já são placeholders."""

        # Encontra todas as posições de placeholders
        placeholder_spans = []
        for placeholder in placeholders:
            start = 0
            while True:
                pos = text.find(placeholder, start)
                if pos == -1:
                    break
                placeholder_spans.append((pos, pos + len(placeholder)))
                start = pos + 1

        all_entities = self._extract_entities(text)

        # Filtra entidades que se sobrepõem a placeholders
        filtered_entities = []
        for entity in all_entities:
            entity_start, entity_end = entity["span"]

            # Verifica se a entidade se SOBREPÕE a qualquer placeholder
            overlaps = False
            for ph_start, ph_end in placeholder_spans:
                # Lógica de sobreposição correta (sem buffer)
                if entity_start < ph_end and entity_end > ph_start:
                    overlaps = True
                    break

            if not overlaps:
                filtered_entities.append(entity)
            else:
                self.logger.debug(
                    "Skipping entity '%s' as it overlaps with an existing placeholder.",
                    entity["value"],
                )

        return filtered_entities

    def _is_valid_name_with_numbers(self, text: str) -> bool:
        """Verifica se o texto com números é um nome válido (ex: 'João II')."""
        text_clean = text.lower().strip()
        # Permite numerais romanos e títulos comuns
        valid_patterns = [" ii", " iii", " iv", " v", " jr", " sr", " filho", " neto"]
        return any(text_clean.endswith(pattern) for pattern in valid_patterns)

    def _filter_overlapping_entities(
        self, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filtra entidades sobrepostas, mantendo as mais longas.
        Se o EntityRuler e o NER encontrarem a mesma coisa, esta função
        ajuda a resolver o conflito.
        """
        if not entities:
            return []

        # Ordena por posição inicial, e depois por comprimento (do maior para o menor)
        entities.sort(key=lambda x: (x["span"][0], -(x["span"][1] - x["span"][0])))

        filtered_entities = []
        last_end = -1

        for entity in entities:
            start, end = entity["span"]

            # Se esta entidade não se sobrepõe à última mantida, guarde-a
            if start >= last_end:
                filtered_entities.append(entity)
                last_end = end

        return filtered_entities

    def filter_by_ner(
        self,
        text: str,
        existing_placeholders: List[str] = None,
    ) -> Tuple[str, List[PIIMapping]]:
        """
        Filtra PII do texto usando Reconhecimento de Entidade Nomeada.

        Args:
            text: Texto de entrada para filtrar.
            existing_placeholders: Lista de placeholders existentes para evitar
                                     conflitos (ex: do filtro Regex).

        Returns:
            Tupla de (texto_filtrado, lista_de_mapeamentos_pii)
        """
        if not text.strip() or not self.nlp:
            return text, []

        if existing_placeholders:
            entities = self._extract_entities_avoiding_placeholders(
                text, existing_placeholders
            )
        else:
            entities = self._extract_entities(text)

        # Remove entidades sobrepostas (ex: "Gerente" e "Gerente de Projetos")
        # Mantém a mais longa ("Gerente de Projetos")
        entities = self._filter_overlapping_entities(entities)

        if not entities:
            self.logger.info("No new entities detected by NER")
            return text, []

        # --- INÍCIO DA CORREÇÃO ---

        # 1. Contagem total (passagem em ordem de aparição)
        # Conta quantas entidades de cada tipo existem no total.
        type_counts: Dict[str, int] = {}
        for entity in entities:
            pii_type = entity["type"]
            type_counts[pii_type] = type_counts.get(pii_type, 0) + 1

        # 2. Copia os contadores totais. Usaremos isso para decrementar.
        # (ex: NOME_PESSOA: 2, LOCAL: 3)
        current_counts = type_counts.copy()

        # 3. Ordena as entidades pela posição inicial (em ordem inversa para substituição)
        entities.sort(key=lambda x: x["span"][0], reverse=True)

        filtered_text = text
        pii_mappings = []

        # 4. Substitui entidades por placeholders (do fim para o começo)
        for entity in entities:
            pii_type = entity["type"]
            original_value = entity["value"]
            start, end = entity["span"]

            # Obtém o contador atual para este tipo (ex: 2 para NOME_PESSOA)
            count = current_counts[pii_type]

            # Decrementa o contador para a próxima entidade do mesmo tipo
            current_counts[pii_type] -= 1

            # Gera placeholder (ex: [NOME_PESSOA_2], depois [NOME_PESSOA_1])
            placeholder = f"[{pii_type}_{count}]"

            # Substitui no texto
            filtered_text = filtered_text[:start] + placeholder + filtered_text[end:]

            pii_mapping = PIIMapping(
                placeholder=placeholder,
                original_value=original_value,
                type=pii_type,
                span=(start, start + len(placeholder)),  # O span agora é do placeholder
            )
            pii_mappings.append(pii_mapping)

            self.logger.debug("Replaced '%s' with '%s'", original_value, placeholder)

        # --- FIM DA CORREÇÃO ---

        # Reverte a lista para manter a ordem original de aparição
        pii_mappings.reverse()

        self.logger.info(
            "NER filtering completed. Found %d entities", len(pii_mappings)
        )

        return filtered_text, pii_mappings

    def restore_from_ner(
        self, filtered_text: str, pii_mappings: List[PIIMapping]
    ) -> str:
        """
        Restaura o texto original a partir do texto filtrado usando mapeamentos PII.

        Args:
            filtered_text: Texto com placeholders
            pii_mappings: Lista de mapeamentos PII para restaurar

        Returns:
            Texto original com PII restaurado
        """
        if not pii_mappings:
            return filtered_text

        restored_text = filtered_text

        # Ordena os mapeamentos pelo comprimento do placeholder, do maior para o menor.
        # Isso evita substituições parciais (ex: substituir [NOME_1] dentro de [NOME_10])
        pii_mappings.sort(key=lambda m: len(m.placeholder), reverse=True)

        for mapping in pii_mappings:
            restored_text = restored_text.replace(
                mapping.placeholder, mapping.original_value
            )
            self.logger.debug(
                "Restored '%s' to '%s'", mapping.placeholder, mapping.original_value
            )

        return restored_text

    def get_supported_entity_types(self) -> List[str]:
        """
        Obtém a lista de tipos de entidade PII suportados.

        Returns:
            Lista de nomes de tipos PII suportados por este serviço
        """
        return list(set(self._ENTITY_TYPE_MAPPING.values()))
