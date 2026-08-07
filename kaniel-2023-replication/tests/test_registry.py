from pathlib import Path

from kaniel_replication.registry import load_registry, status_counts
from kaniel_replication.static_outputs import TABLE_1, TABLE_2, TABLE_B1


PROJECT = Path(__file__).resolve().parents[1]


def test_registry_has_all_paper_outputs() -> None:
    registry = load_registry(PROJECT / "config" / "output-registry.yml")
    assert len(registry["outputs"]) == 64
    assert status_counts(registry)["implemented"] == 4
    assert status_counts(registry)["implemented_proxy"] == 1
    assert status_counts(registry)["planned_proxy"] == 8
    assert {item["id"] for item in registry["outputs"]} >= {
        "fig_01",
        "fig_14",
        "fig_a_01",
        "fig_a_26",
        "table_01",
        "table_09",
        "table_a_01",
        "table_a_14",
        "table_b_01",
    }


def test_static_definition_tables_have_paper_dimensions() -> None:
    assert len(TABLE_1) == 59
    assert len(TABLE_2) == 3
    assert len(TABLE_B1) == 6
