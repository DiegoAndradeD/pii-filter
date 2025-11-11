"""
Test Utilities

Common utilities for validation tests, including dataset loading,
metrics calculation, and reporting functions.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

from src.models.models import PIIMapping

PIITuple = Tuple[str, Tuple[int, int], str]
PIISet = Set[PIITuple]
PIIMap = Dict[str, Any]
TestCase = Dict[str, Any]

log = logging.getLogger(__name__)


def load_dataset(filepath: Path) -> List[TestCase]:
    """
    Loads the ground truth dataset from the specified JSON file.

    Args:
        filepath: Path to the JSON dataset file

    Returns:
        List of test cases from the dataset

    Raises:
        FileNotFoundError: If the dataset file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            dataset = json.load(f)
        log.info("Successfully loaded %d test cases from %s", len(dataset), filepath)
        return dataset
    except FileNotFoundError:
        log.error("FATAL: Dataset file not found at %s", filepath)
        raise
    except json.JSONDecodeError:
        log.error("FATAL: Failed to decode JSON from %s", filepath)
        raise


def calculate_metrics_detailed(
    gt_list: List[PIIMap], detected_list: List[PIIMapping], prompt_text: str
) -> Tuple[PIISet, PIISet, PIISet]:
    """
    Compares ground truth PIIs against detected PIIs and returns
    the SETS of True Positives, False Positives, and False Negatives.

    A match is defined as having the *exact same type* and *exact same span*.
    Includes the actual value from the prompt text.

    Args:
        gt_list: List of ground truth PII dictionaries
        detected_list: List of detected PIIMapping objects
        prompt_text: Original prompt text for extracting values

    Returns:
        Tuple of (true_positives, false_positives, false_negatives) as sets
    """
    gt_set: PIISet = set()
    for pii_dict in gt_list:
        span_tuple = tuple(pii_dict["span"])
        value = pii_dict.get("value", prompt_text[span_tuple[0] : span_tuple[1]])
        gt_set.add((pii_dict["pii_type"], span_tuple, value))

    detected_set: PIISet = set()
    for pii_obj in detected_list:
        value = prompt_text[pii_obj.span[0] : pii_obj.span[1]]
        detected_set.add((pii_obj.type, pii_obj.span, value))

    tp_set = gt_set.intersection(detected_set)
    fp_set = detected_set - gt_set
    fn_set = gt_set - detected_set

    return tp_set, fp_set, fn_set


def calculate_final_metrics(
    total_tp: int, total_fp: int, total_fn: int
) -> Tuple[float, float, float]:
    """
    Calculates Precision, Recall, and F1-Score from TP, FP, and FN counts.

    Args:
        total_tp: Total true positives
        total_fp: Total false positives
        total_fn: Total false negatives

    Returns:
        Tuple of (precision, recall, f1_score)
    """
    if (total_tp + total_fp) == 0:
        precision = 0.0
        log.warning("No PIIs were detected (TP + FP = 0).")
    else:
        precision = total_tp / (total_tp + total_fp)

    if (total_tp + total_fn) == 0:
        recall = 0.0
        log.warning("No PIIs were found in the ground truth (TP + FN = 0).")
    else:
        recall = total_tp / (total_tp + total_fn)

    if (precision + recall) == 0:
        f1_score = 0.0
    else:
        f1_score = 2 * (precision * recall) / (precision + recall)

    return precision, recall, f1_score


def log_detailed_detections(
    all_true_positives: List[Tuple[str, PIITuple]],
    all_false_positives: List[Tuple[str, PIITuple]],
    all_false_negatives: List[Tuple[str, PIITuple]],
    service_name: str = "Service",
) -> None:
    """
    Logs detailed detection reports for TP, FP, and FN.

    Args:
        all_true_positives: List of (test_id, pii_tuple) for true positives
        all_false_positives: List of (test_id, pii_tuple) for false positives
        all_false_negatives: List of (test_id, pii_tuple) for false negatives
        service_name: Name of the service being tested
    """
    log.info("=" * 80)
    log.info("DETAILED DETECTION REPORT (%s)", service_name)
    log.info("=" * 80)

    log.info("True Positives (%d)", len(all_true_positives))
    if all_true_positives:
        for test_id, (pii_type, span, value) in all_true_positives:
            log.info(
                "[TP] TestID=%-10s | Type=%-15s | Value='%-20s' | Span=%s",
                test_id,
                pii_type,
                value,
                span,
            )
    else:
        log.info("  None.")
    log.info("-" * 120)
    log.info("False Positives (%d)", len(all_false_positives))
    if all_false_positives:
        for test_id, (pii_type, span, value) in all_false_positives:
            log.info(
                "[FP] TestID=%-10s | Type=%-15s | Value='%-20s' | Span=%s",
                test_id,
                pii_type,
                value,
                span,
            )
    else:
        log.info("  None.")

    log.info("-" * 120)
    log.info("False Negatives (%d)", len(all_false_negatives))
    if all_false_negatives:
        for test_id, (pii_type, span, value) in all_false_negatives:
            log.info(
                "[FN] TestID=%-10s | Type=%-15s | Value='%-20s' | Span=%s",
                test_id,
                pii_type,
                value,
                span,
            )
    else:
        log.info("  None.")

    log.info("")


def log_final_metrics(
    total_gt_piis: int,
    total_detected_piis: int,
    total_tp: int,
    total_fp: int,
    total_fn: int,
    precision: float,
    recall: float,
    f1_score: float,
    service_name: str = "Service",
) -> None:
    """
    Logs final metrics summary in a formatted table.

    Args:
        total_gt_piis: Total ground truth PIIs
        total_detected_piis: Total detected PIIs
        total_tp: Total true positives
        total_fp: Total false positives
        total_fn: Total false negatives
        precision: Precision score (0-1)
        recall: Recall score (0-1)
        f1_score: F1 score (0-1)
        service_name: Name of the service being tested
    """
    log.info("=" * 80)
    log.info("%s EFFICACY RESULTS", service_name.upper())
    log.info("=" * 80)
    log.info("Total Ground Truth PIIs: %d", total_gt_piis)
    log.info("Total Detected PIIs:     %d", total_detected_piis)
    log.info("-" * 80)
    log.info("True Positives (TP):     %d", total_tp)
    log.info("False Positives (FP):    %d", total_fp)
    log.info("False Negatives (FN):    %d", total_fn)
    log.info("-" * 80)
    log.info("PRECISION: %.4f  (%.2f%%)", precision, precision * 100)
    log.info("RECALL:    %.4f  (%.2f%%)", recall, recall * 100)
    log.info("F1-SCORE:  %.4f  (%.2f%%)", f1_score, f1_score * 100)
    log.info("=" * 80)


def filter_ground_truth_by_types(
    ground_truth: List[PIIMap], pii_types: Set[str]
) -> List[PIIMap]:
    """
    Filters ground truth to only include specified PII types.

    Args:
        ground_truth: List of all ground truth PIIs
        pii_types: Set of PII types to include

    Returns:
        Filtered list of ground truth PIIs
    """
    return [pii for pii in ground_truth if pii["pii_type"] in pii_types]
