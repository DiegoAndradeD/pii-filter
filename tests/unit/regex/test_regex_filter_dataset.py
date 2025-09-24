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

        print("metrics", metrics)

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

    # def test_overall_dataset_performance_summary(self):
    #     """
    #     Processes the entire dataset to calculate and display
    #     aggregate performance metrics, giving a global view of the system's accuracy.
    #     """
    #     if not TEST_CASES:
    #         pytest.skip("No test cases found in dataset.json to generate a summary.")

    #     # Initialize total counters
    #     total_tp = 0
    #     total_fp = 0
    #     total_fn = 0
    #     total_detected = 0
    #     total_ground_truth_piis = 0
    #     total_detectable_ground_truth = 0

    #     # Loop through all test cases to accumulate results
    #     for test_case in TEST_CASES:
    #         text = test_case["prompt_text"]
    #         ground_truth = test_case["ground_truth"]

    #         metrics = self.analyzer.analyze_detection_performance(
    #             text, ground_truth, validate_pii_data=False
    #         )

    #         # Accumulate the primary counts
    #         total_tp += metrics.true_positives
    #         total_fp += metrics.false_positives
    #         total_fn += metrics.false_negatives
    #         total_detected += metrics.total_detected
    #         total_ground_truth_piis += metrics.total_ground_truth

    #         # Correctly accumulate the total number of PIIs our system is expected to detect
    #         detectable_in_case = len(
    #             [
    #                 gt
    #                 for gt in metrics.ground_truth_list
    #                 if gt.pii_type in self.analyzer.detectable_types
    #             ]
    #         )
    #         total_detectable_ground_truth += detectable_in_case

    #     # Calculate overall metrics using the "micro-average" approach
    #     overall_precision = total_tp / total_detected if total_detected > 0 else 0.0
    #     overall_recall = (
    #         total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    #     )
    #     overall_f1_score = (
    #         (2 * overall_precision * overall_recall)
    #         / (overall_precision + overall_recall)
    #         if (overall_precision + overall_recall) > 0
    #         else 0.0
    #     )
    #     overall_coverage = (
    #         total_tp / total_detectable_ground_truth
    #         if total_detectable_ground_truth > 0
    #         else 0.0
    #     )

    #     # Print the final, consolidated report
    #     print(f"\n{'='*70}")
    #     print(f"OVERALL PERFORMANCE SUMMARY - {len(TEST_CASES)} TEST CASE(S) ANALYZED")
    #     print(f"{'='*70}")

    #     print("\n>> TOTAL COUNTS (ACROSS ALL CASES):")
    #     print(f"{'Total PIIs in Ground Truth:':<45} {total_ground_truth_piis}")
    #     print(f"{'Total PIIs Detected:':<45} {total_detected}")
    #     print(f"{'Total True Positives (TP):':<45} {total_tp}")
    #     print(f"{'Total False Positives (FP):':<45} {total_fp}")
    #     print(f"{'Total False Negatives (FN):':<45} {total_fn}")

    #     print("\n>> AGGREGATE PERFORMANCE METRICS:")
    #     print(f"{'Overall Coverage (TP / Detectable GT):':<45} {overall_coverage:.2%}")
    #     print(f"{'Overall Precision (TP / (TP + FP)):':<45} {overall_precision:.3f}")
    #     print(f"{'Overall Recall (TP / (TP + FN)):':<45} {overall_recall:.3f}")
    #     print(f"{'Overall F1-Score:':<45} {overall_f1_score:.3f}")
    #     print(f"{'='*70}")

    #     # Assertions to validate the overall test results
    #     assert overall_precision >= 0 and overall_precision <= 1
    #     assert overall_recall >= 0 and overall_recall <= 1
