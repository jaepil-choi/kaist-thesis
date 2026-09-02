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
**Cost:** how long, and how it was resolved — docs, help output, trial and error, or asking
**Fix:** what would have prevented it. A message, a docstring, a default, a shipped example.
**Severity:** blocked / slowed / surprised
```

`blocked` means work stopped. `slowed` means it cost real time but there was a path. `surprised`
means it worked but not for the reason expected — those are the most valuable and the easiest to
forget to write down, because nothing went wrong.

If a command succeeds, exits 0, and gives a **confidently wrong answer**, record it as `blocked`
and say so explicitly. That case matters more than finishing the task.

Do not merge two entries because they turned out to share a cause. Two people hit them separately.

## What is in bounds

Everything the installed package hands you is fair game, including things that name framework
internals:

- `vqapr --help` and every verb's `--help`
- the installed skill
- **the traceback dumps under `.vqapr/diagnostics/`**, which failure payloads name in `detail`.
  The CLI writes those into your project and points at them; reading one is using the tool as
  built, not going around it. If a dump is the only way to learn something, that fact is itself
  worth an entry — but read it.
- any document inside this repository

Out of bounds is the framework's **own repository** (`qlibx/`) and its source files wherever they
are installed — reading implementation to work out what a function means. An installed user does
not have that, so neither do you.

---

### F-001 — the `date` column's `available_at` instant is a decision the framework correctly refuses to make for you, but the dataset template doesn't hint at KRX session hours

**Doing:** writing the dataset declaration for `adjusted_prices.parquet`, whose `date` column is a
naive midnight timestamp for the trading session.
**Expected:** the template or skill would name a convention (e.g. "if this is an exchange-traded
price, look up the venue's close time").
**Got:** the skill correctly refuses to guess ("do not infer a convention from a column name") and
asks three questions, but supplies no path to the answer — KRX regular session close (15:30 KST)
is domain knowledge that has to come from outside the framework and outside this repo's own docs.
Neither `data-requirements.md` nor the dataset template states it.
**Cost:** ~5 minutes of external knowledge recall, not tool time. Low cost here because KRX hours
are common knowledge; a less familiar market would have blocked entirely.
**Fix:** nothing the framework can fix — this is domain knowledge, correctly left to the user. But
`data-requirements.md`, which the README says to read "before registering anything," could name
the session close explicitly since it already discusses this exact column.
**Severity:** slowed
**Resolved:** the replication's `docs/data-requirements.md` now names the session-close contract,
but not as the blanket 15:30 originally assumed here: this dataset begins in 2015, and KRX changed
the securities regular-session close from 15:00 to 15:30 effective 2016-08-01. It documents
15:00 before that date and 15:30 from that date, cites KRX, and requires a known-instant
round-trip. Applying 15:30 to all 2015 rows would itself have been confidently wrong.

### F-002 — a required key for `agendas` is discovered one round trip at a time

**Doing:** registering an `agendas:` section by hand (the skill's Rung 1 walkthrough never shows
an agenda declaration, and `vqapr new` has no `agendas` scaffold — only `datamodel`, `strategy`,
`dataset`, `execution-input`, `run-spec`).
**Expected:** either a template (`vqapr new` covering agendas) or an error that names all missing
keys in one shot, since `declaration.read` already knows the full required schema.
**Got:** four sequential refusals, each naming exactly one missing/wrong key:
1. `agendas.daily must declare role` (no template existed to know `role` was needed)
2. `agendas.daily.role must be one of: strategy_callback, valuation, monitoring` (guessed `strategy`, wrong)
3. an **unhandled** `ValueError: agendas.daily must declare exactly one of from_dataset or sessions` —
   no `failures` array, `family: null`, `correlation_id: null`, `detail` pointed at a generic
   `unhandled.txt` diagnostic (not a per-run digest name). Reading the dump showed a normal Python
   traceback ending in a `raise ValueError(...)` inside `register.py::_sessions` — useful, but it's
   the same string already in `error`, so the dump added a file:line and nothing else.
4. `agendas.daily must declare timezone`
**Cost:** 4 register→edit→retry round trips, roughly 10 minutes, to assemble one working `agendas:`
block. Every other declaration kind (dataset, execution-input, run-spec) gets a template with every
required key commented; agendas do not.
**Fix:** either add `agendas` to `vqapr new`'s scaffold list, or have `declaration.read` validate
an agenda body against its full required-key set in one pass and report every missing key at once
(the way `example_total`/`examples` already batch row-level violations). Also: item 3 should be a
structured `DATA` failure like the other three, not an unhandled `ValueError`.
**Severity:** slowed
**Resolved:** `docs/implementations/052` did both. `vqapr new agendas` emits agendas +
strategy_configs + valuation_configs together. `_require_agenda_keys` batches every missing key
including the from_dataset/sessions XOR into one refusal. The three bare ValueError/TypeError
paths are now typed DATA failures. Also fixed: `workspace()` was evaluated before `_agenda()` ran,
so a malformed agenda in a fresh directory blamed `workspace.open.missing` instead of the file.

### F-003 — the run spec template never mentions `strategy_configs` / `valuation_configs`, so a filled-in template fails with a stage the reader has never seen

**Doing:** running `vqapr run spec.yaml` after every component named in the template
(`strategy.component`, `strategy.agenda_id`, `valuation.agenda_id`, `exchange`, `execution_input`)
was registered.
**Expected:** preflight would either succeed or point at the run-spec's own keys.
**Got:** `workspace.strategy_config.register.missing — strategy config for agenda 'daily-rebalance'
must be registered`. This is a *third* declaration kind, `strategy_configs:`/`valuation_configs:`,
that binds a component to an agenda and a role — never mentioned in `vqapr new run-spec`'s
template, never mentioned in the skill's Rung 1/Rung 2 walkthrough, and not discoverable from
`vqapr new`'s four scaffold kinds. The run spec *looks* self-contained (it names `component` and
`agenda_id` directly) but silently depends on a separate binding declaration that has to be known
to exist.
**Cost:** ~5 minutes: one failed run, one `python -c "help(vqapr.public.StrategyConfig)"` probe to
find the constructor shape, one hand-written YAML, one successful register.
**Fix:** the run-spec template should either declare `strategy_configs`/`valuation_configs`
inline (like dataset declarations do with their source), or its header comment should say
"components named above must also be bound via a registered strategy_config/valuation_config" with
an example key shape.
**Severity:** slowed
**Resolved:** same 052. The run-spec header now says "naming an agenda_id here is not a binding"
and points at `vqapr new agendas`. SKILL.md Rung 1 lists the three `new` templates explicitly.

### F-004 — a scaffolded `StrategyModel`/`DataModel` assumes `Decimal` rows; a real parquet dataset with float64 columns fails deep inside the simulator with a bare Python `TypeError`, not a structured refusal

**Doing:** running the strategy scaffold emitted by `vqapr new strategy ... --dataset
krx_adjusted_prices --field close`, unmodified except for the required "one line to change,"
against a real dataset whose `close` field is parquet float64.
**Expected:** either the scaffold works against any registered dataset, or registration/preflight
refuses the mismatch before simulation starts (`available_at` type-checking already does this kind
of thing for timestamps).
**Got:** `SimulationFailure: simulation.callback.intent: unsupported operand type(s) for -: 'float'
and 'decimal.Decimal'` — no structured guidance beyond the raw exception message; `failures[0].code`
is literally `simulation.callback.intent.TypeError`, i.e. the Python exception class name promoted
to a field, not a framework-level diagnosis. The `detail` dump was the only way to learn *where*:
it named `krx_momentum_strategy.py:74`, the exact scaffold line, which the JSON envelope did not.
**Cost:** ~5 minutes — one failed run, one diagnostic-dump read, one one-line fix
(`Decimal(str(value))` instead of `value`) applied to both the datamodel and strategy scaffolds,
since both have the identical bug.
**Fix:** the scaffold's docstring says "registering this file as written succeeds and running it
produces a result" — that's only true if the dataset's field happens to already be Decimal.
Either the scaffold should cast defensively, or the DataRequirement/window layer should coerce
numeric fields to Decimal before handing rows to a callback (it already owns the schema).
**Severity:** blocked (the scaffold's own docstring promise was false for a real dataset; the file
ran as written, per the docstring, and failed)
**Resolved:** 0.1.0a16 cast both templates with `Decimal(str(value))`, and
`docs/implementations/051` added the regression test that release shipped without, plus the third
copy of the bug it missed in `agent/sample/reversal_5d.py`. Root cause of the 691-test miss: every
price fixture in the framework wrote bare DuckDB literals, and `typeof(100.0)` is `DECIMAL(4,1)`,
not `DOUBLE` — so no test had ever handed a model a `float`.

### F-005 — a hand-rolled `pyarrow` timezone "localization" that is actually a UTC relabel produced a confidently wrong `available_at`, and nothing in registration caught it

**Doing:** preparing `adjusted_prices_prepared.parquet`'s `available_at` column by adding 15:30 to
the naive `date` column, then calling `.cast(pa.timestamp("us", tz="Asia/Seoul"))` to attach a
timezone.
**Expected:** the cast would localize the naive wall-clock value to Asia/Seoul, i.e.
`2015-01-02 15:30` naive becomes `2015-01-02 15:30+09:00`.
**Got:** `.cast(..., tz=...)` in pyarrow treats the underlying int64 as already being a UTC epoch
and only *attaches* the tz label for display — it does not shift or reinterpret the wall-clock
value. The venue table's `trade_at` ended up reading `2015-01-03 00:30+09:00` for a `date` of
`2015-01-02`, i.e. the `+09:00` offset was applied a second time on display, silently shifting
every execution instant by 9 hours. `vqapr register` accepted this without complaint — the column
is a well-formed timezone-aware timestamp, exactly as the schema requires, and a timestamp that is
wrong in meaning is still perfectly well-formed, which is precisely the warning the skill gives
about `available_at` ("the framework cannot detect it for you"). Confirmed only by manually
comparing `.cast(...)` against `pc.assume_timezone(...)` on a known instant.
**Cost:** this is not a vqapr bug — it's a pyarrow footgun in my own data-prep script, one that the
vqapr skill correctly warned was outside its power to catch. But it directly produced a downstream
`ValueError: no exact execution target exists within the run horizon` on the run's last occurrence
that looked like a venue/fill-selector problem and cost ~15 minutes of investigation (checking
`next_eligible` vs `same_day`, checking row counts, before comparing the two casts side by side)
before the actual root cause (wrong instant, not wrong selector) was found.
**Fix:** the skill's `available_at` guidance is right in principle but should extend past "say what
timezone the timestamp is in" to "prove it by round-tripping a known instant through your prep
code before registering" — the failure mode here was a confidently-produced, schema-valid, silently
wrong timestamp, which is exactly the case the skill calls the most valuable and easiest to miss.
**Severity:** blocked, until traced to the actual cause (self-inflicted, not a framework defect —
but logged per the rule that a confidently wrong answer outranks everything else, and this was one
step removed from becoming a look-ahead the framework genuinely cannot detect)
**Resolved:** `docs/implementations/054`. The installed skill and emitted dataset template now
require one known-instant local-zone/UTC round-trip before converting a full file, explicitly warn
that a pyarrow cast is not wall-clock localization, and name
`pyarrow.compute.assume_timezone`. Tests pin that both installed surfaces retain the warning.

### F-006 — the `next_eligible` fill selector cannot resolve for a strategy decision made on the run's last occurrence, and the refusal only shows up as a generic `ValueError`

**Doing:** running the full spec with `end: "2015-03-31"` and `fill.selector: next_eligible`.
**Expected:** either the run truncates cleanly at the horizon, or preflight refuses in advance
(it already knows the horizon and the selector at freeze time).
**Got:** `SimulationFailure: simulation.callback.intent: no exact execution target exists within
the run horizon`, raised mid-run on the very last occurrence, after 163 prior occurrences had
already executed and mutated account state. `failures[0].code` is again the bare exception class
name (`simulation.callback.intent.ValueError`), not a diagnosis. Fixed by trimming `end` back six
trading days so every decision has a resolvable next-eligible fill inside the horizon — a
workaround, not a real fix, since any real run has this same edge at its own last day.
**Cost:** ~10 minutes, folded into the F-005 investigation since both produced the identical
surface error and had to be disambiguated together.
**Fix:** preflight already validates drift between spec and registered components; it could also
walk the last N occurrences under the chosen fill selector and refuse in advance with "the last
strategy occurrence's fill would fall outside `end`; either extend `end` by the selector's lookahead
or use `same_day`." Right now the only way to learn this rule exists is to hit it.
**Severity:** slowed
**Resolved:** same 054. Preflight now reads the execution horizon once and proves an exact target
for every frozen strategy occurrence before returning a run-ready declaration. The measured edge
is pinned: a 10:00 callback resolves to 15:30, while a final callback exactly at 15:30 under
`next_eligible` is refused as `preflight.execution.target_outside_horizon`, `mutation:false`, with
the occurrence and actionable choices in the structured failure.

---

## Stop condition

Stop condition **1** fired: a full run completed — registration (dataset, two components, an
exchange, an execution input, two agendas, and strategy/valuation configs), an execution input,
a filled-in run spec, and `vqapr run spec.yaml` returning `{"account_version": 190, "occurrences":
164, "ok": true, "stage": "run.complete"}`. Verified reproducible: the workspace was rebuilt from
scratch (`rm -rf .vqapr` + re-register all seven declarations) and the run produced the identical
`account_version`/`occurrences` pair on the rebuilt workspace, and again on a same-workspace rerun.
Six friction entries were logged (F-001 through F-006), short of the three-`blocked`-entries stop
condition (two of six were marked `blocked`: F-004 and F-005) and short of six identical-command
attempts with no new information.


