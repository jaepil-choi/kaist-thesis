from pathlib import Path

from guijarro_ordonez_replication.registry import load_registry, status_counts


PROJECT = Path(__file__).resolve().parents[1]


def test_registry_covers_every_main_and_appendix_output() -> None:
    registry = load_registry(PROJECT / "config" / "output-registry.yml")

    assert len(registry["paper_outputs"]) == 45
    assert status_counts(registry)["implemented_core_only"] == 0
    assert {item["section"] for item in registry["paper_outputs"]} == {
        "main",
        "appendix",
    }
