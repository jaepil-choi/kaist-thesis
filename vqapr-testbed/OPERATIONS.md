# Factor operations — what had to be written by hand

Purpose 2 in `README.md`. A paper replication is mostly cross-sectional and time-series operations
on a panel, and this one leans on them harder than a long-short alpha does. The question is which
of them belong in `vqapr.transforms` and which are this paper's own method.

## What the framework ships today

```
vqapr/transforms/cross_section.py   cross-sectional operations
vqapr/transforms/neutralize.py      projection / demeaning against a group or factor
vqapr/transforms/window.py          time-series windowing
vqapr/transforms/lookthrough.py     exposure through a holding
vqapr/transforms/missing.py         missing-data policy
```

Read them before writing anything. The previous testbed's `FINDINGS §2.1` is a warning worth
carrying: it reimplemented neutralisation as a demean, which removes a *level* where the paper
removed a *direction*, and the alpha's measured market beta went from −0.083 to −0.525 without
anything failing. The framework had the right operation; the reproduction did not use it.

## How to write an entry

```markdown
### OP-00N — the operation, named as a paper would name it

**Needed for:** which figure/table/step
**Written:** where it landed, how many lines
**Framework had:** the nearest existing thing, and exactly why it did not fit
**Generality:** would a second paper want this, or is it this paper's method?
**Verdict:** promote to `transforms/` | keep in a member | already exists, was not found
```

The last verdict value matters as much as the first. **"Already exists, was not found" is a
documentation defect**, and it should also get an `F-` entry in `FRICTION.md` — that is the failure
mode that cost the previous testbed a wrong beta.

## The promotion bar

A second **real** user, not a plausible one. `kwam-enhanced-index/AGENTS.md` states the same rule
for its experiments:

> 실험에서 재사용 가능한 logic이 production으로 승격될 때만 `src/`로 옮기고, 그때 해당 layer의
> unit test를 `tests/unit/`에 추가한다.

So an operation this paper needs and the enhanced-index book also needed is a candidate. An
operation only this paper needs stays in a member, however elegant it looks.

---

## Candidates from reading the paper, before any code

Written in advance deliberately, so the list can be checked against what was *actually* needed
rather than assembled to justify what got built. None of these are decisions yet.

| candidate | paper use | first guess |
|---|---|---|
| rolling PCA on a covariance window | residual construction, 252d covariance / 60d loading | probably general |
| residual extraction against a factor set | every residual in the paper | overlaps `neutralize` — check first |
| cross-sectional standardisation of a wide characteristic panel | 46 IPCA characteristics | probably general |
| rolling z-score / normalisation of a residual series | policy inputs | probably general |
| OU parameter estimation on a residual | `ou_threshold` policy | paper's own method |
| rank + winsorise a characteristic panel | IPCA inputs | check `cross_section` first |

## Entries

_(nothing yet — the point is to fill this from what was actually written)_
