# Friction log

Every point where the framework was harder to use than it needed to be, **written down before it
was resolved**. A question that got answered is worth much less than the record that it had to be
asked at all.

## How to write an entry

```markdown
### F-00N — one line, in the reader's words not the framework's

**Doing:** what was being attempted
**Expected:** what the reader thought would happen, and why
**Got:** what actually happened, verbatim if it was an error
**Cost:** how long, and how it was resolved — docs, source, trial and error, or asking
**Fix:** what would have prevented it. A message, a docstring, a default, a shipped example.
**Severity:** blocked / slowed / surprised
```

`blocked` means work stopped. `slowed` means it cost real time but there was a path. `surprised`
means it worked but not for the reason expected — those are the most valuable and the easiest to
forget to write down, because nothing went wrong.

If a command succeeds, exits 0, and gives a **confidently wrong answer**, record it as `blocked`.

Do not merge two entries because they turned out to share a cause. Two people hit them separately.

---

### F-001 — the source parquet's only timestamp column is naive, and the template says naive is refused

**Doing:** inspecting `adjusted_prices.parquet` to fill in `available_at` for the dataset
declaration template (`vqapr new dataset --out`).
**Expected:** either a ready-made tz-aware timestamp column to point `available_at` at, or at
least a documented convention (KRX close instant, KST) I could apply mechanically.
**Got:** the only date-like column is `date`, `datetime64[us]`, tz-naive (`df['date'].dt.tz is
None`). The template comment says "the column must already be a TIMEZONE-AWARE timestamp in the
parquet... Localize it while preparing the data; registration does not convert it for you." No
column in the file satisfies that. There is also no doc — not the testbed README, not
data-requirements.md, not the skill — that states what instant a Korean daily close should be
localized to (KRX closes 15:30 KST) or in what timezone module strings should be applied
(`Asia/Seoul` is the obvious choice, but "obvious" and "stated" are different things and the skill
explicitly warns not to infer availability from a column name).
**Cost:** ~10 min: reading the parquet metadata (itself hostile, see F-002), diffing against the
template's requirement list, then deciding independently to localize `date` to `Asia/Seoul
15:30:00` as the session-close instant, since that is the only defensible reading of "available
at the close" for a daily bar and matches KRX's actual close time. This is a data-prep decision
the framework and its docs leave entirely to the operator, with only the general principle
("ask, don't infer") and no Korea-specific default.
**Fix:** either (a) `vqapr new dataset` could detect an `available_at` candidate column that is
naive and print a hint referencing the market/timezone question instead of silently deferring
prep, or (b) the testbed README/data-requirements doc could state the KRX close convention
(15:30 KST) once, since every registration in this testbed will need the same answer.
**Severity:** slowed

---

### F-002 — `vqapr new datamodel` writes a component file with no `.py` extension, then `register` refuses it as "not a loadable Python module"

**Doing:** `vqapr new datamodel pca_residual_returns --dataset korean_equity_adjusted_prices
--field close --lookback 252 --out workspace/components/pca_residual_returns`, then `vqapr
register workspace/components/pca_residual_returns.yaml` on the emitted YAML exactly as written.
**Expected:** the scaffold command and its own emitted `.yaml` (`path:
pca_residual_returns`) to agree with each other, and registration to succeed on an unmodified
scaffold — the skill and CLI help both frame `new` + `register` as a working pair ("writes a
component .py that runs as written").
**Got:** `--out workspace/components/pca_residual_returns` (no extension, as literally passed) was
honored verbatim: the tool wrote a real `.py`-content file at that exact extensionless path, and
the generated YAML's `path:` field pointed at the same extensionless name. `register` then
refused: `{"code": "component.load.module_invalid", "observed": "...\\pca_residual_returns",
"requirement": "component path must identify a loadable Python module"}` — true, but it does not
say *why* (missing `.py`) or suggest the fix. I had to run `file` on the emitted artifact to
confirm it actually was Python source before renaming it.
**Cost:** ~5 min — running `file`, copying to `pca_residual_returns.py`, editing the YAML's
`path:` field by hand, re-registering.
**Fix:** `vqapr new datamodel/strategy` should append `.py` to `--out` itself when the caller
omits it (mirroring what `dataset`/`run-spec` do with `.yaml`), or refuse at scaffold time with
"`--out` for datamodel/strategy must end in `.py`" instead of silently writing a working script to
an extensionless path that its own next command will reject. Failing that, the
`component.load.module_invalid` message should name the missing extension as the fix, not just
restate the requirement.
**Severity:** slowed

---

### F-004 — `execution_inputs` required keys arrive one at a time, seven round trips deep and counting

**Doing:** registering an `execution_inputs` declaration (`vqapr new` has no scaffold for this
kind — `new` only knows `datamodel`, `strategy`, `dataset`, `run-spec`; there is no `vqapr new
execution-input`, so I hand-wrote a minimal YAML and let `register` tell me what it needed).
**Expected:** either a scaffold command (matching the pattern `new dataset --out` uses, which
comments every required key up front), or a single failure response that lists every missing key
at once — the skill says `failures` is an array, implying multiple simultaneous diagnostics are
supported by the format.
**Got:** seven consecutive `register` calls, each refusing with exactly **one** new
`declaration.read.key_missing` failure, discovered strictly in this order:
1. `execution_inputs.krx_default must declare table` (starting from `{kind: placeholder}`)
2. `...must declare fill` (after adding `table: {}`)
3. `...table must declare price_fields` (after adding `fill: {}`)
4. `...table must declare path` (after adding `price_fields`)
5. `...table must declare source_id` (after adding `path`)
6. `...table must declare trade_at_field` (after adding `source_id`)
7. (open at time of writing — still not registered)

Each response's `observed` field is accurate ("declares: X, Y") and each `requirement` is
accurate ("must declare Z"), so nothing is *wrong* — but the validator clearly already knows the
full required-key set for `table` (it is enforcing membership against it), and chooses to report
only the first missing one instead of the complete diff. This is the single worst point of
friction in this session: it converts a static schema (`vqapr new dataset --out` proves the
framework *can* emit a fully-commented template) into a binary-search-by-hand exercise, with each
round trip costing a full CLI invocation.
**Cost:** ~15 min so far across 7 register attempts, still not resolved. Would have been one
round trip with either a scaffold command or a complete-diff error.
**Fix:** (a) ship `vqapr new execution-input --out <path>` alongside the existing `dataset` and
`run-spec` templates — the CLI help for `new` already enumerates `{datamodel,strategy,dataset,
run-spec}` and conspicuously has no `execution-input`, despite `execution_input` being a required
field in every run spec; (b) independent of (a), `declaration.read` should report every missing
required key for a section in one `failures` array entry-per-key, not one key per invocation —
the skill's own description of `failures` as an array of independent diagnostics implies this is
supported and simply not used here.
**Severity:** blocked

---

### F-005 — `execution_inputs.<id>.table` alone needed 6 keys across 6 round trips (path, price_fields, source_id, trade_at_field, instrument_field, is_tradable_field); then `fill.selector` crashed six times in a row with a raw, unhandled `KeyError` and no valid-value hint, and this is where the session stopped

**Doing:** continuing F-004's key-at-a-time discovery to completion for the `table` block, then
starting on `fill`.
**Expected:** after `table` finally accepted 6 keys (`price_fields`, `path`, `source_id`,
`trade_at_field`, `instrument_field`, `is_tradable_field` — discovered one per `register` call,
same pattern as F-004), the `fill` block would either scaffold similarly or fail with the same
structured `declaration.read.key_missing` shape.
**Got:** `fill: {selector: close}` did not produce a structured failure. It crashed:
```
{"error": "KeyError: 'CLOSE'", "failures": [], "family": null, "stage": "unhandled"}
```
and the on-disk diagnostic file (`.vqapr/diagnostics/unhandled.txt`, which `register`'s own output
points at) is a raw Python traceback naming `qlibx\src\vqapr\cli\register.py` line numbers and
showing `FillSelector[str(_required(fill, "selector", ...)).upper()]` — i.e. `selector` is looked
up against a `FillSelector` enum by uppercased name, `"close".upper()` -> `"CLOSE"` is not a valid
member, and the enum lookup's `KeyError` is never caught and turned into the same
`declaration.read.key_missing`/`key_invalid`-style structured failure every other bad key in this
section produced. This is the exact case the skill calls a `blocked`-severity confidently-wrong
moment, except worse: it does not even give a confidently wrong *answer*, it gives a raw stack
trace pointing straight at the file the instructions say never to read. I did not open
`qlibx/` myself — the traceback was dumped into a diagnostics file `register` told me to read —
but I did not read past the one frame that named the enum class, and did not go looking for the
valid `FillSelector` member list in source; I guessed common execution-fill vocabulary instead
(`MARKET`, `CLOSE`, `VWAP`, `LAST`) until one worked. Recording the urge as instructed: yes, I
wanted to open the enum definition to get the exhaustive member list in one read instead of
guessing blind against a crash-on-miss validator. I did not — instead I tried
`close`, `market`, `close_price`, `last`, `vwap`, `next_open` as `fill.selector` values, in that
order, choosing each from ordinary execution-fill vocabulary. **All six crashed with the same
unhandled `KeyError`.** No structured failure ever appeared; every single wrong guess produces the
same bare traceback naming a qlibx source line, never a list of valid members. This is where
registration stopped for this run — six guesses without a hit is not "trial and error", it is a
validator with a closed, undocumented vocabulary and a crash instead of a refusal.
**Cost:** ~30 min across the full `table`+`fill` sequence (10 structured round trips plus 6 crash
round trips = 16 total `register` invocations for one declaration), plus the detour of reading a
stack trace to figure out crash vs. structured refusal, ending without a registered
`execution_input`.
**Fix:** (1) every `_required(...).upper()` / enum-lookup pattern in declaration parsing should
catch the invalid-member case and re-raise as the same structured `declaration.read.*` failure
shape everything else uses, listing valid members in `requirement` — an enum's member list is
exactly the kind of fixed vocabulary the `requirement`/`observed` contract exists for; (2) same as
F-004, a scaffold for `execution_inputs` would have prevented all of this by showing the valid
`fill.selector` values in a comment, the way `vqapr new dataset --out` already does for datasets.
**Severity:** blocked

---

### F-003 — reading the parquet directly (not via pandas) prints binary garbage, and the column names are Korean but the terminal encoding is not UTF-8 by default

**Doing:** a first look at `adjusted_prices.parquet` via the generic file reader, then via a plain
`uv run --no-sync python -c "pandas.read_parquet(...).dtypes"` in the default shell.
**Expected:** readable column names and dtypes.
**Got:** the generic reader dumped raw parquet thrift/binary bytes (footer metadata). The pandas
print of `df.columns`/`df.head()` rendered every Korean column name (기준가, 시가, 종가, 유통주식수,
etc.) as `�` mojibake — this is a Windows console codepage problem, not a vqapr problem, but it
cost real time because it was not obvious at first whether the *data* was corrupt or the
*terminal* was. Only after forcing `sys.stdout.reconfigure(encoding='utf-8')` did the real column
names appear: `기준가, 시가, 고가, 저가, 종가, 전일종가, 수정계수, adjustment_multiplier, adj_base,
adj_open, adj_high, adj_low, adj_close, return, trade_volume, tx_amount, 유통주식수, market_cap,
trading_halt_code, admin_issue_code, is_trading_halt, is_admin_issue`.
**Cost:** ~5 min re-running with UTF-8 forced to confirm the data was fine and only the terminal
rendering was broken.
**Fix:** not a vqapr defect — but the testbed README could warn that this dataset has native
Korean column headers and that a Windows shell needs UTF-8 output forced before inspecting it,
since every future session on Windows will hit this identically.
**Severity:** slowed

---

## Session summary (fresh-agent attempt, 2026-08-24)

**Stop condition triggered:** #3 — six consecutive `fill.selector` guesses on `execution_input.yaml`
(`close`, `market`, `close_price`, `last`, `vwap`, `next_open`) each crashed identically with an
unhandled `KeyError` and produced zero new information toward the correct value; that run of
failed attempts with no progress is what ended the session. (Stop condition #2, third `blocked`
entry, was also independently satisfied by F-004/F-005 by this point.)

**Stages completed:**
1. Registration of the dataset (`korean_equity_adjusted_prices`) — succeeded, one round trip,
   after independently deciding the `available_at` convention (F-001).
2. Registration of a scaffolded `DataModel` component (`pca_residual_returns`) — succeeded after
   one fix (F-002, missing `.py` extension).
3. Registration of a scaffolded `StrategyModel` component (`k200_ou_stat_arb`) — succeeded
   first try once `.py` was passed explicitly to `--out`.
4. Registration of an `execution_input` — **not completed**. Blocked after 16 `register`
   invocations for a single hand-written declaration (10 structured `key_missing` diagnostics,
   6 identical unhandled crashes on `fill.selector`), stopped per condition #3.
5. Run-spec / `vqapr run` — not reached; the run spec's `execution_input` field cannot be filled
   without a registered execution input.

Stop condition #1 ("registration AND at least one more stage") is satisfied: dataset registration
plus two component registrations (datamodel and strategy) both completed. The workflow did not
reach derivation execution, a built/registered strategy config, or a run.

**Friction entries:** 5 total — F-001 (slowed), F-002 (slowed), F-003 (slowed), F-004 (blocked),
F-005 (blocked). 2 blocked / 3 slowed.

**Single worst point of friction:** F-005 — `execution_inputs.fill.selector` is validated against
a Python enum by uppercasing the input and doing a raw dict lookup with no exception handling, so
every wrong guess is an unhandled `KeyError` with a qlibx stack trace instead of a structured
refusal naming the valid choices, turning what should be a one-shot lookup into unbounded blind
guessing.

**Was SKILL.md helpful, unhelpful, or irrelevant?** Net helpful but incomplete. It correctly
front-loaded the `available_at` semantics question (prevented a silent look-ahead) and correctly
described the `{ok, stage, failures}` JSON contract, which made every *structured* failure fast to
act on. It was silent exactly where it mattered most: it lists `execution_inputs` as something
Rung 1 must register, but gives no guidance that `vqapr new` has no scaffold for it, no hint of the
required key set, and no warning that this declaration kind's error path is not held to the same
structured-failure contract the skill itself documents (the enum crash). The skill's own promise —
"the CLI validates and refuses with structured diagnostics" — is not true for `fill.selector`, and
nothing signals that gap before it is hit.

**Did I want to read qlibx source? What for?** Yes, once, explicitly (F-005): to get the exhaustive
member list of the `FillSelector` enum after the first unhandled `KeyError`, instead of guessing
execution-fill vocabulary six times with no signal. I did not open it — I read the one traceback
frame that `register` itself wrote to `.vqapr/diagnostics/unhandled.txt` (a file the CLI's own
output pointed at, not a self-directed dive into `qlibx/`), stopped at naming the class, and
guessed from there. The urge was strong and the six-guess failure sequence is the direct cost of
not satisfying it.

**What should the next person do first?** Do not hand-write `execution_inputs` YAML from a
register-and-iterate loop — it is the single most expensive path in this session (16 round trips,
still unresolved, from a two-key placeholder to a `table` block of 6 required keys, then a
crash-only `fill.selector`). If a `vqapr new execution-input --out` scaffold does not exist,
escalate for a valid `FillSelector` member list before attempting registration at all, rather than
guessing blind against a validator that crashes instead of refusing. Everything else in this log
(`available_at` localization to KRX close, the `.py` extension requirement on `--out`, the Windows
UTF-8 terminal issue) is solved and reusable as-is from this file.

