"""Rebuild a similarity-ranked literature set around the eight key-paper seeds.

The script follows the OpenAlex access pattern validated by the older scratch
scripts: journal IDs are loaded from config/key-paper.yaml through the packaged
helper, search uses short full-text queries, and abstracts are reconstructed by
the helper's bracket-access implementation.
"""
from __future__ import annotations

import csv
import io
import math
import sys
from collections import defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
# Use the helper updated in commit b7c8ea3; it injects the Windows OS trust
# store so OpenAlex works behind the current TLS-inspecting network.
sys.path.insert(0, str(REPO_ROOT / ".claude" / "skills" / "paper-search" / "scripts"))

from openalex_client import (  # noqa: E402
    get_abstract,
    get_work,
    load_journal_tiers,
    search_papers,
)


SEEDS = [
    {
        "number": 1,
        "id": "W4391648532",
        "title": "Estimating Stock Market Betas via Machine Learning",
        "queries": ["stock market beta machine learning", "time varying beta forecasting"],
    },
    {
        "number": 2,
        "id": "W4402028449",
        "title": "Cross-sectional expected returns: new Fama-MacBeth regressions in the era of machine learning",
        "queries": ["Fama MacBeth machine learning", "cross sectional expected returns machine learning"],
    },
    {
        "number": 3,
        "id": "W2970643464",
        "title": "Mutual fund performance: Using bespoke benchmarks to disentangle mandates, constraints and skill",
        "queries": ["mutual fund bespoke benchmarks", "mutual fund constraints skill performance"],
    },
    {
        "number": 4,
        "id": "W3121379631",
        "title": "Institutional Investment Constraints and Stock Prices",
        "queries": ["institutional investment constraints stock prices", "delegated portfolio management anomalies"],
    },
    {
        "number": 5,
        "id": "W4385753172",
        "title": "Machine-learning the skill of mutual fund managers",
        "queries": ["machine learning mutual fund skill", "fund characteristics performance prediction"],
    },
    {
        "number": 6,
        "id": "W3121485504",
        "title": "ETF Arbitrage, Non-Fundamental Demand, and Return Predictability",
        "queries": ["ETF arbitrage return predictability", "ETF flows nonfundamental demand"],
    },
    {
        "number": 7,
        "id": "W3155965432",
        "title": "Identifying the Effect of Stock Indexing: Impetus or Impediment to Arbitrage and Price Discovery?",
        "queries": ["stock indexing price discovery", "index reconstitution arbitrage"],
    },
    {
        "number": 8,
        "id": "W4362607100",
        "title": "Earning Alpha by Avoiding the Index Rebalancing Crowd",
        "queries": ["index rebalancing return reversal", "index additions deletions alpha"],
    },
]

SEED_IDS = {seed["id"] for seed in SEEDS}
OUTPUT_DIR = REPO_ROOT / "scratch-pad-for-ai" / "outputs"


def normalize_id(value: str) -> str:
    return value.replace("https://openalex.org/", "")


def source_tier_lookup() -> dict[str, int]:
    lookup = {}
    for tier, journals in load_journal_tiers().items():
        for journal in journals:
            for source_id in journal["source_ids"]:
                lookup[source_id] = tier
    return lookup


def record_from_work(work: dict, tier_lookup: dict[str, int]) -> dict:
    source = ((work.get("primary_location") or {}).get("source") or {})
    source_id = normalize_id(source.get("id") or "")
    return {
        "openalex_id": normalize_id(work["id"]),
        "title": work.get("title") or "",
        "journal": source.get("display_name") or "",
        "tier": tier_lookup.get(source_id, ""),
        "year": work.get("publication_year") or "",
        "doi": work.get("doi") or "",
        "cited_by_count": work.get("cited_by_count") or 0,
        "abstract": get_abstract(work) or "",
    }


def record_from_search(hit: dict) -> dict:
    return {
        "openalex_id": hit["openalex_id"],
        "title": hit.get("title") or "",
        "journal": hit.get("journal") or "",
        "tier": "",
        "year": hit.get("year") or "",
        "doi": hit.get("doi") or "",
        "cited_by_count": hit.get("cited_by_count") or 0,
        "abstract": "",
    }


