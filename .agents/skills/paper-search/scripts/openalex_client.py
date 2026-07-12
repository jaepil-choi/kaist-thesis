"""
Thin wrapper around pyalex (OpenAlex API) for searching finance journals,
reading abstracts, and walking references/citations.

Why this exists: pyalex's `Work` object has a couple of non-obvious
behaviors (see comments below) that are easy to get wrong on the first try.
This module bakes in the fixes so callers don't have to rediscover them.

Requires OPENALEX_API_KEY in the environment (e.g. via .env + load_dotenv).
Get a free key at https://openalex.org/settings/api (100,000 credits/day
with a key vs. 100/day without). List queries (search/filter) cost 1
credit each; fetching a single work by ID is free.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

import pyalex
from pyalex import Works, Sources

# Resolve config/key-paper.yaml relative to the repo root (three levels up
# from .claude/skills/paper-search/scripts/).
_REPO_ROOT = Path(__file__).resolve().parents[4]
_KEY_PAPER_CONFIG = _REPO_ROOT / "config" / "key-paper.yaml"

_initialized = False


def init() -> None:
    """Load .env and set the OpenAlex API key. Safe to call repeatedly."""
    global _initialized
    if _initialized:
        return
    load_dotenv()
    api_key = os.environ.get("OPENALEX_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENALEX_API_KEY not found in environment. Add it to .env "
            "(get a free key at https://openalex.org/settings/api)."
        )
    pyalex.config.api_key = api_key
    _initialized = True


def load_journal_tiers(config_path: Path | str = _KEY_PAPER_CONFIG) -> dict[int, list[dict]]:
    """
    Load config/key-paper.yaml. Returns {tier_int: [{"name": ..., "issn_l": ...,
    "source_ids": [...]}, ...]}.
    """
    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return {int(tier): journals for tier, journals in raw["tiers"].items()}


def source_ids_for_tiers(tiers: list[int] | None = None) -> list[str]:
    """
    Flatten source_ids across the requested tiers (default: all tiers).
    Note some journals (e.g. Review of Finance) legitimately have more than
    one source_id because OpenAlex split their history across a journal
    rename -- always include all ids listed for a journal, don't dedupe
    down to "the" id.
    """
    journal_tiers = load_journal_tiers()
    selected_tiers = tiers or list(journal_tiers.keys())
    ids: list[str] = []
    for tier in selected_tiers:
        for journal in journal_tiers.get(tier, []):
            ids.extend(journal["source_ids"])
    return ids


def search_papers(
    keywords: str,
    tiers: list[int] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    per_page: int = 25,
) -> list[dict[str, Any]]:
    """
    Search for papers by keyword within the configured journal tiers.

    `keywords` is passed to OpenAlex's full-text `.search()` (title/abstract/
    fulltext relevance search) -- pass a short phrase like "fund constraint",
    not a boolean query string.

    Returns a list of lightweight dicts (title, journal, year, doi,
    openalex_id, cited_by_count, has_abstract). Call get_abstract() on
    entries of interest to fetch the actual abstract text -- doing it here
    for every result would be wasteful for a broad search.
    """
    init()
    source_ids = source_ids_for_tiers(tiers)

    query = Works().filter(primary_location={"source": {"id": "|".join(source_ids)}})
    if keywords:
        query = query.search(keywords)
    if year_from or year_to:
        date_filter = {}
        if year_from:
            date_filter["from_publication_date"] = f"{year_from}-01-01"
        if year_to:
            date_filter["to_publication_date"] = f"{year_to}-12-31"
        query = query.filter(**date_filter)

    results = query.get(per_page=per_page)

    out = []
    for w in results:
        source = (w.get("primary_location") or {}).get("source") or {}
        out.append({
            "openalex_id": w["id"].replace("https://openalex.org/", ""),
            "title": w["title"],
            "journal": source.get("display_name"),
            "year": w["publication_year"],
            "doi": w.get("doi"),
            "cited_by_count": w.get("cited_by_count"),
            "has_abstract": bool(w.get("abstract_inverted_index")),
            "referenced_works_count": w.get("referenced_works_count"),
        })
    return out


def get_work(openalex_id_or_doi: str) -> dict:
    """Fetch a single work by OpenAlex ID (e.g. 'W123...') or DOI. Free (0 credits)."""
    init()
    return Works()[openalex_id_or_doi]


def get_abstract(work: dict | str) -> str | None:
    """
    Return the human-readable abstract for a work.

    IMPORTANT: pyalex reconstructs the abstract on the fly from
    `abstract_inverted_index` only when you access it via bracket indexing
    (`work["abstract"]`), not via `.get("abstract")` or `work.get(...)`.
    The dict-style `.get()` bypasses the `Work` object's custom
    `__getitem__` and will silently return None even when an abstract
    exists. This function does the bracket access for you so callers don't
    get bitten by this.

    Accepts either an already-fetched work dict or an id/DOI string.
    Returns None if the work genuinely has no indexed abstract (this is
    normal -- publishers don't always provide one to OpenAlex).
    """
    init()
    if isinstance(work, str):
        work = get_work(work)
    if not work.get("abstract_inverted_index"):
        return None
    return work["abstract"]


def get_references(work: dict | str, limit: int | None = None) -> list[dict]:
    """
    Return the papers a work cites (outgoing references), as lightweight
    dicts (title, year, doi, openalex_id). `work["referenced_works"]` is
    just a list of OpenAlex IDs -- this batch-fetches their metadata.
    """
    init()
    if isinstance(work, str):
        work = get_work(work)
    ref_ids = work.get("referenced_works") or []
    if limit:
        ref_ids = ref_ids[:limit]
    if not ref_ids:
        return []
    refs = Works()[ref_ids]
    return [
        {
            "openalex_id": r["id"].replace("https://openalex.org/", ""),
            "title": r["title"],
            "year": r["publication_year"],
            "doi": r.get("doi"),
        }
        for r in refs
    ]


def get_citing_papers(work: dict | str, per_page: int = 25) -> list[dict]:
    """
    Return papers that cite this work (incoming citations), newest research
    that builds on it. Useful for checking whether a candidate "key paper"
    already has a well-trodden follow-up literature (crowded) or is still
    relatively unexploited (a gap worth filling).
    """
    init()
    work_id = work["id"].replace("https://openalex.org/", "") if isinstance(work, dict) else work
    citing = Works().filter(cites=work_id).get(per_page=per_page)
    return [
        {
            "openalex_id": c["id"].replace("https://openalex.org/", ""),
            "title": c["title"],
            "year": c["publication_year"],
            "doi": c.get("doi"),
        }
        for c in citing
    ]
