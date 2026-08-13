"""Integrity checks for the tracked thesis-draft asset snapshot."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
ASSETS = PROJECT / "paper-assets"
DRAFT = PROJECT / "guijarro-korea-replication.md"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_manifest_exports_all_numbered_assets() -> None:
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["source_run_id"] == "gpu-grid-20260812T215833Z"
    assert manifest["artifact_count"] == 46
    assert len(manifest["artifacts"]) == 46
    run_manifest = PROJECT / manifest["source_run_manifest"]
    assert run_manifest.is_file()
    assert _sha256(run_manifest) == manifest["source_run_manifest_sha256"]
    for artifact in manifest["artifacts"]:
        exported = PROJECT / artifact["exported_path"]
        assert exported.is_file(), artifact["exported_path"]
        assert exported.stat().st_size == artifact["bytes"]
        assert _sha256(exported) == artifact["sha256"]


def test_draft_uses_every_tracked_figure_and_no_ignored_output_links() -> None:
    draft = DRAFT.read_text(encoding="utf-8")
    links = re.findall(r"!\[[^]]*\]\(([^)]+)\)", draft)
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    expected = {
        Path(artifact["exported_path"]).relative_to("paper-assets").as_posix()
        for artifact in manifest["artifacts"]
        if artifact["kind"] == "figure"
    }

    assert len(links) == 27
    assert all(not link.startswith("outputs/") for link in links)
    assert {Path(link).relative_to("paper-assets").as_posix() for link in links} == expected
    assert all((PROJECT / link).is_file() for link in links)
