"""
Broad retrieval (2005-2026) across config/key-paper.yaml journals to surface
topics an active fund manager (esp. running enhanced-index / benchmark-relative
strategies) would find interesting. Saves raw results to outputs/ for reuse.
"""
import sys, csv, json
sys.path.insert(0, ".claude/skills/paper-search/scripts")
from openalex_client import search_papers

QUERIES = [
    "active share closet indexing",
    "factor investing smart beta",
    "portfolio construction constraints",
    "benchmark tracking error",
    "mutual fund manager skill",
    "fund flows manager incentives",
    "ESG active portfolio",
    "machine learning portfolio management",
    "risk factor portfolio management",
    "index fund passive competition",
    "fund fees compensation",
    "momentum value anomaly investing",
    "long short equity strategy",
    "market timing fund performance",
    "fund manager turnover concentration",
    "alpha persistence fund performance",
    "enhanced index fund",
    "portfolio optimization transaction cost",
]

seen = {}
for q in QUERIES:
    results = search_papers(q, tiers=None, year_from=2005, year_to=2026, per_page=25)
    for r in results:
        oid = r["openalex_id"]
        if oid not in seen:
            r["matched_query"] = q
            seen[oid] = r
    print(f"{q!r}: {len(results)} results (cumulative unique: {len(seen)})", file=sys.stderr)

out_path = "scratch-pad-for-ai/outputs/papers_2005_2026.csv"
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "openalex_id", "title", "journal", "year", "cited_by_count",
        "doi", "matched_query", "has_abstract", "referenced_works_count"
    ])
    writer.writeheader()
    for r in seen.values():
        writer.writerow(r)

print(f"\nSaved {len(seen)} unique papers to {out_path}", file=sys.stderr)
