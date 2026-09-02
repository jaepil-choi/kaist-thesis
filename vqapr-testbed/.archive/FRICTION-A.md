# Friction log

Every point where the framework was harder to use than it needed to be, **written down before it
was resolved**. A question that got answered is worth much less than the record that it had to be
asked at all.

This file is the deliverable of purpose 1 in `README.md`, and it is spendable: it can only be
written by someone who does not yet know vqapr. Once you know why something is the way it is, you
have stopped being able to write this entry honestly.

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

Do not merge two entries because they turned out to share a cause. Two people hit them separately.

---

## Setup, before any replication work

### F-001 — `vqapr agent install` is documented but does not exist

**Doing:** installing the agent skill, as the task asked, so a fresh agent starts with the
framework's own guidance rather than with a human's summary.
**Expected:** `src/vqapr/agent/skill/README.md` opens with

> `vqapr agent install`이 이 디렉터리의 내용을 target의 skill directory로 복사한다
> (`agent/targets.py`가 정한 normative path).

so a command by that name, and an `agent/targets.py`, both exist.
**Got:** the CLI has four commands and none is `agent`:

```
usage: vqapr [-h] [--project-root PROJECT_ROOT] {new,register,run,list} ...
```

`src/vqapr/agent/` contains `sample/` and `skill/`; `skill/` contains only that README. There is no
`targets.py` and no `SKILL.md` — which the same README lists as the "required entrypoint, PRD
§11.2가 정한 이름".
**Cost:** ~10 minutes, resolved by reading the source tree. Not recoverable from the docs, which
describe the feature in the present tense.
**Fix:** either implement it or mark the README as a specification. A document that describes an
unbuilt command in the present tense costs every reader the same ten minutes, and the cost lands
on exactly the audience the skill is for.
**Severity:** blocked (for the skill install specifically; the rest proceeded)

**Consequence for this testbed:** purpose 1 is being attempted *without* the skill. That is worth
knowing rather than working around — the friction recorded here is what the package alone
produces, which is the harder and more honest baseline. When the skill lands, the same log run
again is a direct measurement of what it is worth.

### F-002 — installing the framework silently replaced a vendor GPU build

**Doing:** `uv sync` after adding `vqapr` to `pyproject.toml`.
**Expected:** vqapr installed, nothing else moved.
**Got:** vqapr installed, and `torch 2.9.1+rocm7.2.1` replaced by `torch 2.13.0+cpu`.
`torch.cuda.is_available()` went `True → False` on a machine whose GPU the neighbouring project
needs.
**Cost:** ~15 minutes to notice, diagnose and restore. The restore path was pinned in
`guijarro-ordonez-2025-replication/docs/home-gpu-handoff.md`, which had already predicted exactly
this: "일반 `uv sync`는 `uv.lock`의 PyPI 해석에 따라 ROCm Torch를 교체할 수 있으므로".
**Fix:** not vqapr's — this is `uv` reconciling a venv to a lock that never described the vendor
wheel. Recorded because it is a real cost of adding the framework to an existing project, and
because the warning existed and was in a document nobody reads before an install.
**Severity:** slowed (and would have been `blocked` had it gone unnoticed until a GPU run)

---

## Registration

### F-003 — `vqapr new` has no `dataset` scaffold, and `register --help` names no schema

**Doing:** looking for a way to get a starting-point declaration YAML for a *dataset*, the way
`vqapr new datamodel <id> --dataset <d>` gets one for a datamodel. `HANDOFF.md`'s suggested first
move is "register `adjusted_prices.parquet` as a dataset" — the CLI's own scaffolding tool seemed
like the obvious place to start.
**Expected:** `vqapr new dataset <id> --path <parquet>` or similar, emitting a commented template
the way `vqapr new run-spec --out spec.yaml` does ("writes a run spec template with every required
key, each one commented").
**Got:** `vqapr new`'s positional choices are only `{datamodel,strategy,run-spec}`. No `dataset`.
`vqapr register --help` says declarations cover "Datasets, sources, execution inputs, components,
agendas and configs" but names no required keys, no schema, and no example — it only describes
*what register does with* a declaration, not *what a declaration must contain*. Neither
`--help` surface tells you the field names, types, or where `available_at` goes inside the
document.
**Cost:** in progress — about to search this repo's own tree (showcases/, workspace/, other
testbed conventions) for an existing dataset declaration to use as a shape reference, since
neither `new` nor `register --help` supplies one and reading `qlibx/` is off-limits.
**Fix:** either give `vqapr new` a `dataset` subcommand producing a commented template (consistent
with how run-spec already works), or have `register --help` print the minimal required key set for
each declaration kind it accepts.
**Severity:** slowed

