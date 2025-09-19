"""
Utility module to load test cases from a JSON file
for PII detection tests using pytest.
"""

import json
from typing import List, Dict

import pytest


def load_test_cases(dataset_path: str = "dataset.json") -> List[Dict]:
    """Loads test cases from the dataset JSON file."""
    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        pytest.fail(f"Dataset file not found: {dataset_path}")
        return []
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON in dataset file: {e}")
        return []
