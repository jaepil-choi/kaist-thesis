import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from dotenv import load_dotenv

load_dotenv()
import pyalex
from pyalex import Works

pyalex.config.api_key = os.environ.get("OPENALEX_API_KEY")

# All 12 tier 1-3 journals, Review of Finance uses 2 source IDs (historical split)
ALL_SOURCE_IDS = [
    "S5353659",     # Journal of Finance
    "S149240962",   # Journal of Financial Economics
    "S170137484",   # Review of Financial Studies
    "S193228710",   # Journal of Financial and Quantitative Analysis
    "S49857371",    # Review of Finance (as "European Finance Review", pre-rename)
    "S131117787",   # Review of Finance (post-rename continuation)
    "S33323087",    # Management Science
    "S2735409286",  # Review of Asset Pricing Studies
    "S2876017",     # Journal of Banking and Finance
    "S5984737",     # Journal of Financial Intermediation
    "S127646213",   # Journal of Financial Markets
    "S145875555",   # Journal of Empirical Finance
    "S157946625",   # Financial Management
]

works = (
    Works()
    .filter(primary_location={"source": {"id": "|".join(ALL_SOURCE_IDS)}})
    .search("fund constraint")
    .filter(from_publication_date="2015-01-01", to_publication_date="2026-12-31")
    .get()
)
print("Total found:", len(works))
for w in works[:8]:
    print("-" * 90)
    print("title:", w["title"])
    print("journal:", w["primary_location"]["source"]["display_name"] if w.get("primary_location") and w["primary_location"].get("source") else None)
    print("year:", w["publication_year"], "doi:", w.get("doi"))
    print("abstract:", (w["abstract"] or "")[:150] if w.get("abstract_inverted_index") else "(none)")

# Test reference + citation lookups on the first result
w0 = works[0]
ref_ids = w0["referenced_works"][:5]
print("\n--- Sample referenced works (titles) ---")
if ref_ids:
    refs = Works()[ref_ids]
    for r in refs:
        print(" -", r["title"], f"({r['publication_year']})")

wid = w0["id"].replace("https://openalex.org/", "")
print(f"\n--- Papers citing {w0['title']!r} ---")
citing = Works().filter(cites=wid).get(per_page=5)
print("citing count (this page):", len(citing))
for c in citing[:3]:
    print(" -", c["title"], f"({c['publication_year']})")
