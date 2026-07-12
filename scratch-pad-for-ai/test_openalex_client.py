"""Sanity check the packaged skill helper module end-to-end."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"C:\Users\chlje\DevProjects\kaist-thesis\.claude\skills\paper-search\scripts")

from openalex_client import search_papers, get_abstract, get_references, get_citing_papers

print("=== search_papers (tier 1+2, 'fund constraint', 2015-2026) ===")
results = search_papers("fund constraint", tiers=[1, 2], year_from=2015, year_to=2026)
print(f"{len(results)} results")
for r in results[:5]:
    print(" -", r["title"], f"[{r['journal']}, {r['year']}]", "abstract?" , r["has_abstract"])

target = next(r for r in results if r["has_abstract"])
print(f"\n=== get_abstract for: {target['title']!r} ===")
abstract = get_abstract(target["openalex_id"])
print((abstract or "")[:250])

print(f"\n=== get_references (limit 5) ===")
refs = get_references(target["openalex_id"], limit=5)
for r in refs:
    print(" -", r["title"], f"({r['year']})")

print(f"\n=== get_citing_papers (limit via per_page=5) ===")
citing = get_citing_papers(target["openalex_id"], per_page=5)
for c in citing:
    print(" -", c["title"], f"({c['year']})")
