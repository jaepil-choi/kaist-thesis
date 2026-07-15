"""Export references and citing papers for the eight key-paper seeds."""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# This is the helper version updated in commit b7c8ea3 to use truststore and
# therefore works behind the current TLS-inspecting network.
sys.path.insert(0, str(REPO_ROOT / ".claude" / "skills" / "paper-search" / "scripts"))

from openalex_client import get_citing_papers, get_references  # noqa: E402


SEEDS = [
    (1, "W4391648532", "Estimating Stock Market Betas via Machine Learning"),
    (2, "W4402028449", "Cross-sectional expected returns: new Fama-MacBeth regressions in the era of machine learning"),
    (3, "W2970643464", "Mutual fund performance: Using bespoke benchmarks to disentangle mandates, constraints and skill"),
    (4, "W3121379631", "Institutional Investment Constraints and Stock Prices"),
    (5, "W4385753172", "Machine-learning the skill of mutual fund managers"),
    (6, "W3121485504", "ETF Arbitrage, Non-Fundamental Demand, and Return Predictability"),
    (7, "W3155965432", "Identifying the Effect of Stock Indexing: Impetus or Impediment to Arbitrage and Price Discovery?"),
    (8, "W4362607100", "Earning Alpha by Avoiding the Index Rebalancing Crowd"),
]


def main() -> None:
    output_dir = REPO_ROOT / "scratch-pad-for-ai" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for number, seed_id, seed_title in SEEDS:
        citing = get_citing_papers(seed_id, per_page=50)
        references = get_references(seed_id, limit=50)
        print(f"seed {number}: {len(citing)} citing, {len(references)} references exported")
        for relation, papers in (("citing", citing), ("reference", references)):
            for paper in papers:
                rows.append(
                    {
                        "seed_number": number,
                        "seed_openalex_id": seed_id,
                        "seed_title": seed_title,
                        "relation": relation,
                        "paper_openalex_id": paper.get("openalex_id") or "",
                        "paper_title": paper.get("title") or "",
                        "year": paper.get("year") or "",
                        "doi": paper.get("doi") or "",
                    }
                )

    output_path = output_dir / "key-paper-citation-neighborhood.csv"
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} rows to {output_path}")

    for number, _, title in SEEDS:
        print(f"\n=== Seed {number}: {title} — citing papers ===")
        for row in [r for r in rows if r["seed_number"] == number and r["relation"] == "citing"][:20]:
            print(f"[{row['year']}] {row['paper_title']}")


if __name__ == "__main__":
    main()
