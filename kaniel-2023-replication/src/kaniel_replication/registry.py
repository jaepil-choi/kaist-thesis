"""Output registry validation and status reporting."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml


def load_registry(path: Path) -> dict[str, Any]:
    """Load and validate the 64-output replication registry."""

    with path.open("r", encoding="utf-8") as handle:
        registry = yaml.safe_load(handle)
    outputs = registry.get("outputs", [])
    expected = int(registry["paper"]["expected_output_count"])
    ids = [item["id"] for item in outputs]
    if len(outputs) != expected:
        raise ValueError(f"Expected {expected} outputs, found {len(outputs)}")
    duplicates = [key for key, count in Counter(ids).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate output ids: {duplicates}")
    return registry


def status_counts(registry: dict[str, Any]) -> Counter[str]:
    """Count outputs by implementation status."""

    return Counter(item["status"] for item in registry["outputs"])
