"""Configuration loading with repository-relative path resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ReplicationConfig:
    """Resolved replication configuration."""

    raw: dict[str, Any]
    repository_root: Path
    project_root: Path

    def path(self, section: str, key: str) -> Path:
        value = self.raw[section][key]
        return (self.repository_root / value).resolve()

    @property
    def output_root(self) -> Path:
        return self.path("outputs", "root")


def load_config(path: Path) -> ReplicationConfig:
    """Load YAML and resolve paths from the parent repository root."""

    config_path = path.resolve()
    project_root = config_path.parent.parent
    repository_root = project_root.parent
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"Configuration must be a mapping: {config_path}")
    return ReplicationConfig(
        raw=raw,
        repository_root=repository_root,
        project_root=project_root,
    )
