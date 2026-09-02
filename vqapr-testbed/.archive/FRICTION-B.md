# FRICTION-B — registering `adjusted_prices.parquet`

Reader: fresh, first contact with `vqapr`. Log written before each problem was resolved, per
MISSION-B.md.

---

### F-B001 — the framework refuses a naive timestamp but will not tell you what instant to put there

**Doing:** filling in `available_at: date` in the dataset declaration template and registering it
straight against the raw parquet.

**Expected:** either it would register (the column is called `date`, looked plausible), or it
would fail with something I could fix by picking a different column.

**Got:**
```json
{"error": "VqaprError: DATA:dataset.register.schema — 1 failure(s)\n  [dataset.register.schema.available_at_not_tz] available_at column 'date' must be a timezone-aware timestamp",
 "failures": [{"code": "dataset.register.schema.available_at_not_tz", "example_total": 0, "examples": [],
 "observed": "TIMESTAMP_NAIVE", "requirement": "available_at column 'date' must be a timezone-aware timestamp"}]}
```

**Cost:** ~20 minutes. The refusal is correct and unambiguous about *what* is wrong (naive
timestamp), but says nothing about *what value is right*. The dataset's `date` column is a bare
calendar date with no time-of-day at all — it doesn't even carry the session close time, let
alone a timezone. Localizing `Asia/Seoul` onto midnight would be wrong (that's not when the price
was known) and localizing onto UTC would be worse. I had to fall back on outside domain knowledge
(KRX's regular session close moved from 15:00 to 15:30 KST on 2016-08-01) to construct a
defensible instant, then rewrite the parquet with a synthesized tz-aware timestamp before the
declaration would register. Nothing in the CLI, the `vqapr new dataset` template comments, or the
installed SKILL.md states this — the skill *asks the right questions* ("what instant within that
date is defensible?") but has no mechanism to help answer them, and the error's `examples` array
was empty (`example_total: 0`), so there was no bounded example of a passing value to imitate
either.

**Fix:** either (a) the `dataset.register.schema.available_at_not_tz` failure could suggest the
generic fix — "localize with `Series.dt.tz_localize(<venue-tz>)`, at an instant that reflects when
the row's observation was public, e.g. session close" — or (b) `vqapr new dataset` could mention
that this is commonly the single largest cost in a first registration, before the user reaches the
failure at all.

**Severity:** slowed

---

### F-B002 — a failure's `examples` field is empty even though the skill says failures always carry bounded examples

**Doing:** reading the `dataset.register.schema.available_at_not_tz` failure to see a concrete
passing/failing value pair, because the installed skill (`SKILL.md`, "Reading vqapr's output")
states: *"`failures` — an array of structured diagnostics, each with `code`, `requirement`,
`observed`, `examples`."*

**Expected:** an `examples` list with at least one sample value from the offending column, since
the skill presents this as a standing guarantee of the output shape, not a maybe.

**Got:** `"example_total": 0, "examples": []`.

**Cost:** a few minutes of second-guessing whether I was looking at a truncated response or a
genuinely empty array (it's genuinely empty — `example_total: 0` confirms it, not just a display
cap). Not blocking, since `observed: "TIMESTAMP_NAIVE"` and the prose `requirement` were enough to
act on, but it undercuts the documentation's claim and made me distrust the *next* failure's
examples field too until I'd seen one actually populated.

**Fix:** either populate `examples` for every failure code (even a single formatted value from the
offending column), or have the skill/CLI help text say "examples may be empty for structural
checks that don't have a natural per-row example" so the empty array reads as designed rather than
broken.

**Severity:** surprised

---

## Summary of this log

- 2 entries, 0 `blocked`, 1 `slowed`, 1 `surprised`.
- No entry reached `blocked`; stop condition 2 (second `blocked` entry) never fired.
- No command failed three times for three different reasons; stop condition 3 never fired.
- Registration succeeded on the **second** `register` attempt (one failure, one success).
