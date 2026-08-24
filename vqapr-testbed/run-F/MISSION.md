# Mission F -- fresh-user vqapr friction measurement

You are a fresh user of the installed `vqapr` package. Your measurement, not a successful backtest,
is the deliverable.

## Hard boundary

- Work only in this `vqapr-testbed/run-F/` directory and write the final log to
  `../FRICTION-F.md`.
- Treat `vqapr` as an opaque installed distribution. Do not read the sibling `qlibx` repository,
  installed package source, site-packages source, Git history, or implementation files.
- Do not read prior `FRICTION*.md`, `.archive/`, old run directories, or `.vqapr/` outside run-F.
  Your ignorance is the instrument.
- You may use `vqapr --help`, every verb's help, the installed vqapr skill in this repository,
  documented public Python imports, user-project documentation (especially
  `guijarro-ordonez-2025-replication/docs/data-requirements.md`), and diagnostics that the CLI
  explicitly creates inside run-F.
- Another agent is changing qlibx transforms. Do not inspect or touch that work. Do not commit.
- Skip repository-wide tests, linters, formatters, and gates.

## Task

Act as a first-time user reproducing one small KRX strategy run:

1. Read `vqapr --help`, relevant verb help, and the installed vqapr skill.
2. Use `vqapr new` scaffolds wherever offered. Do not hand-author a shape before checking whether a
   scaffold exists.
3. Prepare a bounded real-data slice from the documented adjusted-prices data. Prove one known
   `available_at` instant before converting the whole slice.
4. Register the dataset, components, execution input, agendas, and configs needed by one run.
5. Attempt one complete `vqapr run`.

Write every friction point to `../FRICTION-F.md` **before resolving it**, using:

```markdown
### F-00N -- one line in the reader's words

**Doing:**
**Expected:**
**Got:**
**Cost:**
**Fix:**
**Severity:** blocked / slowed / surprised
```

A command that exits 0 and gives a confidently wrong answer is `blocked`. Keep package friction
separate from user/domain mistakes.

## Stop conditions

Stop when the first condition fires:

1. One full run completes.
2. Three `blocked` entries are logged.
3. Six attempts at the identical command produce no new information.

At the end, `../FRICTION-F.md` must report the fired stop condition, entry count and severities,
whether a run completed, the worst friction, one specific way the installed skill helped or
hindered, and whether you wanted to inspect package source. Preserve command-generated artifacts
inside run-F.
