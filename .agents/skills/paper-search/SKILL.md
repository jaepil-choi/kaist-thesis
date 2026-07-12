---
name: paper-search
description: Search top finance journals (via OpenAlex) to help pick a thesis topic and key papers -- find candidate papers by keyword within tier 1/2/3 finance journals, read their abstracts, and trace what they cite or what cites them to map out a literature. Use this whenever the user wants to brainstorm thesis topics, look for papers on a subject, ask "has anyone done X in finance", check what a paper's key references are, see what's cited a paper since publication, or generally research the academic literature for their KAIST thesis -- even if they don't say "search" or name OpenAlex explicitly.
---

# Paper Search (OpenAlex)

Helps the user research academic finance literature conversationally while
they're deciding on a thesis topic: search within a curated set of top
finance journals, read abstracts, and walk citation/reference links to
figure out which papers are worth building a thesis around.

## Why OpenAlex, not Scopus

This project also has `pybliometrics` (Scopus) installed, but Scopus's
abstract and reference retrieval (`AbstractRetrieval`) returned 401
Unauthorized when tested outside KAIST's institutional network -- Elsevier
gates that data behind IP-based subscriber recognition, not just an API
key. `ScopusSearch` metadata-only queries do work, but without abstracts
they're not useful for evaluating candidate papers.

OpenAlex is free, requires only an API key (no institutional network
needed), and provides search + abstracts + references + citations in one
place. Use OpenAlex (`pyalex`) for this skill's workflow. Don't reach for
Scopus/pybliometrics here unless the user is on KAIST's network and
specifically asks for Scopus data (e.g. citation counts formatted for a
CV, which Scopus tracks differently than OpenAlex).

## Setup

`OPENALEX_API_KEY` must be in `.env` at the repo root (free key from
https://openalex.org/settings/api). The target journal list lives in
`config/key-paper.yaml` -- tier 1/2/3 finance journals with their
pre-resolved OpenAlex Source IDs. If the user wants to add or remove a
journal, edit that file rather than hardcoding IDs elsewhere; look up new
journals' Source IDs via `Sources().search(name)` in pyalex (see gotcha
below about journals with multiple source IDs due to renames).

## Use the helper module, don't hand-roll pyalex calls

`scripts/openalex_client.py` (same directory as this file) wraps the
search/abstract/reference/citation calls and already handles the sharp
edges below. Import it rather than writing raw `pyalex` calls each time --
the fixes here were discovered the hard way and are easy to silently get
wrong again:

- **Abstract reconstruction requires bracket access.** OpenAlex doesn't
  store plaintext abstracts (legal reasons) -- it stores a word-position
  index (`abstract_inverted_index`) that pyalex reconstructs into text
  on the fly, but *only* when you access it as `work["abstract"]`. Calling
  `work.get("abstract")` bypasses that reconstruction and silently returns
  `None` even when an abstract exists. `get_abstract()` in the helper
  module does the bracket access correctly.
- **Journal filter needs OR'd source IDs in one filter call**:
  `Works().filter(primary_location={"source": {"id": "S1|S2|S3"}})`.
- **Don't call `.filter(publication_year=...)` twice** to express a range
  (`>2014` then `<2027`) -- the second call overwrites the first since
  it's the same dict key. Use `from_publication_date` /
  `to_publication_date` instead (the helper module does this).
- **Some journals span multiple OpenAlex Source IDs.** E.g. Review of
  Finance is split because OpenAlex indexes it under its pre-2003 name
  ("European Finance Review") as a separate source from the post-rename
  one -- both IDs are listed in `key-paper.yaml` and must both be
  included, or a big chunk of that journal's older articles goes missing
  from search results. If you add a journal and get suspiciously few
  results for a decades-old journal, check whether it was renamed at some
  point and search for the old name too.
- **Rate limits**: with the API key, 100,000 credits/day. List/search
  queries cost 1 credit; fetching a single work by ID (`Works()[id]`) is
  free. A typical search-and-skim session uses a handful of credits --
  don't worry about the budget in normal use, but avoid looping
  `get_abstract`/`get_references` over hundreds of results without the
  user asking for that.

## Workflow

This is a back-and-forth research conversation, not a one-shot report.
Move at the pace of the discussion -- don't dump 25 abstracts on the user
unprompted.

1. **Narrow the search.** When the user mentions a topic or keyword,
   call `search_papers(keywords, tiers=[...], year_from=..., year_to=...)`.
   Default to all tiers unless the user says otherwise; tier 1 alone is
   reasonable for a first pass on a broad topic to avoid noise. Keep
   `keywords` short (OpenAlex full-text relevance search, e.g. `"fund
   constraint"`) rather than a long boolean query.
2. **Skim results together.** Show title, journal, year -- that's enough
   for the user to say "tell me more about #3 and #7." Don't fetch
   abstracts for every hit; it's wasted work and clutters the
   conversation.
3. **Read abstracts for papers of interest.** Call `get_abstract()` for
   the ones the user flags (or the ones you judge most relevant) and
   summarize them in your own words rather than pasting the raw abstract
   verbatim -- the user is trying to build a mental map of the space, not
   collect abstracts.
4. **Trace the literature when a paper looks like a "key paper" candidate.**
   Use `get_references()` to see what foundational work it builds on, and
   `get_citing_papers()` to see what's been done since (helps gauge
   whether a research gap is still open or already well-covered). This is
   usually the point where a candidate thesis direction starts to sharpen.
5. **Iterate.** As the user's interest narrows, re-run searches with more
   specific keywords, or pull references/citations from a paper the
   previous round surfaced. Keep track of the papers the user has reacted
   positively to -- these are candidate "key papers" for the thesis intro
   / literature review.

## Example

```python
import sys
sys.path.insert(0, ".Codex/skills/paper-search/scripts")
from openalex_client import search_papers, get_abstract, get_references, get_citing_papers

results = search_papers("mutual fund flows", tiers=[1, 2], year_from=2018, year_to=2026)
# -> show user: title / journal / year for each

abstract = get_abstract(results[2]["openalex_id"])
# -> summarize for the user

refs = get_references(results[2]["openalex_id"], limit=15)
citing = get_citing_papers(results[2]["openalex_id"], per_page=15)
# -> use these to map out the surrounding literature
```
