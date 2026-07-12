"""
Scratch test: verify pybliometrics ScopusSearch works end-to-end with
non-interactive init() using ELSEVIER_API_KEY from .env.
"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["ELSEVIER_API_KEY"]

import pybliometrics.scopus as scopus
scopus.init(keys=[api_key])

from pybliometrics.scopus import ScopusSearch

query = "TITLE-ABS-KEY(fund AND constraint*) AND PUBYEAR > 2020 AND PUBYEAR < 2026 AND DOCTYPE(ar)"

search = ScopusSearch(query, verbose=True, subscriber=False, count=25)

print(f"Result count: {search.get_results_size()}")

results = search.results
print(f"Number of results fetched: {len(results) if results else 0}")

if results:
    r0 = results[0]
    print("\n--- First result fields ---")
    print(r0._fields)
    print("\n--- First result ---")
    print(r0)
