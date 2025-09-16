"""

Dataset analysis module for HR text prompts.

This module provides functions to load a JSONL dataset, analyze text prompts
for personally identifiable information (PII), compute statistics on PII
occurrences, text lengths, and semantic diversity, and verify dataset quality.

It includes a Pytest-compatible test to ensure the dataset is sufficiently
diverse for PII-related tasks.
"""

import json
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.core.constants import PORTUGUESE_STOP_WORDS
from src.services.regex_service import RegexService


DATASET_FILE = "hr_dataset.jsonl"
regex_service = RegexService()


def load_dataset(file_path):
    """Load the dataset from a JSONL file with improved error handling."""
    prompts = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            prompts.append(json.loads(line))
    return prompts


def analyze_dataset(dataset):
    """
    Analyze the dataset and compute statistics.

    Returns a dictionary containing:
        - total_prompts: number of text entries
        - total_pii: total PII instances found
        - pii_type_distribution: count per PII type
        - avg_pii_per_prompt: average PII per prompt
        - avg_text_length: average number of words per prompt
        - max_text_length: maximum words in a prompt
        - min_text_length: minimum words in a prompt
        - semantic_diversity: measure of semantic variation in texts
    """
    total_prompts = len(dataset)
    total_pii = 0
    type_counter = Counter()
    text_lengths = []
    texts = []

    for entry in dataset:
        text = entry["text"]
        texts.append(text)
        _, mappings = regex_service.filter_by_regex(text)
        total_pii += len(mappings)
        type_counter.update([m.type for m in mappings])
        text_lengths.append(len(text.split()))

    avg_pii_per_prompt = total_pii / total_prompts if total_prompts else 0
    avg_text_length = sum(text_lengths) / total_prompts if total_prompts else 0
    max_text_length = max(text_lengths) if text_lengths else 0
    min_text_length = min(text_lengths) if text_lengths else 0

    vectorizer = TfidfVectorizer(stop_words=PORTUGUESE_STOP_WORDS)
    tfidf_matrix = vectorizer.fit_transform(texts)
    similarity_matrix = cosine_similarity(tfidf_matrix)
    upper_tri_indices = np.triu_indices_from(similarity_matrix, k=1)
    avg_similarity = np.mean(similarity_matrix[upper_tri_indices])
    semantic_diversity = 1 - avg_similarity

    stats = {
        "total_prompts": total_prompts,
        "total_pii": total_pii,
        "pii_type_distribution": dict(type_counter),
        "avg_pii_per_prompt": avg_pii_per_prompt,
        "avg_text_length": avg_text_length,
        "max_text_length": max_text_length,
        "min_text_length": min_text_length,
        "semantic_diversity": semantic_diversity,
    }
    return stats


def verify_dataset_diversity(stats):
    """
    Evaluate the dataset statistics and check if it meets diversity criteria.

    Returns:
        - is_diverse (bool): True if dataset passes all checks
        - messages (list): list of issues found, empty if is_diverse is True
    """
    messages = []
    if stats["total_prompts"] < 50:
        messages.append("Very small dataset")
    if stats["total_pii"] < 20:
        messages.append("Few PIIs found")
    if len(stats["pii_type_distribution"]) < 2:
        messages.append("Little diversity of PII types")
    if stats["avg_text_length"] < 5:
        messages.append("Very short prompts")
    if stats["semantic_diversity"] < 0.3:
        messages.append("Semantically indiverse dataset")

    is_diverse = len(messages) == 0
    return is_diverse, messages


def test_dataset_diversity():
    """
    Pytest test to ensure the dataset is diverse enough for PII tasks.

    Loads the dataset, analyzes statistics, prints results, and asserts diversity.
    """
    dataset = load_dataset(DATASET_FILE)
    stats = analyze_dataset(dataset)

    print("\n=== Dataset Statistics ===")
    for k, v in stats.items():
        print(f"{k}: {v}")

    is_diverse, messages = verify_dataset_diversity(stats)

    if not is_diverse:
        print("\n=== Diversity issues encountered ===")
        for msg in messages:
            print(f"- {msg}")

    assert is_diverse, f"Dataset is not diverse enough: {messages}"