def rr(rank: int) -> float:
    return 1.0 / math.log2(rank + 1.0)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tier_lookup = source_tier_lookup()
    records: dict[str, dict] = {}
    seed_records: dict[str, dict] = {}
    edges = defaultdict(
        lambda: {
            "queries": set(),
            "best_search_rank": None,
            "search_score": 0.0,
            "related_rank": None,
            "related_score": 0.0,
        }
    )

    print("Fetching seed papers and OpenAlex related-work links...")
    for seed in SEEDS:
        work = get_work(seed["id"])
        seed_records[seed["id"]] = record_from_work(work, tier_lookup)

        for rank, related_id in enumerate((work.get("related_works") or [])[:12], start=1):
            candidate_id = normalize_id(related_id)
            if candidate_id in SEED_IDS:
                continue
            edge = edges[(seed["id"], candidate_id)]
            edge["related_rank"] = rank
            edge["related_score"] = rr(rank)
            try:
                related_work = get_work(candidate_id)
                records[candidate_id] = record_from_work(related_work, tier_lookup)
            except Exception as exc:  # keep the rest of the search usable
                print(f"  related-work fetch failed: {candidate_id}: {exc}", file=sys.stderr)

    print("Running journal-filtered full-text searches...")
    for seed in SEEDS:
        for query in seed["queries"]:
            hits = search_papers(
                query,
                tiers=None,
                year_from=2000,
                year_to=2026,
                per_page=25,
            )
            print(f"  seed {seed['number']} | {query!r}: {len(hits)} hits")
            for rank, hit in enumerate(hits, start=1):
                candidate_id = hit["openalex_id"]
                if candidate_id in SEED_IDS:
                    continue
                records.setdefault(candidate_id, record_from_search(hit))
                edge = edges[(seed["id"], candidate_id)]
                edge["queries"].add(query)
                if edge["best_search_rank"] is None or rank < edge["best_search_rank"]:
                    edge["best_search_rank"] = rank
                edge["search_score"] += rr(rank)

    # Fetch abstracts only for the strongest retrieval candidates per seed.
    selected_ids = set()
    for seed in SEEDS:
        candidates = []
        for (seed_id, candidate_id), edge in edges.items():
            if seed_id != seed["id"] or candidate_id not in records:
                continue
            retrieval = edge["search_score"] + 0.8 * edge["related_score"]
            candidates.append((retrieval, candidate_id))
        candidates.sort(reverse=True)
        selected_ids.update(candidate_id for _, candidate_id in candidates[:30])

    print(f"Fetching full metadata/abstracts for {len(selected_ids)} shortlisted works...")
    for index, candidate_id in enumerate(sorted(selected_ids), start=1):
        if records[candidate_id].get("abstract"):
            continue
        try:
            work = get_work(candidate_id)
            records[candidate_id] = record_from_work(work, tier_lookup)
        except Exception as exc:
            print(f"  candidate fetch failed: {candidate_id}: {exc}", file=sys.stderr)
        if index % 25 == 0:
            print(f"  processed {index}/{len(selected_ids)}")

    # Fit one shared English vocabulary so similarities are comparable across seeds.
    document_ids = list(seed_records) + sorted(selected_ids)
    documents = []
    for work_id in document_ids:
        record = seed_records.get(work_id) or records[work_id]
        title = record["title"]
        abstract = record.get("abstract") or ""
        documents.append(f"{title} {title} {title} {abstract}")

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
        max_features=30000,
    )
    matrix = vectorizer.fit_transform(documents)
    position = {work_id: index for index, work_id in enumerate(document_ids)}

    rows = []
    for seed in SEEDS:
        seed_edges = []
        for (seed_id, candidate_id), edge in edges.items():
            if seed_id != seed["id"] or candidate_id not in selected_ids:
                continue
            retrieval = edge["search_score"] + 0.8 * edge["related_score"]
            seed_edges.append((candidate_id, edge, retrieval))
        max_retrieval = max((item[2] for item in seed_edges), default=1.0)

        for candidate_id, edge, retrieval in seed_edges:
            record = records[candidate_id]
            similarity = float(
                cosine_similarity(
                    matrix[position[seed["id"]]],
                    matrix[position[candidate_id]],
                )[0, 0]
            )
            retrieval_norm = retrieval / max_retrieval if max_retrieval else 0.0
            in_journal_universe = 1.0 if record.get("tier") != "" else 0.0
            priority_score = 0.70 * similarity + 0.20 * retrieval_norm + 0.10 * in_journal_universe
            rows.append(
                {
                    "seed_number": seed["number"],
                    "seed_openalex_id": seed["id"],
                    "seed_title": seed["title"],
                    "candidate_openalex_id": candidate_id,
                    "candidate_title": record["title"],
                    "journal": record["journal"],
                    "tier": record["tier"],
                    "year": record["year"],
                    "cited_by_count": record["cited_by_count"],
                    "doi": record["doi"],
                    "text_similarity": round(similarity, 6),
                    "retrieval_score": round(retrieval, 6),
                    "priority_score": round(priority_score, 6),
                    "best_search_rank": edge["best_search_rank"] or "",
                    "related_rank": edge["related_rank"] or "",
                    "matched_queries": " | ".join(sorted(edge["queries"])),
                    "has_abstract": bool(record.get("abstract")),
                    "abstract": record.get("abstract") or "",
                }
            )

    rows.sort(key=lambda row: (row["seed_number"], -row["priority_score"], -row["text_similarity"]))
    rank_by_seed = defaultdict(int)
    for row in rows:
        rank_by_seed[row["seed_number"]] += 1
        row["rank_within_seed"] = rank_by_seed[row["seed_number"]]

    fields = [
        "seed_number",
        "rank_within_seed",
        "seed_openalex_id",
        "seed_title",
        "candidate_openalex_id",
        "candidate_title",
        "journal",
        "tier",
        "year",
        "cited_by_count",
        "doi",
        "text_similarity",
        "retrieval_score",
        "priority_score",
        "best_search_rank",
        "related_rank",
        "matched_queries",
        "has_abstract",
        "abstract",
    ]
    output_path = OUTPUT_DIR / "key-paper-similarity-ranked.csv"
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} seed-candidate rows to {output_path}")
    for seed in SEEDS:
        top = [row for row in rows if row["seed_number"] == seed["number"]][:5]
        print(f"\n=== Seed {seed['number']}: {seed['title']} ===")
        for row in top:
            print(
                f"{row['rank_within_seed']:2d}. [{row['year']}] {row['candidate_title']} "
                f"— {row['journal'] or 'unknown source'} "
                f"(tier {row['tier'] or '-'}, sim={row['text_similarity']:.3f}, "
                f"cited={row['cited_by_count']})"
            )


if __name__ == "__main__":
    main()
