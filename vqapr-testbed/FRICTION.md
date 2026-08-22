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

_(first entries go here)_

## Derivation

## Strategy and run

## Measurement
