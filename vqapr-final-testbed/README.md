# vqapr-final-testbed (kaist-thesis) — paper-replication friction evaluation

**Evaluator-facing.** The agent under evaluation reads `AGENTS.md` and is told the rest by you, live,
in the session. `AGENTS.md` forbids it from reading this file.

This is a sibling of `kwam-enhanced-index/vqapr-final-testbed/`, run against the same wheel and the
same skill, with one variable changed: **the work is a published paper's strategy rather than a
factor library the user already knew how to build.**

---

## What this is for

The kwam run asked whether a first-time user could get from `uv add vqapr` to a finished run without
friction, building something the user could describe in a sentence. It found thirteen defects, now
`docs/issues/015`–`027` upstream.

This run asks the next question:

> When the thing to be built is **specified by someone other than the user** — a paper, with its own
> vocabulary, its own timing conventions, and its own idea of what a portfolio is — can the package
> hold it?

The measurement is unchanged:

> **an agent blocked by the surface is the measurement.**

What is new is where the friction is expected to sit. A paper states a design precisely and in its
own terms: conditional latent factors, residual portfolios, a trading policy under constraints. Every
one of those is a sentence the user has *already decided* and now needs to say to the framework. The
finding this testbed is built to catch is **"the paper says X plainly and I could not say X in
vqapr"** — which `AGENTS.md` calls out as the most valuable entry the run can produce.

The output is `FINDINGS.md`, not a replication result.

---

## What is deliberately absent, and what is deliberately present

**There is no brief.** No `TASK.md`, no spec, no checklist, no data dictionary. You give the
instructions yourself, in conversation, in pieces, changing your mind if you like.

**The paper is present, and is not a brief.** `paper/deep-learning-statistical-arbitrage.md` is the
full text of Guijarro-Ordonez, Pelger & Zanotti (2025), *Deep Learning Statistical Arbitrage*
(Management Science) — the repository's current top key-paper candidate. `AGENTS.md` states
explicitly that the paper is research input: it says what the authors did, not which part of it the
agent is being asked to build, at what scope, or against which local files. Those still come from
you. Watch for the agent reading the paper and inferring a scope it was never given — that is worth
saying out loud in the session rather than silently allowing.

**The data is staged raw-ish and undescribed.** See the layout below. No column dictionary, no
`about-data.md`, no manifest. Working out what is in it is part of the job, and friction there is
`No` — not attributable to vqapr — per `AGENTS.md`.

**Known issues are present, and are not a to-do list.** `FINDINGS.md` opens with the thirteen filed
upstream. The wheel here predates every fix, so all thirteen are live. The section tells the agent to
annotate rather than re-file, and warns it not to treat the list as a budget.

---

## Isolation

Identical to the kwam testbed, with the ban widened to cover this repository's own contents:

- **The dependency is a built wheel** — `vqapr==0.2.0a1` from `../../qlibx/dist/`. The `.venv` holds
  a released distribution: no repository, no `tests/`, no `docs/`, no showcase, no git history. It is
  a pure-Python wheel, so the module source *is* still physically readable under
  `site-packages/vqapr/`; `AGENTS.md` forbids opening it and `.claude/guard_boundary.py` denies any
  command that names `.venv`.
- **The boundary is the directory, not a list.** `AGENTS.md` forbids leaving `vqapr-final-testbed/`
  at all — no reading, listing, globbing, or `cd` above it, and no relative path that climbs out.

