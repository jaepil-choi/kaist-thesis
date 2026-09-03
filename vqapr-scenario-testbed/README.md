# vqapr-scenario-testbed (kaist-thesis) — scenario friction evaluation

**Evaluator-facing.** The agent under evaluation reads `AGENTS.md` and gets the scenario from you.
`AGENTS.md` forbids it from reading this file.

This is the third generation of the vqapr testbed in this repository, and the first one built for
the post-convergence wheel. The two earlier directories (`vqapr-testbed/`, run against an editable
`0.1.0a11`; `vqapr-final-testbed/`, run 2026-08-30 against the `0.2.0a1` wheel) were deleted on
2026-09-02 and survive only in git history. Their findings went upstream:
`../../qlibx/docs/handoff/2026-08-30-final-testbed-findings.md` and `docs/issues/015`–`027`.

---

## What this is for

One question, with one new emphasis:

> Given a scenario, can an agent with **no prior knowledge of vqapr** carry it out **on its own**,
> inside a controlled directory, using only the package's public surface — and when it hits
> friction, can it tell **whose fault it was**?

The measurement is the same as before — *an agent blocked by the surface is the measurement* — but
the deliverable this time is graded on attribution. Every entry in `FINDINGS.md` says `Yes`, `No`
or `Unsure` to "Attributable to vqapr?", and `AGENTS.md` gives the agent a decision table for it.
What you are reading for afterwards:

- `Yes` entries: upstream proposals. Check each one against the surface yourself before filing.
- `No` entries: the agent's own cost. A cluster of them on one verb usually means the surface invites
  the mistake, which is a `Yes` in disguise.
- `Unsure` entries: the ones the agent could not classify. These are the most informative, because
  a real user cannot classify them either.
- `urge` entries: where the surface ran out and the agent wanted the source.

The wheel under test is a **major rework**. The qlibx convergence campaign
(`../../qlibx/docs/refactoring/2026-09-02-the-convergence-campaign.md`) changes the surface, the
registration transaction, the run record, the panel and the run layout. Treat this run as a new
baseline, not a re-measurement of run 1: the shape of friction is expected to move, and the known
issues list is rebuilt from scratch.

---

## What is deliberately absent, and what is deliberately present

**The scenario comes from you.** Either live in the session, or as a `SCENARIO.md` you drop into
this directory before starting. `SCENARIO.md` is gitignored so that no scenario is ever committed
with the testbed. Write it the way you would brief a colleague — what you want, at what scope, and
which files it should use if that matters — and nothing about how vqapr does anything. Candidate
scenarios, roughly in order of how much surface they exercise:

1. Register the daily price panel with correct knowability, scaffold a strategy, and get one run to
   complete end to end with a readable report. (The run-D scope; measures the on-ramp.)
2. The paper's PCA-residual arm: rolling PCA on a 252-day window, residuals against the loadings,
   an OU-threshold trading policy on the residual portfolios, measured against the paper's tables.
3. The FF-residual arm using the `kimchi-factor` daily series instead of PCA.
4. A universe scenario: build the point-in-time KOSPI universe from the monthly security master and
   make the strategy respect it, including delistings.

**The paper is present, and is not a brief.** `paper/deep-learning-statistical-arbitrage.md` is the
full text of Guijarro-Ordonez, Pelger & Zanotti (2025), *Deep Learning Statistical Arbitrage*
(Management Science). `AGENTS.md` tells the agent it is research input, not scope. Watch for the
agent widening the scenario by reading the paper — say so in the session rather than letting it run.

**The data is staged raw-ish and undescribed.** No column dictionary, no manifest. Working out what
is in it is part of the job, and friction there is `No` per `AGENTS.md`.

**Known issues are present, and are not a to-do list.** `FINDINGS.md` opens with a `## Known
issues` section that you fill at staging time against the wheel you built (Protocol step 0). The
agent annotates when one costs it time; it does not re-file them. Do not copy run 1's list forward —
most of it is fixed or renamed by the campaign. Read each `../../qlibx/docs/issues/` entry's status.

