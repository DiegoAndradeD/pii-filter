import pytest
from services.ner_service import NERService
from models.models import PIIMapping

ner_service = NERService()

class TestNERFilter:
    def test_person_detection(self):
        text = "O João Silva trabalha na empresa."
        filtered_text, mappings = ner_service.filter_by_ner(text)
        
        assert "[PER_1]" in filtered_text
        assert any(m.original_value == "João Silva" and m.type == "PER" for m in mappings)

    def test_organization_detection(self):
        text = "A reunião será na Google Brasil."
        filtered_text, mappings = ner_service.filter_by_ner(text)
        
        assert "[ORG_1]" in filtered_text
        assert any(m.original_value == "Google Brasil" and m.type == "ORG" for m in mappings)

    def test_location_detection(self):
        text = "Ele viajou para o Rio de Janeiro."
        filtered_text, mappings = ner_service.filter_by_ner(text)
        
        assert "[LOC_1]" in filtered_text
        assert any(m.original_value == "Rio de Janeiro" and m.type == "LOC" for m in mappings)

    def test_multiple_ner_types(self):
        text = "Maria Santos da IBM foi para São Paulo."
        filtered_text, mappings = ner_service.filter_by_ner(text)
        
        assert "[PER_1]" in filtered_text
        assert "[ORG_1]" in filtered_text
        assert "[LOC_1]" in filtered_text
        
        assert len(mappings) == 3
        assert any(m.original_value == "Maria Santos" and m.type == "PER" for m in mappings)
        assert any(m.original_value == "IBM" and m.type == "ORG" for m in mappings)
        assert any(m.original_value == "São Paulo" and m.type == "LOC" for m in mappings)

    def test_ner_restoration(self):
        original_text = "O Carlos da Microsoft visitou Paris."
        filtered_text, mappings = ner_service.filter_by_ner(original_text)
        restored_text = ner_service.restore_pii_from_mappings(filtered_text, mappings)
        
        assert restored_text == original_text

    def test_empty_text(self):
        filtered_text, mappings = ner_service.filter_by_ner("")
        assert filtered_text == ""
        assert not mappings

    def test_text_without_pii(self):
        text = "Este é um texto sem informações sensíveis."
        filtered_text, mappings = ner_service.filter_by_ner(text)
        assert filtered_text == text
        assert not mappings

