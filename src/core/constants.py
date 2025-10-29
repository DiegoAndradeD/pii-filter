"""
The dictionary of regex patterns designed to detect Brazilian PII formats.
Each pattern is compiled for better performance.
"""

import re
from typing import Dict, List


PII_PATTERNS: Dict[str, re.Pattern] = {
    # CPF: Exactly 11 digits in XXX.XXX.XXX-XX format (dots and dash optional)
    "CPF": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    # CNH: Exactly 11 digits in XXX.XXX.XXX-XX format (same as CPF, differentiated by validation)
    "CNH": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    # CNPJ: Exactly 14 digits in XX.XXX.XXX/XXXX-XX format
    "CNPJ": re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),
    "EMAIL": re.compile(
        r"\b[a-zA-Z0-9](?:[a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}\b",
        re.IGNORECASE,
    ),
    "TELEFONE": re.compile(r"(?:\+?55\s?)?\(?\d{2}\)?\s?\d{4,5}[-\s]?\d{4}"),
    "CEP": re.compile(r"\b\d{5}-?\d{3}\b"),
    # RG: More restrictive to avoid conflicts with CPF
    # Matches 7-9 digits in X.XXX.XXX-X or XX.XXX.XXX-X format
    "RG": re.compile(r"(?:RG\s*:?\s*)?\b\d{1,2}\.\d{3}\.\d{3}-[0-9X]\b", re.IGNORECASE),
    "CARTAO_CREDITO": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    # PIS: Must have dots in the right positions to differentiate from CPF (XXX.XXXXX.XX-X)
    "PIS": re.compile(r"\b\d{3}\.\d{5}\.\d{2}-\d\b"),
    "TITULO_ELEITOR": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),
    "CONTA_BANCARIA": re.compile(
        r"\b(?:conta|cc|c/c)\s*:?\s*\d{4,8}[-\s]?\d{1,2}\b", re.IGNORECASE
    ),
}

SENSITIVE_CATEGORIES: List[str] = [
    "CONDIÇÃO_DE_SAUDE",
    "INFORMAÇÃO_FINANCEIRA_DETALHADA",
    "HISTORICO_DISCIPLINAR",
    "PROBLEMA_PESSOAL_FAMILIAR",
    "ORIENTAÇÃO_SEXUAL",
    "CRENÇA_RELIGIOSA",
    "OPINIÃO_POLÍTICA",
    "DADOS_BIOMÉTRICOS",
    "AVALIACAO_DESEMPENHO",
    "INFORMACAO_PSICOLOGICA",
    "SENHA",
    "USUARIO_REDE",
    "IP_ADDRESS",
    "MAC_ADDRESS",
    "REGISTRO_PONTO",
    "DOCUMENTO_URL",
    "FOTO_URL",
    "INFORMACAO_SENSIVEL",
    "HISTORICO_PROFISSIONAL",
    "CARGO",
    "DEPARTAMENTO",
    "MATRICULA",
    "SALARIO",
    "BENEFICIO",
    "SITUACAO_FINANCEIRA",
    "ENDERECO_LOGRADOURO",
    "ENDERECO_BAIRRO",
    "ENDERECO_CIDADE",
    "NOME_BANCO",
    "AGENCIA_BANCARIA",
    "NOME_DEPENDENTE",
    "DATA_NASCIMENTO",
    "DATA_NASCIMENTO_DEPENDENTE",
    "NOME_MEDICO",
    "NOME_EMPRESA_TERCEIRA",
    "NOME_CONTATO_EMERGENCIA",
    "TELEFONE_CONTATO_EMERGENCIA",
    "CNH",
    "PASSAPORTE",
    "DATA",
    "HORARIO",
    "PERIODO_LICENCA",
    "FERIAS",
    "RESULTADO_EXAME",
    "MEDICACAO",
]


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
]

# NER-based PII types mapping
NER_PII_TYPES = {
    "NOME_PESSOA": "Nome de pessoa física",
    "ORGANIZACAO": "Nome de organização/empresa",
    "LOCAL": "Nome de local/endereço",
    "EVENTO": "Nome de evento",
    "OBRA_ARTE": "Obra de arte/produto cultural",
    "LEI": "Referência legal/legislação",
    "IDIOMA": "Referência a idioma",
    "PROFISSAO": "Profissão",
}

# All supported PII types (regex + NER)
ALL_PII_TYPES = list(PII_PATTERNS.keys()) + list(NER_PII_TYPES.keys())
