"""
Validation Test (Efficacy: RegexService)

This script implements the "Ablation Study" for the RegexService.

It performs a white-box test by:
1. Loading the ground truth dataset.
2. Identifying which PII types the RegexService is responsible for
   (by importing PII_PATTERNS from constants).
3. Filtering the ground truth to create a "Regex-specific answer key".
4. Running the RegexService directly on each prompt.
5. Comparing the service's detections against the answer key.
6. Calculating and reporting Precision, Recall, and F1-Score for
   the Regex filter.
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple
import pytest

from src.core.constants import PII_PATTERNS
from src.services.regex_service import RegexService
from tests.utils.test_utils import (
    load_dataset,
    calculate_metrics_detailed,
    calculate_final_metrics,
    log_detailed_detections,
    log_final_metrics,
    filter_ground_truth_by_types,
    PIITuple,
)

BASE_DIR = Path(__file__).resolve().parent
DATASET_FILE = BASE_DIR / "../../final-dataset.json"

REGEX_PII_TYPES = set(PII_PATTERNS.keys())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (RegexTest) %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)


def test_regex_service_efficacy():
    """
    Tests the standalone efficacy of the RegexService against the
    ground truth dataset.
    """
    log.info("Starting Efficacy Test: RegexService (Filtro 1)")

    try:
        test_cases = load_dataset(DATASET_FILE)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load dataset: {e}")

    regex_service = RegexService()

    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_gt_piis = 0
    total_detected_piis = 0

    all_true_positives: List[Tuple[str, PIITuple]] = []
    all_false_positives: List[Tuple[str, PIITuple]] = []
    all_false_negatives: List[Tuple[str, PIITuple]] = []

    log.info("RegexService is being tested for %d PII types:", len(REGEX_PII_TYPES))
    log.info("%s\n", ", ".join(sorted(REGEX_PII_TYPES)))

    for i, case in enumerate(test_cases, 1):
        test_id = case.get("metadata", {}).get("id", f"unknown_id_{i}")
        prompt = case["prompt_text"]
        ground_truth_all = case["ground_truth"]

        ground_truth_regex = filter_ground_truth_by_types(
            ground_truth_all, REGEX_PII_TYPES
        )

        _filtered_text, detected_pii = regex_service.filter_by_regex(
            prompt, validate_pii_data=True
        )

        tp_set, fp_set, fn_set = calculate_metrics_detailed(
            ground_truth_regex, detected_pii, prompt
        )

        tp, fp, fn = len(tp_set), len(fp_set), len(fn_set)

        if tp > 0 or fp > 0 or fn > 0:
            log.info("Test %s — Results:", test_id)
            log.info("TP: %-3d | FP: %-3d | FN: %-3d", tp, fp, fn)

        if tp_set:
            log.info("-" * 80)
            log.info("True Positives:")
            for item in tp_set:
                log.info("• %s", item)
            log.info("-" * 80)
        if fp_set:
            log.info("False Positives:")
            for item in fp_set:
                log.info("• %s", item)
            log.info("-" * 80)
        if fn_set:
            log.info("False Negatives:")
            for item in fn_set:
                log.info("• %s", item)
            log.info("-" * 80)
        log.info("")

        if tp_set:
            all_true_positives.extend([(test_id, tp) for tp in tp_set])
        if fp_set:
            all_false_positives.extend([(test_id, fp) for fp in fp_set])
        if fn_set:
            all_false_negatives.extend([(test_id, fn) for fn in fn_set])

        total_tp += tp
        total_fp += fp
        total_fn += fn
        total_gt_piis += len(ground_truth_regex)
        total_detected_piis += len(detected_pii)

    log_detailed_detections(
        all_true_positives, all_false_positives, all_false_negatives, "RegexService"
    )

    log.info("RegexService Test Run Complete. Calculating metrics...\n")
    precision, recall, f1_score = calculate_final_metrics(total_tp, total_fp, total_fn)

    log_final_metrics(
        total_gt_piis,
        total_detected_piis,
        total_tp,
        total_fp,
        total_fn,
        precision,
        recall,
        f1_score,
        "RegexService",
    )

    assert total_gt_piis > 0, "Test dataset seems empty of Regex PIIs."
    assert f1_score > 0.0, "RegexService F1-Score was zero."
