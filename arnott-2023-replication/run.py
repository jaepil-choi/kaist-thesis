"""Command-line entry point for the Arnott et al. (2023) replication."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from arnott_replication.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
