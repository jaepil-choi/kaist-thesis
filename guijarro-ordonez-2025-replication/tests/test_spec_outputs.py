"""Tests for non-empirical paper output definitions."""

from __future__ import annotations

from guijarro_ordonez_replication.spec_outputs import _characteristic_table


def test_characteristic_table_has_six_categories_and_46_rows() -> None:
    table = _characteristic_table()
    assert len(table) == 46
    assert table["category"].nunique() == 6
    assert table["number"].tolist() == list(range(1, 47))
