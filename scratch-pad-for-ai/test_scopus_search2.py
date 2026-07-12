"""
Scratch test 2: verify SRCID-filtered ScopusSearch (flattened to one line)
and check whether `description` (abstract) is populated in search results.
"""
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ["ELSEVIER_API_KEY"]

import pybliometrics.scopus as scopus
scopus.init(keys=[api_key])

from pybliometrics.scopus import ScopusSearch

SRC_IDS = [17500, 24379, 16161, 80370, 16160, 21307, 21100926577, 17472, 28996, 17528, 17499]
src_clause = " OR ".join(f"SRCID({sid})" for sid in SRC_IDS)

query = f"({src_clause}) AND TITLE-ABS-KEY(fund AND constraint*) AND PUBYEAR > 2014 AND PUBYEAR < 2027 AND DOCTYPE(ar)"
print("QUERY:", query)

search = ScopusSearch(query, verbose=True, subscriber=False, count=25)
print(f"\nResult count: {search.get_results_size()}")

results = search.results
print(f"Fetched: {len(results) if results else 0}")

if results:
    for r in results[:5]:
        print("-" * 80)
        print("title:", r.title)
        print("journal:", r.publicationName, "source_id:", r.source_id)
        print("coverDate:", r.coverDate)
        print("doi:", r.doi)
        print("description (abstract):", (r.description or "")[:200])
