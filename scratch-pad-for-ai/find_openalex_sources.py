import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from dotenv import load_dotenv

load_dotenv()
import pyalex
from pyalex import Sources

pyalex.config.api_key = os.environ.get("OPENALEX_API_KEY")

journals = [
    "Journal of Finance",
    "Journal of Financial Economics",
    "Review of Financial Studies",
    "Journal of Financial and Quantitative Analysis",
    "Review of Finance",
    "Management Science",
    "Review of Asset Pricing Studies",
    "Journal of Banking and Finance",
    "Journal of Financial Intermediation",
    "Journal of Financial Markets",
    "Journal of Empirical Finance",
    "Financial Management",
]

for name in journals:
    res = Sources().search(name).filter(type="journal").get(per_page=5)
    print("=" * 90)
    print("QUERY:", name)
    for s in res:
        sid = s["id"].replace("https://openalex.org/", "")
        print(f"  {sid:12s} | {s['display_name']!r:60s} | issn_l={s.get('issn_l')} | works={s.get('works_count')} | host={ (s.get('host_organization_name') or '')[:30] }")
