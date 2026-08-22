# Handoff — 2026-08-22

Setup only. **No replication work has started, deliberately** — see below.

Read `README.md` first for why this directory exists. This file carries state.

---

## Where things stand

| | |
|---|---|
| vqapr | `0.1.0a11`, editable from `../../qlibx`, verified importing (134 public exports) |
| torch | `2.9.1+rocm7.2.1` restored, `rocm_available: true`, AMD Radeon 8060S |
| testbed | `README.md`, `FRICTION.md`, `OPERATIONS.md`, `PROFILING.md`, this file |
| skill | **not installed — `vqapr agent install` does not exist.** `FRICTION.md` F-001 |
| replication work | none |

Uncommitted in `kaist-thesis`: `pyproject.toml`, `uv.lock`, `.gitignore`, and this untracked
directory.

---

## Read this before starting

**The first agent to do replication work here should be one that does not know vqapr.**

That is purpose 1 in `README.md` and it is the only one of the three that can be spent. The
friction log is only writable by someone who has not yet learned why the framework is shaped the
way it is — after that, every entry becomes a reconstruction.

Concretely, whoever picks this up:

- works from the installed package, its docstrings and `qlibx/docs/` — **not** from
  `kwam-enhanced-index/vqapr-testbed/`, which has already solved most of the same problems;
- writes `FRICTION.md` entries **as they happen**, before resolving them;
- does not read `qlibx/src/` to work out what a public function means. If that is necessary, that
  is itself the finding, and it is an `F-` entry.

If you already know this framework well, the useful thing you can do here is **not** to start —
it is to hand it to an agent that does not.

---

## Environment

```
kaist-thesis   C:/Users/chlje/DevProjects/kaist-thesis        branch master
qlibx          C:/Users/chlje/DevProjects/qlibx               0.1.0a11, branch jaepil-develop
```

`pyproject.toml` now carries `vqapr>=0.1.0a10` with `[tool.uv.sources] vqapr = { path = "../qlibx",
editable = true }`. The pin floor is a10; a11 is what resolved.

### GPU — the one trap in this repository

`.venv` carries a vendor ROCm PyTorch that **is not in `uv.lock`**. A plain `uv sync` replaces it
with a PyPI CPU build. That happened during this setup and was restored:

```powershell
uv pip install --python .venv\Scripts\python.exe -r guijarro-ordonez-2025-replication\config\rocm-windows-7.2.1-requirements.txt
uv run --no-sync python guijarro-ordonez-2025-replication/scripts/verify_rocm_environment.py --skip-smoke
```

Use `uv run --no-sync` for anything touching torch. The neighbouring replication has **496
checkpoints** that are not cheap to reproduce.

---

## What is being reproduced

`../guijarro-ordonez-2025-replication/` — Guijarro-Ordonez, Pelger & Zanotti (2025), "Deep Learning
Statistical Arbitrage". Its own `README.md` and `docs/` are the contract; this testbed does not
restate them. Two things from there matter immediately:

- **The Korean residual sample is 2020-01-02 ~ 2026-07-20**, with policy OOS from 2024-01-19 after
  a 1,000-day training window. That is not the paper's 1998–2016 design, and the replication says
  so plainly. Compare against *its* numbers, not the paper's US ones.
- **`adjusted_prices.return` carries no cash dividend**, and the accounting is fixed-3-month-lag
  non-PIT. `docs/data-requirements.md` records what is closed and what is not. A registration that
  gets `available_at` wrong is a look-ahead the framework cannot detect for you.

The cheapest first target is `estimate-pca` → `simulate-pca --simulation-model ou_threshold`: it
already runs next door, produces 275,711 residuals, and needs no GPU.

---

## Suggested first move

Do not start with the strategy. Start with **registration**, and stop after it:

1. Register `adjusted_prices.parquet` as a dataset — prices and tradability, `available_at` at the
   Korean session close.
2. Run `vqapr list` against the workspace and read back what was declared.
3. Write down everything that was ambiguous while doing it.

Two reasons. Registration is where an agent that does not know the framework meets its first real
decision — what `available_at` *means* — and it is the step the missing skill was specifically
built to talk through (`agent/skill/README.md`: "등록 이전부터 개입한다. error 이후가 아니다").
Whatever friction shows up there is the strongest evidence this testbed can produce about what the
skill is worth.

---

## Open

- `vqapr agent install` — documented in `qlibx/src/vqapr/agent/skill/README.md`, not implemented,
  no `SKILL.md` in the tree. F-001. Whether to build it, or to run purpose 1 without it and use
  the result as the specification, is a decision for the owner.
- Nothing else. Purposes 2 and 3 have no entries yet because no code has been written.