**The extra risk here is this repository, not `qlibx`.** `guijarro-ordonez-2025-replication/` is a
completed Korean replication of the very paper being handed to the agent: pipeline, variable
definitions, timing decisions, `outputs/`, and a written `docs/execution-status.md`. So do
`Deep_Learning_Statistical_Arbitrage_Code/` (the authors' own code) and `docs/markdown/summary/`.
Reading any of them would let the agent skip precisely the decisions this run exists to watch. The
directory boundary already bans them; `AGENTS.md` names them anyway so that crossing is a visible act.

A defect found here is still fixed upstream in `../../qlibx` and picked up by rebuilding the wheel.
That is your move, not the agent's.

---

## Layout

```
AGENTS.md         the contract: isolation, the urge rule, the finding format. Overrides every other one.
CLAUDE.md         @AGENTS.md — same contract for Claude Code sessions.
FINDINGS.md       the deliverable. Known issues, template, and the setup findings.
README.md         this file. Evaluator only; the agent is told not to read it.
pyproject.toml    wheel dependency on ../../qlibx/dist/, plus pandas/pyarrow/duckdb/numpy.
.claude/          guard_boundary.py (PreToolUse deny hook) + settings.json + the skill adapter.
.agents/skills/   the installed vqapr skill. Written by `vqapr skill install`, not by hand.
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

**1. Restage inputs** if they are missing (both are gitignored):

```powershell
robocopy data\kaist_pilot\canonical\common\korean_equity vqapr-final-testbed\data\korean_equity /S
robocopy data\kaist_pilot\canonical\guijarro_2025\fng\raw vqapr-final-testbed\data\fng *.csv
robocopy data\kaist_pilot\canonical\guijarro_2025\ecos\raw vqapr-final-testbed\data\ecos *.json
robocopy data\kimchi-factor vqapr-final-testbed\data\kimchi-factor *.csv
copy "docs\markdown\2025 Deep Learning Statistical Arbitrage - Guijarro-Ordonez et al. (MS).md" vqapr-final-testbed\paper\deep-learning-statistical-arbitrage.md
```

**2. Confirm the boundary holds** before the agent starts, so a broken environment is not misrecorded
as a surface defect. Run from `vqapr-final-testbed/`:

```powershell
uv run --no-sync python -c "import importlib.metadata as m; print(m.version('vqapr'))"
uv run --no-sync vqapr --help
uv run --no-sync vqapr skill list --into .
```

Expected: `0.2.0a1`; the seven-verb help; `{"current": true, "installed": true, ...}`.

**3. Start the agent in a fresh session** whose working directory is `vqapr-final-testbed/`, with no
prior vqapr context in its history. A session that has already read `qlibx/src` — or
`guijarro-ordonez-2025-replication/` — cannot be the subject. That is the one condition that
invalidates the whole run.

**4. Drive it yourself.** Say what you want built the way you would tell a colleague. Do not paste a
specification; do not pre-empt the questions. When it asks something the package should have
answered, answer it *and* make sure the exchange lands in `FINDINGS.md` marked `Resolved by: asked`.
The question is the data.

**5. Do not help past that.** Answering "what did you mean", "which data file is which", and "is this
convention acceptable" is fair — that is the user's job, and known issue 027 says the agent should be
asking more of it, not less. Answering "how does vqapr do X" is the measurement leaking away.

**6. Afterwards**, triage `FINDINGS.md`. `Attributable to vqapr? Yes` entries become upstream
proposals in the qlibx repo. `urge` entries deserve the closest reading. The annotations under
`KNOWN ISSUES` are the second-run evidence that prices the pending fixes.

---

## Provenance of the wheel

`vqapr-0.2.0a1-py3-none-any.whl`, built 2026-08-29 from `qlibx@develop`. It predates the entire
`015`–`027` repair campaign, which began 2026-08-30 at `develop@8d040b9e`. Whatever has merged
upstream since, **this venv has none of it.** That is deliberate: it keeps this run comparable to the
kwam run, which used the same bytes.

Rebuild only if you intend to change what is being measured — and if you do, record it in the run
metadata and expect the `KNOWN ISSUES` list to need re-checking against the new wheel.

---

## Why the boundary is enforced by a file and not by trust

An agent that has read the source cannot un-read it, and will silently use that knowledge to recover
from a gap a real user cannot recover from. That produces a clean run with zero findings, which looks
like success and is worth nothing.

The same is true, and worse, of the existing replication in this repository: it contains not just how
the package works but what the answers are.

`AGENTS.md` names the boundary precisely so that crossing it is a visible act rather than a drift,
and gives the urge to cross it a place to go instead.
