from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync_replication_draft.py"
SPEC = importlib.util.spec_from_file_location("sync_replication_draft", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_replace_nth_table_preserves_surrounding_text() -> None:
    source = "anchor\n\n| A |\n| --- |\n| old |\n\nmiddle\n\n| B |\n| --- |\n| old2 |\n\nend"
    updated = MODULE._replace_nth_table(source, "anchor", "| B |\n| --- |\n| new |", 1)
    assert "| old |" in updated
    assert "| new |" in updated
    assert updated.endswith("end")


def test_factor_key_supports_current_and_legacy_pca5() -> None:
    assert MODULE._factor_key("Stock returns K0") == ("stock", 0)
    assert MODULE._factor_key("PCA") == ("pca", 5)
    assert MODULE._factor_key("PCA10") == ("pca", 10)
    assert MODULE._factor_key("Korean FF3 average residual") == ("ff", 3)
