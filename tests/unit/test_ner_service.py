"""
Unit tests for the NER service to verify named entity detection functionality.
"""

import pytest
from unittest.mock import Mock, patch
from src.services.ner_service import NERService
from src.models.models import PIIMapping


class MockEntity:
    """Mock spaCy entity for testing."""
    
    def __init__(self, text, label, start_char, end_char):
        self.text = text
        self.label_ = label
        self.start_char = start_char
        self.end_char = end_char


class MockDoc:
    """Mock spaCy document for testing."""
    
    def __init__(self, entities):
        self.ents = entities


class TestNERService:
    """Test cases for the NER service."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock spaCy to avoid requiring the actual model
        with patch('spacy.load') as mock_load:
            mock_nlp = Mock()
            mock_nlp.pipe_names = ['ner']
            mock_load.return_value = mock_nlp
            self.ner_service = NERService(model_name="test_model")
            self.ner_service.nlp = mock_nlp

    def test_extract_entities_with_persons(self):
        """Test entity extraction with person names."""
        # Arrange
        text = "João Silva trabalha na empresa Microsoft em São Paulo."
        
        mock_entities = [
            MockEntity("João Silva", "PERSON", 0, 10),
            MockEntity("Microsoft", "ORG", 32, 41),
            MockEntity("São Paulo", "GPE", 45, 54),
        ]
        mock_doc = MockDoc(mock_entities)
        self.ner_service.nlp.return_value = mock_doc
        
        # Act
        entities = self.ner_service._extract_entities(text)
        
        # Assert
        assert len(entities) == 3
        assert entities[0]["type"] == "NOME_PESSOA"
        assert entities[0]["value"] == "João Silva"
        assert entities[0]["span"] == (0, 10)
        
        assert entities[1]["type"] == "ORGANIZACAO"
        assert entities[1]["value"] == "Microsoft"
        assert entities[1]["span"] == (32, 41)
        
        assert entities[2]["type"] == "LOCAL"
        assert entities[2]["value"] == "São Paulo"
        assert entities[2]["span"] == (45, 54)

    def test_extract_entities_empty_text(self):
        """Test entity extraction with empty text."""
        # Arrange
        text = ""
        mock_doc = MockDoc([])
        self.ner_service.nlp.return_value = mock_doc
        
        # Act
        entities = self.ner_service._extract_entities(text)
        
        # Assert
        assert len(entities) == 0

    def test_filter_overlapping_entities(self):
        """Test filtering of overlapping entities."""
        # Arrange
        entities = [
            {"type": "NOME_PESSOA", "value": "João Silva", "span": (0, 10), "confidence": 1.0},
            {"type": "NOME_PESSOA", "value": "João", "span": (0, 4), "confidence": 0.8},  # Overlapping
            {"type": "ORGANIZACAO", "value": "Microsoft", "span": (20, 29), "confidence": 1.0},
        ]
        
        # Act
        filtered = self.ner_service._filter_overlapping_entities(entities)
        
        # Assert
        assert len(filtered) == 2
        assert filtered[0]["value"] == "João Silva"  # Longer entity kept
        assert filtered[1]["value"] == "Microsoft"

    def test_filter_by_ner_complete_flow(self):
        """Test the complete NER filtering flow."""
        # Arrange
        text = "Maria Santos trabalha na Google Brasil."
        
        mock_entities = [
            MockEntity("Maria Santos", "PERSON", 0, 12),
            MockEntity("Google Brasil", "ORG", 25, 38),
        ]
        mock_doc = MockDoc(mock_entities)
        self.ner_service.nlp.return_value = mock_doc
        
        # Act
        filtered_text, mappings = self.ner_service.filter_by_ner(text)
        
        # Assert
        assert len(mappings) == 2
        assert "[NOME_PESSOA_" in filtered_text
        assert "[ORGANIZACAO_" in filtered_text
        assert "Maria Santos" not in filtered_text
        assert "Google Brasil" not in filtered_text
        
        # Verify mappings (note: order is preserved after reverse)
        assert mappings[0].type == "NOME_PESSOA"
        assert mappings[0].original_value == "Maria Santos"
        
        assert mappings[1].type == "ORGANIZACAO"
        assert mappings[1].original_value == "Google Brasil"

    def test_filter_by_ner_no_entities(self):
        """Test NER filtering when no entities are found."""
        # Arrange
        text = "Este texto não tem entidades nomeadas específicas."
        mock_doc = MockDoc([])
        self.ner_service.nlp.return_value = mock_doc
        
        # Act
        filtered_text, mappings = self.ner_service.filter_by_ner(text)
        
        # Assert
        assert filtered_text == text
        assert len(mappings) == 0

    def test_restore_from_ner(self):
        """Test restoration of original text from NER mappings."""
        # Arrange
        filtered_text = "[NOME_PESSOA_1] trabalha na [ORGANIZACAO_2] em [LOCAL_3]."
        mappings = [
            PIIMapping(
                placeholder="[NOME_PESSOA_1]",
                original_value="Ana Costa",
                type="NOME_PESSOA",
                span=(0, 9)
            ),
            PIIMapping(
                placeholder="[ORGANIZACAO_2]",
                original_value="Amazon",
                type="ORGANIZACAO",
                span=(22, 28)
            ),
            PIIMapping(
                placeholder="[LOCAL_3]",
                original_value="Rio de Janeiro",
                type="LOCAL",
                span=(32, 46)
            )
        ]
        
        # Act
        restored_text = self.ner_service.restore_from_ner(filtered_text, mappings)
        
        # Assert
        expected = "Ana Costa trabalha na Amazon em Rio de Janeiro."
        assert restored_text == expected

    def test_restore_from_ner_no_mappings(self):
        """Test restoration when no mappings are provided."""
        # Arrange
        text = "Texto sem placeholders."
        mappings = []
        
        # Act
        restored_text = self.ner_service.restore_from_ner(text, mappings)
        
        # Assert
        assert restored_text == text

    def test_confidence_threshold_filtering(self):
        """Test filtering entities by confidence threshold."""
        # Arrange
        text = "João Silva trabalha na Microsoft."
        
        # Mock entities with different confidence levels
        mock_entities = [
            MockEntity("João Silva", "PERSON", 0, 10),
            MockEntity("Microsoft", "ORG", 23, 32),
        ]
        mock_doc = MockDoc(mock_entities)
        self.ner_service.nlp.return_value = mock_doc
        
        # Manually set confidence in extracted entities
        with patch.object(self.ner_service, '_extract_entities') as mock_extract:
            mock_extract.return_value = [
                {"type": "NOME_PESSOA", "value": "João Silva", "span": (0, 10), "confidence": 0.9},
                {"type": "ORGANIZACAO", "value": "Microsoft", "span": (23, 32), "confidence": 0.3},
            ]
            
            # Act
            filtered_text, mappings = self.ner_service.filter_by_ner(text, confidence_threshold=0.5)
            
            # Assert
            assert len(mappings) == 1  # Only high-confidence entity kept
            assert mappings[0].original_value == "João Silva"

    def test_get_supported_entity_types(self):
        """Test getting list of supported entity types."""
        # Act
        types = self.ner_service.get_supported_entity_types()
        
        # Assert
        assert "NOME_PESSOA" in types
        assert "ORGANIZACAO" in types
        assert "LOCAL" in types
        assert isinstance(types, list)

    def test_short_entity_filtering(self):
        """Test that very short entities are filtered out."""
        # Arrange
        text = "A empresa X contratou João Silva."
        
        mock_entities = [
            MockEntity("A", "ORG", 0, 1),  # Too short
            MockEntity("X", "ORG", 10, 11),  # Too short
            MockEntity("João Silva", "PERSON", 22, 32),  # Valid
        ]
        mock_doc = MockDoc(mock_entities)
        self.ner_service.nlp.return_value = mock_doc
        
        # Act
        entities = self.ner_service._extract_entities(text)
        
        # Assert
        assert len(entities) == 1
        assert entities[0]["value"] == "João Silva"

    def test_numeric_entity_filtering(self):
        """Test that purely numeric entities are filtered out."""
        # Arrange
        text = "Em 2023 a empresa Microsoft foi fundada."
        
        mock_entities = [
            MockEntity("2023", "DATE", 3, 7),  # Numeric, should be filtered
            MockEntity("Microsoft", "ORG", 18, 27),  # Valid
        ]
        mock_doc = MockDoc(mock_entities)
        self.ner_service.nlp.return_value = mock_doc
        
        # Act
        entities = self.ner_service._extract_entities(text)
        
        # Assert
        assert len(entities) == 1
        assert entities[0]["value"] == "Microsoft"