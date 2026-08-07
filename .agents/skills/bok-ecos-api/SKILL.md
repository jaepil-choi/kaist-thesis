---
name: bok-ecos-api
description: Query and automate the Bank of Korea ECOS Open API without relying on XLS/XLSX documentation. Use for discovering Korean economic statistic table and item codes, retrieving bounded time series such as CPI/GDP/rates/FX, reading ECOS metadata or terminology, validating ECOS responses, and building reproducible ECOS data workflows.
---

# Bank of Korea ECOS API

Use the bundled CLI and text reference as the source of truth. Do not require,
open, or reconstruct the original Excel API documents.

## Core workflow

1. Confirm that `BOK_ECOS_API_KEY` exists in the environment or a project `.env`.
   Never print the key or a URL containing it.
2. Discover the statistic table instead of guessing its code:

   ```powershell
   uv run python .agents/skills/bok-ecos-api/scripts/ecos_api.py tables --contains 소비자물가
   ```

3. Inspect the selected table's item hierarchy, cycle, coverage, and unit:

   ```powershell
   uv run python .agents/skills/bok-ecos-api/scripts/ecos_api.py items 901Y010 --cycle M
   ```

4. Select explicit item codes and a bounded time window. Retrieve observations:

   ```powershell
   uv run python .agents/skills/bok-ecos-api/scripts/ecos_api.py series 901Y010 M 202501 202512 --item 00
   ```

5. Validate before using the data:
   - response service matches the request;
   - returned item codes and names match the chosen metadata;
   - `TIME` follows the requested cycle;
   - months/dates are unique and cover the expected window;
   - units are consistent;
   - numeric conversion of `DATA_VALUE` succeeds where required.
6. Preserve provenance with service name, table code/name, item code/name,
   cycle, time window, unit, retrieval date, and a redacted request template.

## Task routing

- Find tables: use `tables`; filter with `--contains`, `--cycle`, or
  `--stat-code`.
- Find item codes and coverage: use `items STAT_CODE`; filter with
  `--contains` and `--cycle`.
- Retrieve time series: use `series STAT_CODE CYCLE START END --item CODE`.
  Repeat `--item` for item-code groups 1 through 4.
- Retrieve all items only when explicitly necessary: use `series ... --all-items`
  with a narrow date range and bounded row range.
- Read headline indicators: use `key-stats`.
- Read a statistical term: use `word TERM`.
- Read statistical metadata: use `meta DATA_NAME`.
- Save machine-readable output: add `--output path.json`; use `--format csv`
  for flat row output.
- Inspect the redacted request without a network call: add `--dry-run`.

Run `uv run python .agents/skills/bok-ecos-api/scripts/ecos_api.py COMMAND --help`
for command-specific options.

## Guardrails

- Discover codes dynamically. Do not rely on remembered codes when the task
  requires current or exact data.
- Use JSON responses. Treat numeric-looking identifiers as strings.
- URL-encode every path segment. Encode unused optional item codes as `%3F`;
  a literal `?` would begin a URL query string.
- Keep row and time windows bounded. Split large requests rather than retrying
  an ECOS timeout with the same range.
- Stop on ECOS `ERROR-*` responses. Report `INFO-200` as no matching data,
  not as a fabricated empty value.
- Back off on `ERROR-602`; do not loop aggressively.
- Never include the API key in output files, logs, exceptions, or source code.

## Detailed reference

Read [references/api-reference.md](references/api-reference.md) before manually
constructing requests, interpreting response fields, handling an error code, or
using a service other than the common table → item → series workflow.