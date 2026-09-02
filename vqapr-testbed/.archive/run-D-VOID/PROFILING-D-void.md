# Profiling — where the framework is slow

Purpose 3 in `README.md`. Deliberate this time, not discovered by a run that hung.

## Why this is not optional here

The previous testbed found two hot paths, both by accident, both after a run stopped finishing:

- `FrozenRun.identity` re-hashed every occurrence of all three agendas on every callback — O(N) per
  callback, O(N²) per run. Fixed in `qlibx` `d1a9a92`: 71.30s → 6.80s on 2,940 occurrences.
- `_apply_venue_rules` walked the affordability clip down one `quantity_step` at a time — 55
  iterations on a whole-share venue, **55,226,256** on a fractional one. Fixed in `qlibx` record
  043, which also closed `docs/issues/005`.

Neither was found by profiling. The second is the sharper lesson: `qlibx` record 041 had already
profiled that exact loop and cleared it, correctly, **on a whole-share venue** where the walk is 55
iterations. A hot-path measurement inherits the declarations of the venue it was taken on.

So every entry here records the declaration, not only the number.

## This paper's shape is different

The enhanced-index book was ~200 names rebalanced daily against a position book. This is:

- a **wider panel** — 4,962 names in `adjusted_prices.parquet`, ~275,711 residuals in the existing
  PCA5 output;
- a **rolling estimation** that recomputes on every step — 252-day covariance, 60-day loadings;
- a **residual panel much wider than the position book** it eventually trades.

Each of those stresses a different part of the framework than a daily long-short book does, so the
previous testbed's timings do not transfer.

## How to write an entry

```markdown
### P-00N — what was slow, in one line

**Measured on:** venue declaration, instrument count, session count, lookback shape
**Method:** cProfile / wall clock / bisect — and why that one
**Before:** the number
**Where:** the frame, with file:line
**Cause:** what the frame was actually doing
**After:** the number, and what changed
**Generalises?:** which declarations would and would not reproduce it
```

`Measured on` is first because record 041 is what happens when it is missing.

## Method notes

- **Measure before assuming.** Record 041 rejected vectorising the fill loop after measuring it at
  0.034s for 3,000 instruments — under 2% of one factor build. The instinct was wrong and the
  measurement said so.
- **Bisect a hang rather than profile it.** A profiler on a run that never returns produces
  nothing. Walking the session count up until it stops finishing names the occurrence, and a
  `faulthandler` stack dump on a loop names the frame.
- **Watch for output buffering.** `nohup ... &` plus polling the log is the pattern that works
  here; a blocking timeout kills a run mid-publish and leaves a half-written workspace.

## Baselines

Fill in as they are measured. A missing baseline is why a regression goes unnoticed.

| step | instruments | sessions | wall | note |
|---|---|---|---|---|
| dataset prep (5-name dev slice, `scripts/prepare_prices.py`) | 5 | ~330 | ~1s | filtered to 5 tickers / ~16 months before the Decimal cast |
| `vqapr register` (dataset) | 5 | ~330 | <1s | |
| `vqapr run` (full horizon, 2016-01-04 -> 2016-11-15) | 5 | 217 strategy occurrences | ~3-5s wall | 642 total occurrences (strategy+valuation), account_version 831 |

## Entries

### P-001 — Decimal-casting the full source parquet, not the filtered slice, is the actual hot path a naive prep script would hit

**Measured on:** `data/kaist_pilot/canonical/common/korean_equity/adjusted_prices.parquet`, single
column (`adj_close`), Python `Decimal(str(v))` map, wall-clock timed directly (not cProfile — this
is data-prep code outside the framework, not a `qlibx` frame).
**Method:** timed a 200,000-row slice of `adj_close` with `Series.map(lambda v: Decimal(str(v)))`
and linearly extrapolated to the full file's 8,651,872 rows.
**Before:** 0.121s / 200,000 rows -> 0.605 microseconds/row -> **~5.2s extrapolated for one column
over the full file**, and this dataset needs three Decimal columns (`adj_close`, `return`,
`trade_volume`), so an unfiltered prep script pays roughly **~15s** just for the dtype cast, before
any registration or run cost.
**Where:** `vqapr-testbed/scripts/prepare_prices.py` (data prep, not framework code) — the
`for col in (...): df[col] = df[col].map(...)` loop.
**Cause:** `vqapr` requires Strategy-callback price fields to be `Decimal` (see FRICTION F-003:
float64 columns crash mid-run with a `TypeError`), and pandas has no native Decimal dtype, so the
only path is a Python-level `.map()` over every cell — there is no vectorised cast available.
**After:** filtered the source to 5 tickers over ~16 months (1,175 rows) *before* casting, which
brought this specific step under 1s. The ~15s full-file cost was never actually paid in this
session because the dev slice made it moot — but it is real, it is on the *first* thing any new
user does after hitting F-003, and it would not stay moot for the residual panel described in the
README ("much wider than a position book").
**Generalises?:** yes, directly — any dataset registered against this framework with float64
source columns pays this cost once, at prep time, scaling linearly with row count and Decimal
column count. A 46-characteristic panel across 4,962 names (the paper's actual universe) would be
multiple orders of magnitude larger than this dev slice; extrapolating linearly, the full
`adjusted_prices.parquet` alone (8.65M rows x 3 Decimal columns) is in the tens-of-seconds range,
and a wider characteristic panel would likely be worse. This is a **data-prep cost the framework's
Decimal contract imposes**, not a `qlibx` internal frame, so it belongs here as a warning for the
next person rather than as a framework defect: budget prep time proportional to row count x
Decimal-typed column count, and filter to the working universe before casting, not after.
