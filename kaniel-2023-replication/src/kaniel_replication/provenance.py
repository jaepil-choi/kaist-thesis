"""Small provenance helpers for generated artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    """Return the SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic, UTF-8 JSON manifest."""

    path.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "manifest_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(),
        **payload,
    }
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2, default=str)
        handle.write("\n")
