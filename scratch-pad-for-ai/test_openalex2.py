import os, sys, io
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

load_dotenv()
import pyalex
from pyalex import Works

pyalex.config.api_key = os.environ.get("OPENALEX_API_KEY")

sid_list = ["S5353659", "S149240962", "S170137484"]

works = (
    Works()
    .filter(primary_location={"source": {"id": "|".join(sid_list)}})
    .search("fund constraint")
    .filter(from_publication_date="2015-01-01", to_publication_date="2026-12-31")
    .get()
)
print("Found:", len(works))
w = works[0]
print("keys:", sorted(w.keys()))
print()
print("has abstract_inverted_index key:", "abstract_inverted_index" in w)
print("abstract_inverted_index value (truncated):", str(w.get("abstract_inverted_index"))[:300])
print("abstract attr:", w.get("abstract"))

print()
print("--- fetch single work by id to compare ---")
wid = w["id"].replace("https://openalex.org/", "")
single = Works()[wid]
print("single has abstract_inverted_index:", "abstract_inverted_index" in single)
print("single abstract:", (single.get("abstract") or "")[:300])
