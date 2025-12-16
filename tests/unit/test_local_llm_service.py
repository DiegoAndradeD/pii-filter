"""
Validation Test (Efficacy: LocalLLMService)

This script implements the "Ablation Study" (Test 2c) for the LocalLLMService.

It performs a white-box test by:
1. Loading the ground truth dataset.
2. Identifying which sensitive categories the LocalLLMService is responsible for
   (based on SENSITIVE_CATEGORIES from constants.py).
3. Filtering the ground truth to create a "LLM-specific answer key".
4. Running the LocalLLMService directly on each prompt.
   NOTE: This requires the local Ollama instance to be running and accessible.
5. Comparing the service's detections against the answer key.
6. Calculating and reporting Precision, Recall, and F1-Score for
   the LLM filter.
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple, Set
import pytest

from src.core.constants import SENSITIVE_CATEGORIES
from src.services.local_llm_service import LocalLLMService
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
DATASET_FILE = BASE_DIR / "../../dataset.json"

LLM_SENSITIVE_TYPES: Set[str] = set(SENSITIVE_CATEGORIES)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (LLMTest) %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)


def test_local_llm_service_efficacy():
    """
    Tests the standalone efficacy of the LocalLLMService against the
    ground truth dataset.

    WARNING: This test relies on a live connection to the local LLM (Ollama).
    It will fail if the service is not running at the configured URL.
    """
    log.info("Starting Efficacy Test: LocalLLMService (Filtro 3)")
    log.info("NOTE: Ensure Ollama is running locally before proceeding.")

    try:
        test_cases = load_dataset(DATASET_FILE)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load dataset: {e}")

    llm_service = LocalLLMService()

    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_gt_piis = 0
    total_detected_piis = 0

    all_true_positives: List[Tuple[str, PIITuple]] = []
    all_false_positives: List[Tuple[str, PIITuple]] = []
    all_false_negatives: List[Tuple[str, PIITuple]] = []

    log.info(
        "LocalLLMService is being tested for %d sensitive categories:",
        len(LLM_SENSITIVE_TYPES),
    )
    log.info("%s\n", ", ".join(sorted(LLM_SENSITIVE_TYPES)))

    for i, case in enumerate(test_cases, 1):
        test_id = case.get("metadata", {}).get("id", f"unknown_id_{i}")
        prompt = case["prompt_text"]
        ground_truth_all = case["ground_truth"]

        ground_truth_llm = filter_ground_truth_by_types(
            ground_truth_all, LLM_SENSITIVE_TYPES
        )

        if not ground_truth_llm:
            log.debug("Case %s has no annotated sensitive topics for LLM.", test_id)

        log.info("Processing case %s with LLM...", test_id)
        _filtered_text, detected_pii = llm_service.filter_sensitive_topics(
            prompt, existing_placeholders=[]
        )

        tp_set, fp_set, fn_set = calculate_metrics_detailed(
            ground_truth_llm, detected_pii, prompt
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
        if fp_set:
            log.info("-" * 80)
            log.info("False Positives (Hallucinations/Errors):")
            for item in fp_set:
                log.info("• %s", item)
        if fn_set:
            log.info("-" * 80)
            log.info("False Negatives (Missed):")
            for item in fn_set:
                log.info("• %s", item)

        if tp_set or fp_set or fn_set:
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
        total_gt_piis += len(ground_truth_llm)
        total_detected_piis += len(detected_pii)

    log_detailed_detections(
        all_true_positives, all_false_positives, all_false_negatives, "LocalLLMService"
    )

    log.info("LocalLLMService Test Run Complete. Calculating metrics...\n")
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
        "LocalLLMService",
    )

    if total_gt_piis > 0:
        log.info("Final F1-Score: %.4f", f1_score)
    else:
        log.warning("No ground truth items found for LLM categories in the dataset.")
