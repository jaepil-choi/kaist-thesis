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
| _(register)_ | | | | |
| _(derive)_ | | | | |
| _(run)_ | | | | |

## Entries

_(nothing yet)_
