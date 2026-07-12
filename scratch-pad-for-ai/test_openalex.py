"""
Scratch test 4: verify pyalex (OpenAlex) works end-to-end:
- source lookup by journal name / ISSN
- filtered work search (journal + keyword + year range)
- abstract retrieval (reconstructed from inverted index)
- outgoing references (referenced_works) and incoming citations (cites filter)
"""
import os
from dotenv import load_dotenv

load_dotenv()
openalex_key = os.environ.get("OPENALEX_API_KEY")
print("Have OpenAlex key:", bool(openalex_key))

import pyalex
from pyalex import Works, Sources

pyalex.config.api_key = openalex_key
pyalex.config.email = None  # optional polite pool, key covers auth now

# 1. Find OpenAlex source IDs for a couple tier-1 journals by ISSN
# Journal of Finance ISSN: 0022-1082, Journal of Financial Economics ISSN: 0304-405X
test_issns = {
    "Journal of Finance": "0022-1082",
    "Journal of Financial Economics": "0304-405X",
    "Review of Financial Studies": "0893-9454",
}

source_ids = {}
for name, issn in test_issns.items():
    res = Sources().filter(issn=issn).get()
    print(f"{name} ({issn}) -> {len(res)} source(s) found")
    if res:
        s = res[0]
        print("   id:", s["id"], "display_name:", s["display_name"])
        source_ids[name] = s["id"].replace("https://openalex.org/", "")

print("\nSource IDs:", source_ids)

# 2. Filtered search: keyword + journal + year range
sid_list = list(source_ids.values())
print("\n--- Search: fund AND constraint, in these sources, 2015-2026 ---")
works = (
    Works()
    .filter(primary_location={"source": {"id": "|".join(sid_list)}})
    .search("fund constraint")
    .filter(from_publication_date="2015-01-01", to_publication_date="2026-12-31")
    .get()
)
print(f"Found: {len(works)}")
for w in works[:5]:
    print("-" * 80)
    print("title:", w["title"])
    print("year:", w["publication_year"], "doi:", w.get("doi"))
    print("abstract:", (w.get("abstract") or "")[:200])
    print("referenced_works count:", len(w.get("referenced_works") or []))
    print("cited_by_count:", w.get("cited_by_count"))
