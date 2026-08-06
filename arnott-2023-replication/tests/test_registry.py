from pathlib import Path

from arnott_replication.registry import load_registry, status_counts


PROJECT = Path(__file__).resolve().parents[1]


def test_registry_keeps_exact_paper_outputs_separate_from_extensions() -> None:
    registry = load_registry(PROJECT / "config" / "output-registry.yml")
    assert len(registry["paper_outputs"]) == 9
    assert len(registry["korea_extensions"]) == 3
    assert status_counts(registry, "korea_extensions")["implemented"] == 3
    assert status_counts(registry, "paper_outputs")["blocked_announcement"] == 3
