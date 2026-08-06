"""Small provenance helpers for generated empirical outputs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest(
    path: Path,
    *,
    command: str,
    inputs: dict[str, Path],
    outputs: list[Path],
    parameters: dict[str, Any],
    limitations: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "inputs": {
            key: {
                "path": str(value),
                "bytes": value.stat().st_size,
                "sha256": sha256(value),
            }
            for key, value in inputs.items()
        },
        "outputs": [str(value) for value in outputs],
        "parameters": parameters,
        "limitations": limitations,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