### F-004 — `--project-root` is a global option but rejected after the subcommand

**Doing:** running `vqapr register workspace/adjusted_prices.yaml --project-root .` from inside
`vqapr-testbed/`, having seen from `vqapr --help` that `--project-root PROJECT_ROOT` is listed
under the top-level `options:` block (not under any one subcommand), which reads as "pass it
anywhere."
**Expected:** either it works after the subcommand (most argparse-based multi-command CLIs
accept a parent option in either position, or at least say so), or the earlier `--help` output
notes that it is positional-sensitive.
**Got:** `{"error": "UsageError: unrecognized arguments: --project-root .", ...}` — the message names
the offending token but not that the fix is "put it before the subcommand," nor that the current
directory is already the default project root, making the flag unnecessary here in the first
place.
**Cost:** ~2 minutes — re-read `vqapr --help`'s synopsis line (`vqapr [-h] [--project-root ...]
COMMAND ...`) and noticed `--project-root` sits before `COMMAND` in the usage string, which is the
only place order is actually specified.
**Fix:** either accept the flag in both positions (argparse subparsers can do this with a small
change), or have the refusal say "global options must precede the subcommand" instead of just
"unrecognized arguments."
**Severity:** slowed

### F-005 — a missing required key produces `stage: "unhandled"` with an empty `failures` array, not a structured diagnostic

**Doing:** `vqapr register workspace/adjusted_prices.yaml` with a first-draft declaration
(`path`, `instrument_column`, `timestamp_column`, `available_at` — no `fields` key, because
nothing in `register --help` or `vqapr new`'s output named `fields` as required for a dataset).
**Expected:** per the installed SKILL.md ("When `ok` is false, read the `failures` array first.
Each failure tells you what was required, what was observed, and gives bounded examples"), a
refusal shaped like `{"ok": false, "stage": "workspace.register", "failures": [{"code": ...,
"requirement": "datasets.<id> must declare fields", ...}]}`.
**Got:**
```
{"error": "ValueError: datasets.adjusted-prices must declare fields", "failures": [],
 "stage": "unhandled", "detail": ".vqapr/diagnostics/unhandled.txt", ...}