**Autonomy is expected.** `AGENTS.md` tells the agent to carry the scenario out end to end and to
ask you only about the scenario itself — never about how vqapr does something. If it asks you a
vqapr question anyway, do not answer it; tell it the package should be able to say, and let it record
the gap. Scenario questions ("which file is which", "is this convention acceptable") are fair, and
each one lands in `FINDINGS.md` as `Resolved by: asked`.

---

## Isolation

- **The dependency is a built wheel** — the exact `vqapr` wheel pinned in `pyproject.toml`, from
  `../../qlibx/dist/`. The `.venv` holds a released distribution: no repository, no `tests/`, no
  `docs/`, no showcase, no git history. It is a pure-Python wheel, so the module source *is* still
  physically readable under `site-packages/vqapr/`; `AGENTS.md` forbids opening it and
  `.claude/guard_boundary.py` denies any command that names `.venv` or reaches for
  `inspect.getsource`.
- **The boundary is the directory, not a list.** `AGENTS.md` forbids leaving
  `vqapr-scenario-testbed/` at all — no reading, listing, globbing, or `cd` above it, and no relative
  path that climbs out. `.claude/settings.json` adds `Read(../**)`-style denies on top of the hook.

**The extra risk here is this repository, not `qlibx`.** `guijarro-ordonez-2025-replication/` is a
completed Korean replication of the very paper in `paper/`: pipeline, variable definitions, timing
decisions, `outputs/`, and a written `docs/execution-status.md`. So are
`Deep_Learning_Statistical_Arbitrage_Code/` (the authors' own code) and `docs/markdown/summary/`.
Reading any of them lets the agent skip precisely the decisions this run exists to watch.

A defect found here is fixed upstream in `../../qlibx` and picked up by rebuilding the wheel. That
is your move, not the agent's.

---

## Layout

```
AGENTS.md         the contract: isolation, the urge rule, the attribution table, the finding format.
CLAUDE.md         @AGENTS.md — same contract for Claude Code sessions.
README.md         this file. Evaluator only; the agent is told not to read it.
FINDINGS.md       the deliverable. gitignored. You stage the header + Known issues; the agent writes the rest.
SCENARIO.md       optional, gitignored. The scenario, if you prefer to write it down rather than say it.
pyproject.toml    exact wheel pin on ../../qlibx/dist/, plus pandas/pyarrow/duckdb/numpy.
uv.lock           generated in step 0 and committed with the pin, so a run's venv is reproducible.
.python-version   3.12
.claude/          guard_boundary.py (PreToolUse deny hook) + settings.json + the skill adapter.
.agents/skills/   the installed vqapr skill. Written by `vqapr skill install` in step 0; commit it.
paper/            the paper text. gitignored — restage per the protocol below.
data/             staged inputs, ~786 MB. gitignored.
workspace/        whatever the agent registers. gitignored.
outputs/          whatever the agent produces. gitignored.
```

### What is in `data/`

Copied from this repository's own pilot extract with the paper-specific directory names stripped, so
the agent cannot read the staging itself as a hint about which paper artefact goes where.

| path | source | what it is |
|---|---|---|
| `korean_equity/adjusted_prices.parquet` | `data/kaist_pilot/canonical/common/korean_equity/` | 436 MB. Daily adjusted prices — the residual-return input |
| `korean_equity/fng_daily_share_counts.parquet`, `fng_annual_share_counts.parquet` | same | share counts for market equity |
| `korean_equity/fng_dividend_items.parquet` | same | dividends. **Note the total-return gap** — see below |
| `korean_equity/fng_statement_facts/` | same | 341 MB, partitioned by `statement_scope` × `fiscal_year`, FY2016–2026 |
| `korean_equity/sector_classification.parquet`, `industry_mapping.parquet` | same | sector/industry |
| `fng/fgsc_market_rebalance_snapshots_201801_202606.csv` | `canonical/guijarro_2025/fng/raw/` | 11 MB. Month-end point-in-time security master, 2018-01 – 2026-06 |
| `ecos/kospi_index_daily_*.json`, `rf_cd_91d_daily_*.json` | `canonical/guijarro_2025/ecos/raw/` | BOK ECOS: KOSPI index level, CD 91d risk-free |
| `kimchi-factor/kimchi_daily_{RMRF,SMB,HML,RMW,CMA,MOM}_vw_all.csv` | `data/kimchi-factor/` | daily Korean FF5+MOM series, for the FF-residual arm |

**Known gaps in the staged data**, so you can answer honestly when asked and know when the agent is
right to be stuck. These are data gaps, not vqapr findings:

- **No total return.** Prices are price-return; the dividend file is a separate items table, not a
  reinvested series. The paper's US sample uses CRSP total returns.
- **No point-in-time accounting.** `fng_statement_facts` carries latest-revision figures with no
  filing or restatement timestamps. Any accounting characteristic is a fixed-lag proxy at best.
- **The PIT security master starts 2018-01**, so a survivorship-clean universe cannot be built before
  then from these files.
- **No realized short-borrow or transaction-cost history**, which the paper's constrained trading
  policy wants.
- **No market/board column** identifying KOSPI vs KOSDAQ.

Do not volunteer these. If the agent works one out and asks, confirm it — that exchange is a finding
marked `Resolved by: asked`, and the shape of the question tells you how legible the data was.

---

## Protocol

**0. Pin, lock and stage the wheel under test.** Between runs this directory carries no venv and no
`FINDINGS.md` body, so nothing from the previous wheel leaks into the next run.

1. Build the wheel in `../../qlibx` (`uv build`; its `dist/` is gitignored there, so whatever is in
   it is whatever you last built). Make sure `pyproject.toml` here pins that exact version and
   filename — `0.2.0a2` is a placeholder from 2026-09-02 and may need to change.
2. From `vqapr-scenario-testbed/`:

   ```powershell
   uv lock
   uv sync
   uv run --no-sync vqapr skill install --into .
   ```

3. Open `FINDINGS.md` and fill the header table (wheel filename, build date, qlibx commit) and the
   `## Known issues` list from `../../qlibx/docs/issues/` — only the entries still open against this
   wheel, one line each. An empty list is valid. If `FINDINGS.md` is missing, recreate it from the
   skeleton at the end of this file.
4. Commit `pyproject.toml`, `uv.lock` and `.agents/skills/` together so the run is reproducible.
   `FINDINGS.md`, `SCENARIO.md`, `data/` and `paper/` stay uncommitted.

**1. Restage inputs** if they are missing (all gitignored). From the repository root:

```powershell
robocopy data\kaist_pilot\canonical\common\korean_equity vqapr-scenario-testbed\data\korean_equity /S
robocopy data\kaist_pilot\canonical\guijarro_2025\fng\raw vqapr-scenario-testbed\data\fng *.csv
robocopy data\kaist_pilot\canonical\guijarro_2025\ecos\raw vqapr-scenario-testbed\data\ecos *.json
robocopy data\kimchi-factor vqapr-scenario-testbed\data\kimchi-factor *.csv
copy "docs\markdown\2025 Deep Learning Statistical Arbitrage - Guijarro-Ordonez et al. (MS).md" vqapr-scenario-testbed\paper\deep-learning-statistical-arbitrage.md
```

**2. Confirm the environment and the boundary** before the agent starts, so a broken environment is
not misrecorded as a surface defect. From `vqapr-scenario-testbed/`:

```powershell
uv run --no-sync python -c "import importlib.metadata as m; print(m.version('vqapr'))"
uv run --no-sync vqapr --help
uv run --no-sync vqapr skill list --into .
echo '{"tool_name":"Bash","tool_input":{"command":"cat ../AGENTS.md"}}' | python .claude/guard_boundary.py
```

Expected: the pinned version; the top-level help (record its verb list in the `FINDINGS.md` header —
it was seven verbs at `0.2.0a1` and the campaign reshapes it); `{"current": true, "installed":
true, ...}`; and a `deny` decision from the hook.

**3. Start the agent in a fresh session** whose working directory is `vqapr-scenario-testbed/`, with
no prior vqapr context in its history. A session that has already read `qlibx/src` — or
`guijarro-ordonez-2025-replication/` — cannot be the subject. That is the one condition that
invalidates the whole run.

**4. Give the scenario and step back.** Say it once, the way you would to a colleague, or point at
`SCENARIO.md`. Then let it work. Do not pre-empt questions; do not narrate vqapr.

**5. Answer only scenario questions.** "What did you mean", "which data file is which", "is this
convention acceptable" — fair. "How does vqapr do X" — not; tell it the package should be able to
say, and let it record the gap. Every exchange should land in `FINDINGS.md` as `Resolved by: asked`.

**6. Afterwards**, triage `FINDINGS.md`. Re-check every `Yes` against the surface before filing it
upstream in `../../qlibx`. Read `Unsure` and `urge` entries closest. Note where the agent's `No`
entries cluster. Then delete `FINDINGS.md`, `SCENARIO.md`, `workspace/` and `outputs/` (or move them
out of the repository) so the next run starts clean; keep a copy of `FINDINGS.md` upstream in
`../../qlibx/docs/handoff/` the way run 1 did.

---

## Provenance of the wheel

| run | wheel | built from | outcome |
|---|---|---|---|
| kwam run | `0.2.0a1` | `qlibx@develop`, 2026-08-29 | 13 defects → `docs/issues/015`–`027` |
| run 1 (`vqapr-final-testbed/`) | `0.2.0a1`, same bytes | same | `docs/handoff/2026-08-30-final-testbed-findings.md` |
| run 2 (this directory) | `0.3.0` | `qlibx@develop@4f616f5a` (`v0.3.0`), 2026-09-03 — the convergence campaign, records `129`–`139` | run 2026-09-03, both phases (FF5+MOM K=6 OU+Thresh; then K=0/K=5 x OU+Thresh/Fourier+FFN, profiled). 17 findings, no `blocked`; 14 filed as `docs/issues/055`-`068`, of which `058` and `061` were closed the same day (records `146`, `143`). Copy: `../../qlibx/docs/handoff/2026-09-03-scenario-testbed-run-2-findings.md` |

Record the run 2 row here once the wheel is built, and mirror it in the `FINDINGS.md` header.

---

## Why the boundary is enforced by a file and not by trust

An agent that has read the source cannot un-read it, and will silently use that knowledge to recover
from a gap a real user cannot recover from. That produces a clean run with zero findings, which looks
like success and is worth nothing.

The same is true, and worse, of the existing replication in this repository: it contains not just how
the package works but what the answers are.

`AGENTS.md` names the boundary precisely so that crossing it is a visible act rather than a drift,
and gives the urge to cross it a place to go instead.

---

## `FINDINGS.md` skeleton

If the gitignored `FINDINGS.md` is missing, recreate it from this:

```markdown
# FINDINGS.md — vqapr-scenario-testbed

| | |
|---|---|
| **Wheel** | `vqapr-<version>-py3-none-any.whl` — built <date> from `qlibx@<branch>@<commit>` |
| **Skill** | `.agents/skills/vqapr/SKILL.md`, installed by `vqapr skill install --into .` |
| **Scenario** | given live / `SCENARIO.md` |

## Known issues

- **NNN** — title (one line per open ../../qlibx/docs/issues entry; the agent annotates under it)

## Findings

## Where I stopped
```
