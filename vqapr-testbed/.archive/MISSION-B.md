# Mission B — registration, and the friction it costs

You have never used `vqapr`. That is the qualification for this task, not a gap in it, and it is
spendable exactly once: the moment you understand why something is the way it is, you stop being
able to report honestly that it was confusing.

Read `README.md` in this directory for why the testbed exists. Read the **Environment** and
**Data** sections of it before starting.

---

## Do not read these

They contain another reader's findings, and knowing them in advance destroys what this mission
measures:

- `FRICTION.md`
- `MISSION-A.md`
- `HANDOFF.md`
- `.mission-a-archive/`

Write your log to **`FRICTION-B.md`** instead, creating it. The entry format is reproduced below so
you never need to open the other file.

If you open any of them by accident, say so plainly in your report. An honest note costs nothing;
a silent one makes the whole measurement worthless.

---

## The task

**Register `adjusted_prices.parquet` as a vqapr dataset, and stop.**

```
data/kaist_pilot/canonical/common/korean_equity/adjusted_prices.parquet
```

relative to the repository root above this directory, shared with the replication next door.

Read `../guijarro-ordonez-2025-replication/docs/data-requirements.md` before registering. A
registration that gets `available_at` wrong is a look-ahead, and the framework cannot detect that
for you.

Then read it back with `vqapr list datasets`.

**Do not continue into derivation, strategy, or a run.** Stopping is a requirement of the mission,
not a limit on your ability.

---

## Stop conditions

Stop and report when **any** of these is true:

1. The dataset is registered and `vqapr list datasets` reads it back correctly.
2. You have written your **second** `blocked` entry in `FRICTION-B.md`.
3. Three attempts at the same command have failed for three different reasons.

---

## Rules

**Work only from the installed package.** `vqapr --help`, `vqapr <verb> --help`, the installed
skill at `../.agents/skills/vqapr/SKILL.md`, and this repository's own documents.

**Do not read `../../qlibx/`.** Not `src/`, not `docs/`, not its tests. If you find yourself wanting
to, that wanting is itself the most valuable thing you can record — write down what you were trying
to learn and what you had already tried, then find another way or stop. If you do read it, say so
in your log.

**Do not use `uv sync`.** It resolves `torch` from PyPI and silently replaces the vendor ROCm build
the neighbouring replication needs. Use `uv run --no-sync`.

**Write friction before resolving it.** Not after.

---

## Entry format

```markdown
### F-B00N — one line, in the reader's words not the framework's

**Doing:** what was being attempted
**Expected:** what you thought would happen, and why
**Got:** what actually happened, verbatim if it was an error
**Cost:** how long, and how it was resolved — docs, help output, trial and error
**Fix:** what would have prevented it. A message, a docstring, a default, a shipped example.
**Severity:** blocked / slowed / surprised
```

`blocked` means work stopped. `slowed` means it cost real time but a path existed. `surprised`
means it worked but not for the reason you expected — those are the most valuable and the easiest
to forget to write down, because nothing went wrong.

If a command succeeds, exits 0, and gives a **confidently wrong answer**, record it as `blocked`
and say so explicitly. That case matters more than finishing the registration.

---

## What counts as friction

- a required concept you had to infer rather than being told
- an error that named a stage rather than the declaration that caused it
- a registration that could be spelled two ways with no guidance
- **a CLI verb whose purpose you had to guess.** `vqapr --help` and `vqapr <verb> --help` are
  supposed to answer that without any other document
- **a refusal you could not act on.** A failure that says what is wrong but not what to do next is
  friction even when it is technically accurate
- **a required key you discovered one at a time.** If fixing one error only reveals the next, say
  how many round trips the declaration cost you

---

## Deliverable

`FRICTION-B.md`. The registration itself is secondary — if you reach a stop condition with a good
log and no registered dataset, the mission succeeded.

Report at the end: which stop condition fired, how many entries and their severities, whether the
dataset registered, the worst single point of friction in one sentence, whether the installed
`SKILL.md` helped or hindered with a specific example, and whether you ever wanted to read the
framework's source.

Be blunt. A polite report that hides confusion is a failed measurement.
