"""
Validation Test (Integration: Pipeline Efficacy)

This script tests the COMBINED efficacy of the three filtering layers:
1. RegexService
2. NERService
3. LocalLLMService

It simulates the sequential pipeline behavior based on INDEX PRECEDENCE:
- Regex detections take highest priority.
- NER detections are kept only if they don't overlap with Regex.
- LLM detections are kept only if they don't overlap with Regex or NER.

This approach avoids the "Index Shift" problem caused by string replacement
during testing against a static Ground Truth.
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple
import pytest

from src.services.regex_service import RegexService
from src.services.ner_service import NERService
from src.services.local_llm_service import LocalLLMService
from src.models.models import PIIMapping

from tests.utils.test_utils import (
    load_dataset,
    calculate_metrics_detailed,
    calculate_final_metrics,
    log_detailed_detections,
    log_final_metrics,
    PIITuple,
)

BASE_DIR = Path(__file__).resolve().parent
DATASET_FILE = BASE_DIR / "../../final-dataset.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (PipelineTest) %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)


def _is_overlapping(span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
    """
    Helper to check if two spans overlap.
    Span format: (start_index, end_index)
    Logic: Start of A < End of B AND End of A > Start of B
    """
    return span1[0] < span2[1] and span1[1] > span2[0]


def test_pipeline_integration_efficacy():
    """
    Tests the integrated efficacy of the 3-stage filtering pipeline
    using Logic-based filtering instead of Text Mutation to preserve indices.
    """
    log.info("Starting Integration Test: Full Filtering Pipeline (Regex -> NER -> LLM)")
    log.info("NOTE: Ensure Ollama is running locally.")

    try:
        test_cases = load_dataset(DATASET_FILE)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        pytest.fail(f"Failed to load dataset: {e}")

    regex_service = RegexService()
    ner_service = NERService()
    llm_service = LocalLLMService()

    total_tp = 0
    total_fp = 0
    total_fn = 0
    total_gt_piis = 0
    total_detected_piis = 0

    all_true_positives: List[Tuple[str, PIITuple]] = []
    all_false_positives: List[Tuple[str, PIITuple]] = []
    all_false_negatives: List[Tuple[str, PIITuple]] = []

    for i, case in enumerate(test_cases, 1):
        test_id = case.get("metadata", {}).get("id", f"unknown_id_{i}")
        prompt = case["prompt_text"]

        ground_truth_all = case["ground_truth"]

        log.info("Processing pipeline for case %s...", test_id)

        _, regex_mappings = regex_service.filter_by_regex(
            prompt, validate_pii_data=True
        )

        final_regex_mappings = regex_mappings

        _, raw_ner_mappings = ner_service.filter_by_ner(prompt)

        final_ner_mappings = []
        for ner_map in raw_ner_mappings:
            has_conflict = False
            for regex_map in final_regex_mappings:
                if _is_overlapping(ner_map.span, regex_map.span):
                    has_conflict = True
                    log.debug(
                        "NER dropped '%s' (%s) due to overlap with Regex '%s'",
                        ner_map.original_value,
                        ner_map.type,
                        regex_map.type,
                    )
                    break

            if not has_conflict:
                final_ner_mappings.append(ner_map)

        _, raw_llm_mappings = llm_service.filter_sensitive_topics(
            prompt, existing_placeholders=[]
        )

        final_llm_mappings = []
        higher_priority_mappings = final_regex_mappings + final_ner_mappings

        for llm_map in raw_llm_mappings:
            has_conflict = False
            for existing_map in higher_priority_mappings:
                if _is_overlapping(llm_map.span, existing_map.span):
                    has_conflict = True
                    log.debug(
                        "LLM dropped '%s' (%s) due to overlap with %s",
                        llm_map.original_value,
                        llm_map.type,
                        existing_map.type,
                    )
                    break

            if not has_conflict:
                final_llm_mappings.append(llm_map)

        all_detected_mappings = (
            final_regex_mappings + final_ner_mappings + final_llm_mappings
        )

        tp_set, fp_set, fn_set = calculate_metrics_detailed(
            ground_truth_all, all_detected_mappings, prompt
        )

        tp, fp, fn = len(tp_set), len(fp_set), len(fn_set)

        log.info(
            "  -> Stage 1 (Regex): Found %d valid items", len(final_regex_mappings)
        )
        log.info(
            "  -> Stage 2 (NER):   Found %d valid items (filtered from %d)",
            len(final_ner_mappings),
            len(raw_ner_mappings),
        )
        log.info(
            "  -> Stage 3 (LLM):   Found %d valid items (filtered from %d)",
            len(final_llm_mappings),
            len(raw_llm_mappings),
        )
        log.info(
            "  => Total Final: %d | TP: %d | FP: %d | FN: %d",
            len(all_detected_mappings),
            tp,
            fp,
            fn,
        )
        log.info("-" * 60)

        if tp_set:
            all_true_positives.extend([(test_id, tp) for tp in tp_set])
        if fp_set:
            all_false_positives.extend([(test_id, fp) for fp in fp_set])
        if fn_set:
            all_false_negatives.extend([(test_id, fn) for fn in fn_set])

        total_tp += tp
        total_fp += fp
        total_fn += fn
        total_gt_piis += len(ground_truth_all)
        total_detected_piis += len(all_detected_mappings)

    log_detailed_detections(
        all_true_positives, all_false_positives, all_false_negatives, "FullPipeline"
    )

    log.info("Integration Pipeline Test Run Complete. Calculating metrics...\n")
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
        "FullPipeline",
    )

    if total_gt_piis > 0:
        log.info("Final F1-Score: %.4f", f1_score)
