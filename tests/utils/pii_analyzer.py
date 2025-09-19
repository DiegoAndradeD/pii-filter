"""
Main logic for PII detection coverage analysis used in regex filter.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any

from src.services.regex_service import RegexService
from src.models.models import PIIGroundTruth, PIIMapping
from src.utils.normalizers import normalize_pii_value


@dataclass
class DetectionMetrics:
    """Metrics for PII detection performance."""

    total_ground_truth: int
    total_detected: int
    true_positives: int
    false_positives: int
    false_negatives: int

    coverage_percentage: float
    precision: float
    recall: float
    f1_score: float

    detected_by_type: Dict[str, int]
    missed_by_type: Dict[str, int]
    false_positives_by_type: Dict[str, int]

    ground_truth_list: List[PIIGroundTruth] = field(default_factory=list)
    true_positives_list: List[Dict[str, Any]] = field(default_factory=list)
    false_positives_list: List[Dict[str, Any]] = field(default_factory=list)
    false_negatives_list: List[PIIGroundTruth] = field(default_factory=list)


class PIICoverageAnalyzer:
    """Analyzes PII detection performance against ground truth."""

    def __init__(self):
        self.regex_service = RegexService()
        self.detectable_types = set(self.regex_service._TYPE_PRIORITY.keys())

    def _extract_ground_truth_piis(
        self, ground_truth: List[Dict]
    ) -> List[PIIGroundTruth]:
        """Extracts PII from the ground truth of the data structure."""
        return [
            PIIGroundTruth(
                pii_type=pii_data["pii_type"],
                value=pii_data["value"],
                span=(pii_data["span"][0], pii_data["span"][1]),
            )
            for pii_data in ground_truth
        ]

    def _find_detected_pii_positions(self, mappings: List[PIIMapping]) -> List[Dict]:
        """Gets the details of detected PIIs directly from the mappings."""
        return [
            {
                "pii_type": mapping.type,
                "value": mapping.original_value,
                "span": mapping.span,
                "mapping": mapping,
            }
            for mapping in mappings
        ]

    def _calculate_overlap(
        self, span1: Tuple[int, int], span2: Tuple[int, int]
    ) -> bool:
        """Checks if two spans overlap."""
        return not (span1[1] <= span2[0] or span2[1] <= span1[0])

    def _match_detected_with_ground_truth(
        self, detected_piis: List[Dict], ground_truth_piis: List[PIIGroundTruth]
    ) -> Tuple[List[Dict], List[Dict], List[PIIGroundTruth]]:
        """
        Matches detected PIIs with ground truth PIIs using normalized values
        for more accurate comparison.
        """
        true_positives = []
        matched_ground_truth_indices = set()
        unmatched_detected_piis = list(detected_piis)

        for i, gt_pii in enumerate(ground_truth_piis):
            found_match = False
            for j, detected in enumerate(unmatched_detected_piis):

                types_match = detected["pii_type"] == gt_pii.pii_type
                if not types_match:
                    continue

                normalized_detected = normalize_pii_value(
                    detected["pii_type"], detected["value"]
                )
                normalized_gt = normalize_pii_value(gt_pii.pii_type, gt_pii.value)
                values_match = normalized_detected == normalized_gt

                spans_overlap = self._calculate_overlap(detected["span"], gt_pii.span)

                if values_match and spans_overlap:
                    true_positives.append(detected)
                    matched_ground_truth_indices.add(i)
                    unmatched_detected_piis.pop(j)
                    found_match = True
                    break

        false_positives = unmatched_detected_piis
        false_negatives = [
            gt_pii
            for i, gt_pii in enumerate(ground_truth_piis)
            if i not in matched_ground_truth_indices
        ]
        return true_positives, false_positives, false_negatives

    def _count_by_type(self, piis: list) -> Dict[str, int]:
        """Count PIIs by type."""
        counts = {}
        for pii in piis:
            pii_type = pii.pii_type if hasattr(pii, "pii_type") else pii["pii_type"]
            counts[pii_type] = counts.get(pii_type, 0) + 1
        return counts

    def analyze_detection_performance(
        self, text: str, ground_truth: List[Dict], validate_pii_data: bool = True
    ) -> DetectionMetrics:
        """
        Analyzes PII detection performance against ground truth.
        """
        ground_truth_piis = self._extract_ground_truth_piis(ground_truth)

        _, mappings = self.regex_service.filter_by_regex(text, validate_pii_data)
        detected_piis = self._find_detected_pii_positions(mappings)

        true_positives, false_positives, false_negatives = (
            self._match_detected_with_ground_truth(detected_piis, ground_truth_piis)
        )

        detectable_ground_truth = [
            gt for gt in ground_truth_piis if gt.pii_type in self.detectable_types
        ]

        total_detectable_ground_truth = len(detectable_ground_truth)
        tp_count = len(true_positives)
        precision = tp_count / len(detected_piis) if detected_piis else 0.0
        recall = (
            tp_count / total_detectable_ground_truth
            if total_detectable_ground_truth > 0
            else 0.0
        )
        f1_score = (
            (2 * (precision * recall) / (precision + recall))
            if (precision + recall) > 0
            else 0.0
        )

        return DetectionMetrics(
            total_ground_truth=len(ground_truth_piis),
            total_detected=len(detected_piis),
            true_positives=tp_count,
            false_positives=len(false_positives),
            false_negatives=len(false_negatives),
            coverage_percentage=(
                (tp_count / total_detectable_ground_truth * 100)
                if total_detectable_ground_truth > 0
                else 0.0
            ),
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            detected_by_type=self._count_by_type(true_positives),
            missed_by_type=self._count_by_type(false_negatives),
            false_positives_by_type=self._count_by_type(false_positives),
            ground_truth_list=ground_truth_piis,
            true_positives_list=true_positives,
            false_positives_list=false_positives,
            false_negatives_list=false_negatives,
        )
