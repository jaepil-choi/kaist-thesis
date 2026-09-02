# Mission A — registration, and the friction it costs

You have never used `vqapr`. That is the qualification for this task, not a gap in it, and it is
spendable exactly once: the moment you understand why something is the way it is, you stop being
able to report honestly that it was confusing. Everything below protects that.

Read `README.md` and `HANDOFF.md` in this directory first. They own the context; this file only
says where to stop and what to write down.

---

## The task

**Register `adjusted_prices.parquet` as a vqapr dataset, and stop.**

```
data/kaist_pilot/canonical/common/korean_equity/adjusted_prices.parquet
```

shared with the replication next door. `HANDOFF.md` states the three steps: register the dataset
with `available_at` at the Korean session close, read it back with `vqapr list`, and record
everything ambiguous encountered on the way.

Read `../guijarro-ordonez-2025-replication/docs/data-requirements.md` before registering. A
registration that gets `available_at` wrong is a look-ahead, and the framework cannot detect that
for you.

**Do not continue into derivation, strategy, or a run.** Stopping is a requirement of the mission,
not a limit on your ability.

---

## Stop conditions

Stop and report when **any** of these is true:

1. The dataset is registered and `vqapr list datasets` reads it back correctly.
2. You have written your **second** `blocked` entry in `FRICTION.md`.
3. Three attempts at the same command have failed for three different reasons.

Condition 2 exists because a single root cause that cascades into five entries makes the log
useless for attribution. Two blockers is enough signal; the third would only be noise from the
first.

---

## Rules

**Work only from the installed package.** `vqapr --help`, `vqapr <verb> --help`, the installed
skill at `.agents/skills/vqapr/SKILL.md`, and this repository's own documents.

**Do not read `../qlibx/`.** Not `src/`, not `docs/`, not its tests. If you find yourself wanting
to, that wanting is itself the most valuable thing you can record — write down what you were trying
to learn and what you had already tried, then find another way or stop. If you do read it, say so
in `FRICTION.md`; an unlogged read makes the whole measurement worthless, and an honest one costs
nothing.

**Do not use `uv sync`.** It resolves `torch` from PyPI and silently replaces the vendor ROCm build
that the neighbouring replication needs; this already happened once and is recorded as F-002. Use
`uv run --no-sync`.

**Write friction before resolving it.** Not after. The entry format is at the top of `FRICTION.md`.

---

## What counts as friction

From `README.md`, unchanged:

- a required concept that had to be inferred
- an error that named a stage rather than the declaration that caused it
- a registration that could be spelled two ways with no guidance
- a lookback whose semantics only became clear after a wrong result

Two additions for this run:

- **a CLI verb whose purpose you had to guess.** `vqapr --help` and `vqapr <verb> --help` are
  supposed to answer that without any other document. Where they do not, that is a defect.
- **a refusal you could not act on.** A failure that tells you what is wrong but not what to do
  next is friction even when it is technically accurate.

Severities are `blocked`, `slowed`, `surprised`. If you get a **confidently wrong answer** — a
command succeeds, exits 0, and the result is not what the inputs meant — record it as `blocked`
and say so plainly in the entry. That case has no severity of its own yet, and finding one is
worth more than finishing the registration.

---

## What is already known

`F-001` is closed. `vqapr skill install` exists and the skill is installed in this repository at
`.agents/skills/vqapr/`. If it is unhelpful, that is now a *new* finding rather than a known gap —
say so specifically: which question you had, and what the skill said instead.

`F-002` is not a vqapr defect and is already recorded. Do not re-file it.

Nothing else about the CLI has been measured. The verbs, their help text, and their failure
messages were changed immediately before this mission and **no fresh reader has seen them.** That
is what you are measuring.

---

## Deliverable

`FRICTION.md`, extended in place. The registration itself is secondary — if you reach a stop
condition with a good log and no registered dataset, the mission succeeded.

Append to `HANDOFF.md`: where you stopped, which condition triggered it, and what the next reader
should not have to rediscover.
