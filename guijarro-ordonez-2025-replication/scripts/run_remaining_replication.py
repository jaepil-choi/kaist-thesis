"""Run all remaining DLSA experiments and output builders sequentially."""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from guijarro_ordonez_replication.orchestration import main  # noqa: E402


if __name__ == "__main__":
    main()
