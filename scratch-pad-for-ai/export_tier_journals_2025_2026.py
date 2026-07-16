"""Export all 2025-2026 works from the configured tier 1-4 journals.

The complete OpenAlex metadata export is saved alongside a transparent,
keyword-based machine-learning shortlist for subsequent literature review.
"""
from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path
from typing import Any

import truststore
from pyalex import Works


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "scratch-pad-for-ai" / "outputs"
FULL_OUTPUT = OUTPUT_DIR / "tier1-4-papers-2025-2026.csv"
ML_OUTPUT = OUTPUT_DIR / "tier1-4-machine-learning-papers-2025-2026.csv"

# OpenAlex publication_date uses the earliest publication date it knows
# (often online-first), not necessarily the later print-issue date.
DATE_FROM = "2025-01-01"
DATE_TO = "2026-12-31"

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
truststore.inject_into_ssl()
sys.path.insert(
    0,
    str(REPO_ROOT / ".agents" / "skills" / "paper-search" / "scripts"),
)

from openalex_client import (  # noqa: E402
    get_abstract,
    init,
    load_journal_tiers,
    source_ids_for_tiers,
)


ML_PATTERNS = {
    "machine learning": r"\bmachine[- ]learning\b",
    "deep learning": r"\bdeep[- ]learning\b",
    "artificial intelligence": r"\bartificial intelligence\b",
    "generative AI": r"\bgenerative (?:ai|artificial intelligence)\b",
    "large language model": r"\b(?:large language model|llm)s?\b",
    "natural language processing": r"\b(?:natural language processing|nlp)\b",
    "textual analysis": r"\b(?:textual|text|sentiment) analysis\b",
    "neural network": r"\bneural networks?\b",
    "transformer": r"\btransformer(?:-based)?\b",
    "random forest": r"\brandom forests?\b",
    "gradient boosting": r"\bgradient[- ]boost(?:ed|ing)\b",
    "XGBoost": r"\bxgboost\b",
    "LightGBM": r"\blightgbm\b",
    "support vector machine": r"\bsupport vector (?:machine|regression)s?\b",
    "reinforcement learning": r"\breinforcement learning\b",
    "supervised learning": r"\bsupervised learning\b",
    "unsupervised learning": r"\bunsupervised learning\b",
    "explainable AI": r"\b(?:explainable ai|interpretable machine learning|shap(?:ley)?)\b",
    "computer vision": r"\bcomputer vision\b",
}

FIELDS = [
    "openalex_id",
    "title",
    "journal",
    "configured_journal",
    "tier",
    "source_id",
    "publication_year",
    "publication_date",
    "type",
    "doi",
    "landing_page_url",
    "volume",
    "issue",
    "first_page",
    "last_page",
    "authors",
    "author_openalex_ids",
    "institutions",
    "countries",
    "corresponding_authors",
    "language",
    "abstract",
    "has_abstract",
    "keywords",
    "primary_topic",
    "topics",
    "cited_by_count",
    "referenced_works_count",
    "related_works_count",
    "fwci",
    "citation_percentile",
    "is_oa",
    "oa_status",
    "oa_url",
    "has_fulltext",
    "fulltext_origin",
    "locations_count",
    "is_retracted",
    "is_paratext",
    "ml_match",
    "ml_relevance_score",
    "ml_match_terms",
]


def normalize_openalex_id(value: str | None) -> str:
    return (value or "").replace("https://openalex.org/", "")


def unique_join(values: list[str]) -> str:
    return " | ".join(dict.fromkeys(value.strip() for value in values if value and value.strip()))


def source_lookup() -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for tier, journals in load_journal_tiers().items():
        for journal in journals:
            for source_id in journal["source_ids"]:
                lookup[source_id] = {
                    "tier": tier,
                    "configured_journal": journal["name"],
                }
    return lookup


def reconstruct_abstract(work: dict[str, Any]) -> str:
    try:
        return get_abstract(work) or ""
    except (KeyError, TypeError):
        return ""


def ml_classification(
    title: str,
    abstract: str,
    keywords: list[str],
    topics: list[str],
) -> tuple[bool, int, str]:
    sections = {
        "title": title,
        "keywords_topics": " ".join(keywords + topics),
        "abstract": abstract,
    }
    matched_terms: list[str] = []
    score = 0
    for label, pattern in ML_PATTERNS.items():
        section_hits = [
            section
            for section, text in sections.items()
            if text and re.search(pattern, text, flags=re.IGNORECASE)
        ]
        if not section_hits:
            continue
        matched_terms.append(label)
        if "title" in section_hits:
            score += 5
        if "keywords_topics" in section_hits:
            score += 3
        if "abstract" in section_hits:
            score += 1
    return bool(matched_terms), score, " | ".join(matched_terms)


