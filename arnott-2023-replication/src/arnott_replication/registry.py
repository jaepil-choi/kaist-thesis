"""Validate the exact-paper output registry and Korean extension registry."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml


def load_registry(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        registry = yaml.safe_load(handle)
    outputs = registry.get("paper_outputs", [])
    expected = int(registry["paper"]["expected_output_count"])
    if len(outputs) != expected:
        raise ValueError(f"Expected {expected} paper outputs, found {len(outputs)}")
    identifiers = [item["id"] for item in outputs]
    duplicates = [key for key, count in Counter(identifiers).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate paper output ids: {duplicates}")
    return registry


def status_counts(registry: dict[str, Any], section: str) -> Counter[str]:
    return Counter(item["status"] for item in registry.get(section, []))
