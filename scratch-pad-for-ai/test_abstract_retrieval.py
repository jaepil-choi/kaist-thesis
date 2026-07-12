"""
Scratch test 3: verify AbstractRetrieval works for abstract text and references,
using a DOI from the previous search test.
"""
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ["ELSEVIER_API_KEY"]

import pybliometrics.scopus as scopus
scopus.init(keys=[api_key])

from pybliometrics.scopus import AbstractRetrieval

doi = "10.1093/rfs/hhaf036"  # Fast and Slow Arbitrage ... RFS

for view in ["META_ABS", "FULL"]:
    print("=" * 80)
    print("VIEW:", view)
    try:
        ab = AbstractRetrieval(doi, view=view)
        print("title:", ab.title)
        print("abstract:", (ab.abstract or "")[:300])
        refs = ab.references
        print("references count:", len(refs) if refs else 0)
        if refs:
            print("first ref:", refs[0])
    except Exception as e:
        print("ERROR:", type(e).__name__, e)
