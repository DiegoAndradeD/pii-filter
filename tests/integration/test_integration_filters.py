import pytest
from services.regex_service import RegexService
from services.ner_service import NERService

regex_service = RegexService()
ner_service = NERService()

class TestIntegrationFilters:
    def test_regex_and_ner_integration(self):
        text = "João Silva, CPF 123.456.789-09, trabalha na Google Brasil e mora em São Paulo."
        regex_filtered_text, regex_mapping = regex_service.filter_by_regex(text, validate_pii_data=True)
        ner_filtered_text, ner_mapping = ner_service.filter_by_ner(regex_filtered_text)
        all_mappings = regex_mapping + ner_mapping

        assert "[PER_1]" in ner_filtered_text
        assert "[ORG_1]" in ner_filtered_text
        assert "[LOC_1]" in ner_filtered_text
        assert "[CPF" in regex_filtered_text or "[CPF" in ner_filtered_text
        assert any(m.original_value == "João Silva" and m.type == "PER" for m in all_mappings)
        assert any(m.original_value == "Google Brasil" and m.type == "ORG" for m in all_mappings)
        assert any(m.original_value == "São Paulo" and m.type == "LOC" for m in all_mappings)
        assert any(m.type == "CPF" for m in all_mappings)

        # Restauração
        restored = ner_service.restore_pii_from_mappings(ner_filtered_text, ner_mapping)
        restored = regex_service.restore_pii_from_mappings(restored, regex_mapping)
        assert restored == text

    def test_overlapping_entities(self):
        text = "Ana 123.456.789-09 foi para Belo Horizonte. 123.456.789-09 é o CPF dela."
        regex_filtered_text, regex_mapping = regex_service.filter_by_regex(text, validate_pii_data=True)
        ner_filtered_text, ner_mapping = ner_service.filter_by_ner(regex_filtered_text)
        all_mappings = regex_mapping + ner_mapping

        # Garante que nome e CPF foram mascarados corretamente, sem sobreposição
        assert "[PER_1]" in ner_filtered_text
        assert "[CPF" in regex_filtered_text or "[CPF" in ner_filtered_text
        assert any(m.original_value == "Ana" and m.type == "PER" for m in all_mappings)
        assert any(m.original_value == "123.456.789-09" and m.type == "CPF" for m in all_mappings)

        restored = ner_service.restore_pii_from_mappings(ner_filtered_text, ner_mapping)
        restored = regex_service.restore_pii_from_mappings(restored, regex_mapping)
        assert restored == text

    def test_large_text_multiple_entities(self):
        text = (
            "Carlos visitou a IBM em Brasília. CPF 529.982.247-25. "
            "Maria Santos trabalha na Google Brasil, mora em Curitiba, CPF 153.509.460-56."
        )
        regex_filtered_text, regex_mapping = regex_service.filter_by_regex(text, validate_pii_data=True)
        ner_filtered_text, ner_mapping = ner_service.filter_by_ner(regex_filtered_text)
        all_mappings = regex_mapping + ner_mapping

        # Verifica se mascarou todos os tipos
        assert "[PER_1]" in ner_filtered_text
        assert "[PER_2]" in ner_filtered_text
        assert "[ORG_1]" in ner_filtered_text
        assert "[ORG_2]" in ner_filtered_text
        assert "[LOC_1]" in ner_filtered_text
        assert "[LOC_2]" in ner_filtered_text
        assert "[CPF" in regex_filtered_text or "[CPF" in ner_filtered_text
        assert len([m for m in all_mappings if m.type == "CPF"]) == 2

        restored = ner_service.restore_pii_from_mappings(ner_filtered_text, ner_mapping)
        restored = regex_service.restore_pii_from_mappings(restored, regex_mapping)
        assert restored == text

    def test_filter_order(self):
        # Primeiro NER depois regex
        text = "Fernando, CPF 123.456.789-09, trabalha na Microsoft."
        ner_filtered_text, ner_mapping = ner_service.filter_by_ner(text)
        regex_filtered_text, regex_mapping = regex_service.filter_by_regex(ner_filtered_text, validate_pii_data=True)

        # Verifica se ambos mascararam corretamente na ordem invertida
        assert "[PER_1]" in regex_filtered_text
        assert "[ORG_1]" in regex_filtered_text
        assert "[CPF" in regex_filtered_text or "[CPF" in ner_filtered_text
        all_mappings = ner_mapping + regex_mapping

        restored = regex_service.restore_pii_from_mappings(regex_filtered_text, regex_mapping)
        restored = ner_service.restore_pii_from_mappings(restored, ner_mapping)
        assert restored == text

    def test_false_positive_protection(self):
        # Texto com dados não sensíveis
        text = "Este não é um CPF: 123.456.789.00, e nem um nome famoso: Computador."
        regex_filtered_text, regex_mapping = regex_service.filter_by_regex(text, validate_pii_data=True)
        ner_filtered_text, ner_mapping = ner_service.filter_by_ner(regex_filtered_text)

        # Nada deve ser mascarado
        assert ner_filtered_text == text
        assert not regex_mapping
        assert not ner_mapping

    def test_restore_with_mixed_filters(self):
        # Caso misto, restaurar usando ambos os mapeamentos
        text = "João, CPF 123.456.789-09, mora em Porto Alegre."
        regex_filtered_text, regex_mapping = regex_service.filter_by_regex(text, validate_pii_data=True)
        ner_filtered_text, ner_mapping = ner_service.filter_by_ner(regex_filtered_text)
        restored = ner_service.restore_pii_from_mappings(ner_filtered_text, ner_mapping)
        restored = regex_service.restore_pii_from_mappings(restored, regex_mapping)
        assert restored == text