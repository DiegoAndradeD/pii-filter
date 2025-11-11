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
    {"label": "CARGO", "pattern": "analista de sistemas"},
    {"label": "CARGO", "pattern": "engenheiro de software"},
    {"label": "CARGO", "pattern": "gerente de projetos"},
    {"label": "CARGO", "pattern": "médico"},
    {"label": "CARGO", "pattern": "advogado"},
    {"label": "CARGO", "pattern": "professor"},
    {"label": "CARGO", "pattern": "técnico em enfermagem"},
    {"label": "CARGO", "pattern": "técnico de"},
    {"label": "CARGO", "pattern": "analista"},
    {"label": "CARGO", "pattern": "gerente"},
    {"label": "CARGO", "pattern": "coordenador"},
    {"label": "CARGO", "pattern": "diretor"},
    {"label": "CARGO", "pattern": "supervisor"},
    {"label": "CARGO", "pattern": "assistente"},
    {"label": "CARGO", "pattern": "estagiário"},
    {"label": "CARGO", "pattern": "consultor"},
    {"label": "CARGO", "pattern": "desenvolvedor"},
    {"label": "CARGO", "pattern": "Assistente de Logística"},
    {"label": "CARGO", "pattern": "Analista de Marketing"},
    {"label": "CARGO", "pattern": "Coordenadora de Marketing"},
    {"label": "CARGO", "pattern": "Técnico de TI"},
    {"label": "CARGO", "pattern": "Analista Financeiro"},
    {"label": "CARGO", "pattern": "Desenvolvedor Front-End"},
    {"label": "CARGO", "pattern": "Coordenador de TI"},
    {"label": "CARGO", "pattern": "Gerente de Infraestrutura"},
    {"label": "CARGO", "pattern": "Assistente Administrativo"},
    {"label": "CARGO", "pattern": "Analista de Qualidade Sênior"},
    {"label": "CARGO", "pattern": "Desenvolvedora Full Stack Junior"},
    {"label": "CARGO", "pattern": "Supervisor de Logística"},
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
