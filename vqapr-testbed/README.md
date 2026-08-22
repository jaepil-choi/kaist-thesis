# vqapr-testbed — Guijarro-Ordonez et al. (2025) on the framework

Reproducing `../guijarro-ordonez-2025-replication/` on `vqapr` instead of its own bespoke
pipeline, and treating **the framework** as the thing under test rather than the paper.

The paper is Guijarro-Ordonez, Pelger and Zanotti (2025), "Deep Learning Statistical Arbitrage",
*Management Science*: residuals from PCA/IPCA, then OU / Fourier+FFN / CNN+Transformer trading
policies on those residuals. The Korean replication next door already produces numbers. This
directory exists to find out what the framework costs a replication that already works.

---

## Why this exists

Three questions, in order of how much they decide.

### 1. Can an agent that has never seen vqapr get from raw data to a reproduced paper?

**This is the point, and it is spent the moment it is read.** The previous testbed
(`kwam-enhanced-index/vqapr-testbed/`) was built by an agent that had already been through the
framework's PRD, its architecture document and several rounds of its failures. That agent could
not tell which parts were obvious and which parts it had simply learned the hard way.

So the value here is in a **fresh** agent's confusion, and it survives exactly one attempt. Whoever
starts this should:

- work from the installed package, its docstrings and `docs/` alone — not from memory of the other
  testbed, and not by reading `qlibx/` source to work out what a function meant;
- **write down every point of friction as it happens**, in `FRICTION.md`, before resolving it. A
  question answered is worth less than the record that it had to be asked;
- treat a refusal that took more than one read to understand as a defect in the message, not as a
  gap in the reader.

What counts as friction: a required concept that had to be inferred, an error that named a stage
rather than the declaration that caused it, a registration that could be spelled two ways with no
guidance, a lookback whose semantics only became clear after a wrong result.

### 2. Which factor operations should be built into the framework?

A paper replication is mostly **cross-sectional and time-series operations on a panel**, and this
paper leans harder on them than a long-short alpha does: PCA on a rolling covariance, residual
extraction against a factor set, standardisation and ranking of 46 characteristics, rolling
z-scores, OU parameter estimation.

`vqapr.transforms` today has `cross_section`, `neutralize`, `window`, `lookthrough` and `missing`.
The question is what this paper needs that is **not** there, and of those, which are general
operations rather than this paper's own method.

Record each in `OPERATIONS.md` as: what was written by hand, how many lines, whether another
paper would want the same thing, and whether it belongs in `transforms/` or stays in a member.
The bar for promotion is a second real user, not a plausible one — that is the same rule
`kwam-enhanced-index/AGENTS.md` applies to its own experiments.

### 3. Where is the framework slow?

The previous testbed found two hot paths by accident, after a run failed to finish: an O(N²)
identity hash and an affordability loop that walked one lot at a time. Both were fixed, and
neither was found by profiling — they were found by a run that hung.

Here the profiling is deliberate. This paper's shape is different from a daily long-short book:
more instruments, a rolling estimation window that recomputes on every step, and a residual panel
much wider than a position book. Profile before assuming, record in `PROFILING.md`, and keep the
measurement next to the declaration it was taken on — a hot-path number inherits the venue and the
data it was measured against, which is exactly how `qlibx` record 041 cleared a loop that was in
fact 55 million iterations on a different declaration.

---

## What this is not

- **Not a check that the paper is right.** `../guijarro-ordonez-2025-replication/` owns that, and
  its own README is explicit that the Korean sample is not an exact replication of the US results.
- **Not a rewrite of that project.** It keeps running. This one reproduces its *outputs* through
  the framework so the two can be compared.
- **Not a place to fix the framework quietly.** A framework defect gets an issue in `qlibx/docs/`
  with a reproduction, and the fix goes there with a test.

---

## Environment

```
vqapr    0.1.0a11, editable from ../../qlibx     (pyproject: vqapr = { path = "../qlibx" })
python   3.12
```

vqapr is an editable path dependency, so a `qlibx` edit is visible on the next run with no publish
step.

### GPU — read before running `uv sync`

This repository's `.venv` carries a **vendor ROCm PyTorch** (`2.9.1+rocm7.2.1`, AMD Radeon 8060S)
that is *not* in `uv.lock`. A plain `uv sync` resolves `torch` from PyPI and silently replaces it
with a CPU build — that happened while installing vqapr here and had to be restored:

```powershell
uv pip install --python .venv\Scripts\python.exe -r guijarro-ordonez-2025-replication\config\rocm-windows-7.2.1-requirements.txt
uv run --no-sync python guijarro-ordonez-2025-replication/scripts/verify_rocm_environment.py --skip-smoke
```

Use `uv run --no-sync` for anything that touches torch. Nothing in this testbed needs a GPU — the
framework side is CPU work — but the neighbouring replication does, and its 496 checkpoints are
not reproducible cheaply.

---

## Data

Shared with the replication next door, under `data/kaist_pilot/canonical/`:

```
common/korean_equity/adjusted_prices.parquet   2015-01-02 ~ 2026-07-20, 4,962 names
common/korean_equity/fng_statement_facts/      FY2016 ~ FY2026
common/korean_equity/sector_classification.parquet
guijarro_2025/                                 paper-specific inputs
```

`adjusted_prices.return` carries **no cash dividend**, and the replication's `docs/` records which
accounting fields are point-in-time and which are not. Read
`../guijarro-ordonez-2025-replication/docs/data-requirements.md` before registering anything: a
registration that gets `available_at` wrong is a look-ahead, and the framework cannot detect it
for you.

---

## Layout

```
FRICTION.md     every point of friction, written before it was resolved   <- purpose 1
OPERATIONS.md   factor operations written by hand, and the case for each  <- purpose 2
PROFILING.md    measured hot paths, with the declaration measured on      <- purpose 3
FINDINGS.md     what the comparison exposed, on either side
HANDOFF.md      state, so the next session does not rediscover it
workspace/      registered + derived data. gitignored, reproducible
outputs/        measurement. gitignored
```

The first three are the deliverable. `FINDINGS.md` and `HANDOFF.md` follow the convention the
`kwam-enhanced-index` testbed settled on and are worth keeping in the same shape.
