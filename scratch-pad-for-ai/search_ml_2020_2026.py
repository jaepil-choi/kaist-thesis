import sys, csv
sys.path.insert(0, ".claude/skills/paper-search/scripts")
from openalex_client import search_papers

results = search_papers("machine learning", tiers=None, year_from=2020, year_to=2026, per_page=50)
results_sorted = sorted(results, key=lambda x: -(x['cited_by_count'] or 0))

for r in results_sorted:
    print(f"[{r['year']}] {r['title'][:90]} - {r['journal']} (cited {r['cited_by_count']})")

print(f"\nTotal: {len(results)}")

out_path = "scratch-pad-for-ai/outputs/ml_2020_2026.csv"
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "openalex_id", "title", "journal", "year", "cited_by_count",
        "doi", "has_abstract", "referenced_works_count"
    ])
    writer.writeheader()
    for r in results:
        writer.writerow(r)
print(f"Saved to {out_path}", file=sys.stderr)
