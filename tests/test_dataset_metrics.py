import json
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from filters.regex_filter import filter_by_regex

DATASET_FILE = "hr_dataset.jsonl"


def load_dataset(file_path):
    prompts = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            prompts.append(json.loads(line))
    return prompts


def analyze_dataset(dataset):
    total_prompts = len(dataset)
    total_pii = 0
    type_counter = Counter()
    text_lengths = []
    texts = []

    for entry in dataset:
        text = entry["text"]
        texts.append(text)
        _, mappings = filter_by_regex(text)
        total_pii += len(mappings)
        type_counter.update([m.type for m in mappings])
        text_lengths.append(len(text.split()))

    avg_pii_per_prompt = total_pii / total_prompts if total_prompts else 0
    avg_text_length = sum(text_lengths) / total_prompts if total_prompts else 0
    max_text_length = max(text_lengths) if text_lengths else 0
    min_text_length = min(text_lengths) if text_lengths else 0

    portuguese_stop_words = [
        "a",
        "o",
        "e",
        "de",
        "do",
        "da",
        "em",
        "um",
        "uma",
        "que",
        "para",
        "com",
        "não",
        "se",
        "os",
        "as",
        "por",
        "no",
        "na",
        "dos",
        "das",
        "como",
        "mais",
        "mas",
    ]
    vectorizer = TfidfVectorizer(stop_words=portuguese_stop_words)
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
