"""
Constants for detecting PII and sensitive information in HR documents.
Regular patterns optimized for the Brazilian context, aligned with the scope of the thesis.
"""

import re
from typing import Any, Dict, List


# Regex patterns for key PIIs in the Brazilian HR context
PII_PATTERNS: Dict[str, re.Pattern] = {
    # CPF: Exactly 11 digits in the format XXX.XXX.XXX-XX (periods and hyphens optional)
    "CPF": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    # RG: Format X.XXX.XXX-X or XX.XXX.XXX-X (may have "RG:" before)
    "RG": re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-[0-9X]\b", re.IGNORECASE),
    # Email: Basic RFC compliant standard
    "EMAIL": re.compile(
        r"\b[a-zA-Z0-9](?:[a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b",
        re.IGNORECASE,
    ),
    # Phone: Brazilian formats with area code (landline and mobile)
    "TELEFONE": re.compile(r"(?:\+?55\s?)?\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}"),
    # Postal Code: Brazilian format XXXXX-XXX (hyphen optional)
    "CEP": re.compile(r"\b\d{5}-?\d{3}\b"),
}


# Categories of sensitive (non-PII) information relevant to HR
SENSITIVE_CATEGORIES: List[str] = [
    "CONDICAO_DE_SAUDE",
    "INFORMACAO_FINANCEIRA_DETALHADA",
    "HISTORICO_DISCIPLINAR",
    "PROBLEMA_PESSOAL_FAMILIAR",
    "USUARIO_REDE",
    "IP_ADDRESS",
    "REGISTRO_PONTO",
    "CARGO",
    "DEPARTAMENTO",
    "MATRICULA",
    "SALARIO",
    "ENDERECO_COMPLETO",
    "ENDERECO_LOGRADOURO",
    "ENDERECO_BAIRRO",
    "ENDERECO_CIDADE",
    "NOME_BANCO",
    "AGENCIA_BANCARIA",
    "DATA_NASCIMENTO",
    "CONTA_BANCARIA",
]


# Stop words in Portuguese (for NER and word processing)
PORTUGUESE_STOP_WORDS = [
    "a",
    "o",
    "e",
    "de",
    "do",
    "da",
    "em",
    "um",
    "uma",
    "que",
    "para",
    "com",
    "não",
    "se",
    "os",
    "as",
    "por",
    "no",
    "na",
    "dos",
    "das",
    "como",
    "mais",
    "mas",
    "ao",
    "pelo",
    "pela",
]


# Types of PII detectable via the NET
NER_PII_TYPES = {
    "NOME_COMPLETO": "Nome completo de pessoa física",
    "ORGANIZACAO": "Nome de organização/empresa",
    "LOCAL": "Nome de local/endereço",
    "CARGO": "Cargo/profissão",
}

NER_ENTITY_TYPE_MAPPING: Dict[str, str] = {
    "PERSON": "NOME_COMPLETO",
    "PER": "NOME_COMPLETO",
    "ORG": "ORGANIZACAO",
    "LOC": "LOCAL",
    "EVENT": "EVENTO",
    "WORK_OF_ART": "OBRA_ARTE",
    "LAW": "LEI",
    "LANGUAGE": "IDIOMA",
    "PROFISSAO": "CARGO",
    "CARGO": "CARGO",
}

NER_PROFESSION_PATTERNS: List[Dict[str, Any]] = [
    {
        "label": "CARGO",
        "pattern": [
            {
                "LOWER": {
                    "IN": [
                        "analista",
                        "gerente",
                        "coordenador",
                        "coordenadora",
                        "diretor",
                        "diretora",
                        "supervisor",
                        "supervisora",
                        "assistente",
                        "estagiário",
                        "estagiária",
                        "consultor",
                        "consultora",
                        "técnico",
                        "técnica",
                        "engenheiro",
                        "engenheira",
                        "desenvolvedor",
                        "desenvolvedora",
                        "especialista",
                        "chefe",
                        "lider",
                        "líder",
                    ]
                }
            },
            {"LOWER": "de", "OP": "?"},
            {"OP": "+"},
            {
                "LOWER": {
                    "IN": ["júnior", "pleno", "sênior", "sr", "pl", "jr", "ii", "iii"]
                },
                "OP": "?",
            },
        ],
    },
    {
        "label": "CARGO",
        "pattern": [
            {"LOWER": {"IN": ["desenvolvedor", "desenvolvedora", "dev"]}},
            {"LOWER": {"IN": ["full", "back", "front"]}, "OP": "?"},
            {"LOWER": {"IN": ["stack", "end"]}, "OP": "?"},
            {
                "LOWER": {"IN": ["júnior", "pleno", "sênior", "jr", "pl", "sr"]},
                "OP": "?",
            },
        ],
    },
    {
        "label": "CARGO",
        "pattern": [
            {"LOWER": {"IN": ["engenheiro", "engenheira"]}},
            {"LOWER": "de"},
            {"LOWER": {"IN": ["software", "dados", "segurança", "sistemas"]}},
            {"OP": "*"},
        ],
    },
    {"label": "CARGO", "pattern": [{"LOWER": "médico"}]},
    {"label": "CARGO", "pattern": [{"LOWER": "médica"}]},
    {"label": "CARGO", "pattern": [{"LOWER": "advogado"}]},
    {"label": "CARGO", "pattern": [{"LOWER": "advogada"}]},
    {"label": "CARGO", "pattern": [{"LOWER": "professor"}]},
    {"label": "CARGO", "pattern": [{"LOWER": "professora"}]},
    {"label": "CARGO", "pattern": [{"LOWER": "motorista"}]},
    {"label": "CARGO", "pattern": [{"LOWER": "recepcionista"}]},
    {
        "label": "CARGO",
        "pattern": [
            {"LOWER": {"IN": ["técnico", "técnica"]}},
            {"LOWER": {"IN": ["em", "de"]}},
            {
                "LOWER": {
                    "IN": [
                        "enfermagem",
                        "segurança",
                        "ti",
                        "informática",
                        "manutenção",
                        "suporte",
                    ]
                }
            },
        ],
    },
]

NER_FALSE_POSITIVES: set = {
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
    "funcionário principal: nome",
    "evidências digitais",
    "detalhes da fraude",
    "informações adicionais",
    "cúmplices:",
    "contato: telefone",
    "setor de suprimentos matrícula",
    "setor de suprimentos",
    "funcionário principal",
}


# All PII types supported (Regex + NER)
ALL_PII_TYPES = list(PII_PATTERNS.keys()) + list(NER_PII_TYPES.keys())
