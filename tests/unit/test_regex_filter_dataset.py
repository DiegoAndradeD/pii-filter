"""
Test to evaluate PII detection coverage against ground truth data.
"""

import pytest

from tests.utils.load_dataset import load_test_cases
from tests.utils.pii_analyzer import PIICoverageAnalyzer


TEST_CASES = load_test_cases()


class TestPIICoverage:
    """Test class for PII detection coverage analysis."""

    analyzer: PIICoverageAnalyzer = None

    def setup_method(self):
        """Setup method called before each test."""
        self.analyzer = PIICoverageAnalyzer()

    @pytest.mark.parametrize("test_case", TEST_CASES)
    def test_pii_detection_coverage(self, test_case):
        """Tests PII detection coverage in a specific test case."""
        text = test_case["prompt_text"]
        ground_truth = test_case["ground_truth"]
        test_id = test_case["metadata"]["id"]

        metrics = self.analyzer.analyze_detection_performance(
            text, ground_truth, validate_pii_data=False
        )

        print("\n" + "=" * 60)
        print(f"ANÁLISE DE DETECÇÃO DE PII - Test ID: {test_id}")
        print("=" * 60)
        print("\n📊 MÉTRICAS GERAIS (RESUMO):")
        print(f"Total de PIIs no Ground Truth: {metrics.total_ground_truth}")
        print(f"Total de PIIs Detectadas: {metrics.total_detected}")
        print(f"Verdadeiros Positivos: {metrics.true_positives}")
        print(f"Falsos Positivos: {metrics.false_positives}")
        print(f"Falsos Negativos: {metrics.false_negatives}")

        print("\n📈 MÉTRICAS DE DESEMPENHO:")
        print(f"Cobertura (Coverage): {metrics.coverage_percentage:.1f}%")
        print(f"Precisão (Precision): {metrics.precision:.3f}")
        print(f"Revocação (Recall): {metrics.recall:.3f}")
        print(f"F1-Score: {metrics.f1_score:.3f}")

        print(f"\n{'='*25} DETALHES {'='*25}")

        print(f"\n📋 GROUND TRUTH ({len(metrics.ground_truth_list)} itens):")
        if not metrics.ground_truth_list:
            print("  (Nenhum item no Ground Truth)")
        else:
            for pii in metrics.ground_truth_list:
                print(f"  - Tipo: {pii.pii_type:<15} | Valor: '{pii.value}'")

        print(f"\n✅ VERDADEIROS POSITIVOS ({len(metrics.true_positives_list)} itens):")
        if not metrics.true_positives_list:
            print("  (Nenhum item detectado corretamente)")
        else:
            for pii in metrics.true_positives_list:
                print(f"  - Tipo: {pii['pii_type']:<15} | Valor: '{pii['value']}'")

        print(
            f"\n❌ FALSOS NEGATIVOS ({len(metrics.false_negatives_list)} itens perdidos):"
        )
        if not metrics.false_negatives_list:
            print("  (Nenhum item do Ground Truth foi perdido)")
        else:
            for pii in metrics.false_negatives_list:
                is_detectable = (
                    " (Não detectável por regex)"
                    if pii.pii_type not in self.analyzer.detectable_types
                    else ""
                )
                print(
                    f"  - Tipo: {pii.pii_type:<15} | Valor: '{pii.value}'{is_detectable}"
                )

        print(
            f"\n⚠️  FALSOS POSITIVOS ({len(metrics.false_positives_list)} itens detectados incorretamente):"
        )
        if not metrics.false_positives_list:
            print("  (Nenhum item detectado incorretamente)")
        else:
            for pii in metrics.false_positives_list:
                print(f"  - Tipo: {pii['pii_type']:<15} | Valor: '{pii['value']}'")

        assert metrics.total_ground_truth >= 0
        assert metrics.total_detected >= 0
