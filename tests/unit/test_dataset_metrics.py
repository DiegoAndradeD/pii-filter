"""
Quality metrics analysis and testing module for the HR prompts dataset.

This module loads a dataset in JSON format and, using the pre-existing
annotations in the `ground_truth` field, calculates a comprehensive set of
diversity and coverage metrics.
"""

import json
from collections import Counter
from typing import List, Dict, Any, Tuple

import numpy as np
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Import centralized definitions from the constants file
from src.core.constants import (
    PORTUGUESE_STOP_WORDS,
    PII_PATTERNS,
    SENSITIVE_CATEGORIES,
)

# Path to the dataset file
DATASET_FILE = "dataset.json"


@pytest.fixture(scope="module")
def dataset() -> List[Dict[str, Any]]:
    """Loads the dataset from the JSON file."""
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_dataset_from_ground_truth(dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes the dataset and calculates metrics using the `ground_truth` annotations.
    """
    texts = [entry["prompt_text"] for entry in dataset]
    total_prompts = len(dataset)

    regex_pii_counter = Counter()
    llm_topic_counter = Counter()

    # Iterate over the dataset to collect ground_truth data
    for entry in dataset:
        for annotation in entry.get("ground_truth", []):
            pii_type = annotation.get("pii_type")
            # Classify PII based on imported lists
            if pii_type in PII_PATTERNS:
                regex_pii_counter.update([pii_type])
            elif pii_type in SENSITIVE_CATEGORIES:
                llm_topic_counter.update([pii_type])

    total_regex_pii = sum(regex_pii_counter.values())
    total_llm_topics = sum(llm_topic_counter.values())

    # Text metrics
    text_lengths = [len(text.split()) for text in texts]
    avg_text_length = np.mean(text_lengths) if text_lengths else 0
    max_text_length = max(text_lengths) if text_lengths else 0
    min_text_length = min(text_lengths) if text_lengths else 0

    # Semantic Diversity Analysis
    semantic_diversity = 0.0
    if total_prompts > 1:
        vectorizer = TfidfVectorizer(stop_words=PORTUGUESE_STOP_WORDS)
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        upper_tri_indices = np.triu_indices_from(similarity_matrix, k=1)
        if upper_tri_indices[0].size > 0:
            avg_similarity = np.mean(similarity_matrix[upper_tri_indices])
            semantic_diversity = 1 - avg_similarity

    return {
        "total_prompts": total_prompts,
        "avg_text_length": round(avg_text_length, 2),
        "max_text_length": max_text_length,
        "min_text_length": min_text_length,
        "semantic_diversity": round(semantic_diversity, 4),
        "total_regex_pii": total_regex_pii,
        "regex_pii_distribution": dict(regex_pii_counter),
        "avg_regex_pii_per_prompt": (
            round(total_regex_pii / total_prompts, 2) if total_prompts else 0
        ),
        "total_llm_topics": total_llm_topics,
        "llm_topic_distribution": dict(llm_topic_counter),
        "avg_llm_topics_per_prompt": (
            round(total_llm_topics / total_prompts, 2) if total_prompts else 0
        ),
    }


def verify_dataset_quality(stats: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Evaluates the statistics and checks if the dataset meets quality criteria.
    """
    messages = []
    if stats["total_prompts"] < 50:
        messages.append(
            f"Dataset too small ({stats['total_prompts']} prompts), expected > 50."
        )
    if stats["avg_text_length"] < 20:
        messages.append(
            f"Prompts too short on average ({stats['avg_text_length']} words), expected > 20."
        )
    if stats["total_regex_pii"] < 100:
        messages.append(
            f"Few structured PIIs found ({stats['total_regex_pii']}), expected > 100."
        )
    if len(stats["regex_pii_distribution"]) < 5:
        messages.append(
            f"Low diversity of PII types ({len(stats['regex_pii_distribution'])} types), expected > 5."
        )
    if stats["total_llm_topics"] < 7:
        messages.append(
            f"Few sensitive topics found ({stats['total_llm_topics']}), expected > 25."
        )
    if len(stats["llm_topic_distribution"]) < 1:
        messages.append(
            f"Low diversity of sensitive topics ({len(stats['llm_topic_distribution'])} types), expected > 3."
        )
    if stats["semantic_diversity"] < 0.7:
        messages.append(
            f"Dataset not diverse enough (similarity: {1-stats['semantic_diversity']:.2f}), expected score > 0.7."
        )

    is_high_quality = len(messages) == 0
    return is_high_quality, messages


def test_dataset_metrics_and_quality(dataset: List[Dict[str, Any]]):
    """
    Main test: calculates the dataset metrics from the ground_truth
    and verifies if it meets the defined quality standards.
    """
    stats = analyze_dataset_from_ground_truth(dataset)

    print("\n\n" + "=" * 25 + " Dataset Metrics Analysis " + "=" * 25)
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"- {key}:")
            for sub_key, sub_value in sorted(value.items()):
                print(f"    - {sub_key}: {sub_value}")
        else:
            print(f"- {key}: {value}")
    print("=" * 80)

    is_high_quality, messages = verify_dataset_quality(stats)

    if not is_high_quality:
        print("\n=== Quality Issues Found ===")
        for msg in messages:
            print(f"- {msg}")

    assert (
        is_high_quality
    ), f"The dataset does not meet quality criteria: {'; '.join(messages)}"