def row_from_work(
    work: dict[str, Any],
    journals: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    source_id = normalize_openalex_id(source.get("id"))
    journal_config = journals.get(source_id, {})
    biblio = work.get("biblio") or {}
    open_access = work.get("open_access") or {}

    authors: list[str] = []
    author_ids: list[str] = []
    institutions: list[str] = []
    countries: list[str] = []
    corresponding_authors: list[str] = []
    for authorship in work.get("authorships") or []:
        author = authorship.get("author") or {}
        name = author.get("display_name") or ""
        authors.append(name)
        author_ids.append(normalize_openalex_id(author.get("id")))
        if authorship.get("is_corresponding") and name:
            corresponding_authors.append(name)
        for institution in authorship.get("institutions") or []:
            institutions.append(institution.get("display_name") or "")
            country_code = institution.get("country_code") or ""
            if country_code:
                countries.append(country_code)
        countries.extend(authorship.get("countries") or [])

    keyword_names = [
        keyword.get("display_name") or ""
        for keyword in work.get("keywords") or []
    ]
    topic_names = [
        topic.get("display_name") or ""
        for topic in work.get("topics") or []
    ]
    primary_topic = (work.get("primary_topic") or {}).get("display_name") or ""
    abstract = reconstruct_abstract(work)
    title = work.get("title") or ""
    ml_match, ml_score, ml_terms = ml_classification(
        title,
        abstract,
        keyword_names,
        topic_names,
    )
    citation_percentile = work.get("citation_normalized_percentile") or {}

    return {
        "openalex_id": normalize_openalex_id(work.get("id")),
        "title": title,
        "journal": source.get("display_name") or "",
        "configured_journal": journal_config.get("configured_journal", ""),
        "tier": journal_config.get("tier", ""),
        "source_id": source_id,
        "publication_year": work.get("publication_year") or "",
        "publication_date": work.get("publication_date") or "",
        "type": work.get("type") or "",
        "doi": work.get("doi") or "",
        "landing_page_url": primary_location.get("landing_page_url") or "",
        "volume": biblio.get("volume") or "",
        "issue": biblio.get("issue") or "",
        "first_page": biblio.get("first_page") or "",
        "last_page": biblio.get("last_page") or "",
        "authors": unique_join(authors),
        "author_openalex_ids": unique_join(author_ids),
        "institutions": unique_join(institutions),
        "countries": unique_join(countries),
        "corresponding_authors": unique_join(corresponding_authors),
        "language": work.get("language") or "",
        "abstract": abstract,
        "has_abstract": bool(abstract),
        "keywords": unique_join(keyword_names),
        "primary_topic": primary_topic,
        "topics": unique_join(topic_names),
        "cited_by_count": work.get("cited_by_count") or 0,
        "referenced_works_count": work.get("referenced_works_count") or 0,
        "related_works_count": len(work.get("related_works") or []),
        "fwci": work.get("fwci") if work.get("fwci") is not None else "",
        "citation_percentile": citation_percentile.get("value") or "",
        "is_oa": bool(open_access.get("is_oa")),
        "oa_status": open_access.get("oa_status") or "",
        "oa_url": open_access.get("oa_url") or "",
        "has_fulltext": bool(work.get("has_fulltext")),
        "fulltext_origin": work.get("fulltext_origin") or "",
        "locations_count": work.get("locations_count") or 0,
        "is_retracted": bool(work.get("is_retracted")),
        "is_paratext": bool(work.get("is_paratext")),
        "ml_match": ml_match,
        "ml_relevance_score": ml_score,
        "ml_match_terms": ml_terms,
    }


def main() -> None:
    init()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    journals = source_lookup()
    source_ids = source_ids_for_tiers([1, 2, 3, 4])

    query = Works().filter(
        primary_location={"source": {"id": "|".join(source_ids)}},
        from_publication_date=DATE_FROM,
        to_publication_date=DATE_TO,
    )
    expected_count = query.count()
    print(f"OpenAlex reports {expected_count} works for {DATE_FROM} through {DATE_TO}.")

    rows: list[dict[str, Any]] = []
    for page_number, page in enumerate(
        query.paginate(method="cursor", per_page=200, n_max=None),
        start=1,
    ):
        rows.extend(row_from_work(work, journals) for work in page)
        print(f"Fetched page {page_number}: {len(rows)}/{expected_count}")

    # Guard against duplicate OpenAlex records appearing across cursor pages.
    deduplicated = {row["openalex_id"]: row for row in rows}
    rows = list(deduplicated.values())
    rows.sort(
        key=lambda row: (
            int(row["tier"]) if row["tier"] != "" else 99,
            row["configured_journal"],
            str(row["publication_date"]),
            row["title"],
        )
    )

    with FULL_OUTPUT.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    ml_rows = [row for row in rows if row["ml_match"]]
    ml_rows.sort(
        key=lambda row: (
            -int(row["ml_relevance_score"]),
            -int(row["cited_by_count"]),
            int(row["tier"]) if row["tier"] != "" else 99,
            row["title"],
        )
    )
    with ML_OUTPUT.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(ml_rows)

    print(f"Saved {len(rows)} works to {FULL_OUTPUT}")
    print(f"Saved {len(ml_rows)} ML-related candidates to {ML_OUTPUT}")


if __name__ == "__main__":
    main()