```
`failures` is empty, `stage` is the literal string `"unhandled"` rather than a pipeline stage name,
and the only reason the message was legible at all is that the raw Python exception text happens
to say what key is missing. The `detail` path is a full Python traceback rooted in
`D:\...\qlibx\src\vqapr\cli\register.py`, i.e. resolving this required looking at a stack trace
that names framework source files and line numbers — the CLI itself put qlibx internals in front
of me, unprompted, to answer a question `--help` should have answered up front.
**Cost:** ~3 minutes: read the one-line `ValueError`, matched `fields` against nothing in
`register --help`, guessed it wants the same `fields=(...)` shape seen in the scaffolded
datamodel's `DataRequirement.of(..., fields=("close",), ...)`, and used that as the pattern for a
dataset-level `fields` mapping.
**Fix:** validate declaration-required keys the same way component validation apparently does
elsewhere (structured `failures[]` entry with `requirement`/`observed`), rather than letting a bare
`ValueError` fall through to `stage: "unhandled"`. A required-key error is not unhandled — it is
the single most common first mistake, and the framework already knows its own schema well enough
to name the missing key in the exception text; it just needs to put that in `failures[]` instead
of a traceback file.
**Severity:** blocked — the *documented contract* ("read failures first") was confidently wrong
for this input: `failures` was empty and useless, and the real answer only came from an exception
string that happened to be quotable, plus a mental model borrowed from an unrelated scaffold
(component `fields=(...)`) rather than anything the CLI told me about dataset declarations
specifically.

### F-006 — datasets require a `source_id` referencing a separately-registered `source`, and nothing before the second refusal said so

**Doing:** re-running `vqapr register workspace/adjusted_prices.yaml` after fixing F-005 (adding
`fields`).
**Expected:** either success, or — since `vqapr list` enumerates `sources` as its own kind
separate from `datasets` — some earlier document (`register --help`, the SKILL.md rung-1 steps, or
the first refusal) mentioning that a dataset declaration depends on a source that must exist or be
declared first. Rung 1 of SKILL.md lists "dataset, source, component, execution input, agenda" as
five peer nouns to register, which reads as five independent things, not as dataset depending on
source.
**Got:** the exact same failure shape as F-005 — `stage: "unhandled"`, `failures: []`, and a bare
`ValueError: datasets.adjusted-prices must declare source_id`. Confirms F-005 was not a one-off:
required-key validation for dataset declarations goes through this path every time, so every
missing key costs one round trip and one traceback read, one key at a time, with no way to learn
the full required set from the refusal itself.
**Cost:** ~2 minutes to read the new key name and infer that `source_id` names a `sources`
declaration (not, e.g., a free-text label), based only on `vqapr list`'s enumeration of `sources`
as a distinct registrable kind. What a source declaration itself must contain is still unknown at
this point — untested until the next register attempt.
**Fix:** the same fix as F-005 covers this — structured `failures[]` with all missing required
keys at once (not one ValueError per retry), which would have surfaced `fields` and `source_id`
together on the very first attempt.
**Severity:** slowed (the concept — dataset needs source — had to be inferred from a sibling
command's output rather than being told, but the path forward was findable without asking; not
counted as this run's second `blocked` because it is the same underlying defect as F-005, not an
independent failure)

### F-007 — `source_id` names something that cannot be declared in a top-level `sources:` section; the error that demanded it and the error that rejects it disagree

**Doing:** adding a `sources:` top-level section to the declaration to satisfy F-006's
`source_id` requirement, modeled directly on `vqapr list`'s five other declaration kinds and on
the register refusal itself, which named the missing key `source_id` without saying where a
source is declared.
**Expected:** registration to proceed to dataset validation (schema/column checks against the
parquet), since `sources` reads as a first-class declaration kind — `vqapr list sources` exists as
a command.
**Got:**
```
ValueError: unknown section(s): sources; this command registers datasets, execution_inputs,
agendas, components, strategy_configs, valuation_configs, monitoring_policies
```
Note what is missing from that list: `sources` is not in it, despite `datasets.adjusted-prices
must declare source_id` (F-006) implying a `source_id` refers to something registrable, and
despite `vqapr list {datasets,sources,components,agendas,execution-inputs,...}` treating `sources`
as a first-class listable kind on equal footing with the rest. Two different parts of the same CLI
disagree about whether `sources` is a section you write into a declaration.
**Cost:** this is the third distinct failure reason on the same `vqapr register
workspace/adjusted_prices.yaml` command (F-005: missing `fields`, F-006: missing `source_id`,
F-007: `source_id`'s referent cannot be declared where the previous error implied). Per
MISSION-A.md's stop condition 3 ("three attempts at the same command failed for three different
reasons"), this is the trigger — stopping here rather than guessing a fourth shape for `source_id`
(embedding it inline under `datasets.adjusted-prices.source: {...}`, or some other spelling not
yet tried, would be exactly the kind of guess the SKILL.md says this skill "never" does: "Guesses
missing semantics").
**Fix:** either `register`'s accepted-sections error should list `sources` if `list sources` is a
real workspace concept fed by something other than `register`, or `datasets.<id> must declare
source_id` should name where a source_id comes from (inline under the dataset, a different CLI
verb entirely, e.g. `vqapr new source`, or a fixed/derived value) instead of a bare key name that
looks declarable but is rejected the moment it is declared.
**Severity:** blocked — a confidently-issued requirement (`must declare source_id`) and a
confidently-issued rejection (`unknown section(s): sources`) contradict each other, and nothing in
`--help`, the SKILL.md, or either error message resolves the contradiction. This is the run's
second `blocked` entry (F-005 was the first), so MISSION-A.md stop condition 2 is also satisfied
here independently of condition 3.

## Derivation

## Strategy and run

## Measurement
