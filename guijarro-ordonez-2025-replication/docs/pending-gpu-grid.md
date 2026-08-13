# Pending Korean GPU grid

The executable experiment specification is
`config/experiment-matrix.yml`. It separates the supported Korean
price-return grid from `data_blocked` and `not_applicable` specifications.
Completion is never inferred from an output directory or checkpoint alone.

## Run

From the repository root, after the ROCm/CUDA preflight and input transfer:

```powershell
uv run --no-sync python guijarro-ordonez-2025-replication/scripts/run_pending_gpu_grid.py
```

The runner expands the matrix in priority order, runs one GPU job at a time,
and stops on the first nonzero exit or failed artifact contract. A job is
skipped only when all three final artifacts exist and its audit matches the
factor family, K, policy, objective, lookback, epochs, rolling mode, holding,
costs, OOS dates, and subperiod count. SHA-256 hashes are recorded under a new
`outputs/orchestration/gpu-grid-*/` run directory.

Check current numbered-file and experiment-grid coverage separately:

```powershell
uv run --no-sync python guijarro-ordonez-2025-replication/run.py status
```

The runner is resumable across invocations. Completed audit-validated jobs are
skipped; an incomplete job resumes from its per-epoch checkpoint. Useful
bounded diagnostics are `--dry-run`, repeatable `--family FAMILY`, and
`--max-jobs N`.

## Finalize

Only after `run.py status` reports no `unrun` runnable experiment:

```powershell
uv run --no-sync python guijarro-ordonez-2025-replication/run.py report-strategies
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-robustness
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-interpretability
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-appendix
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-appendix-signals
uv run --no-sync python guijarro-ordonez-2025-replication/run.py build-risk-premium
uv run --no-sync python guijarro-ordonez-2025-replication/scripts/export_thesis_assets.py
uv run --no-sync python guijarro-ordonez-2025-replication/scripts/sync_replication_draft.py
```

The draft synchronizer refuses partial coverage. It fills runnable result cells
from generated CSVs while keeping IPCA, FF8, FF10/15, eight-year constant, and
actual-cost blockers explicit. Main Table 9 remains IPCA-specific; PCA
friction runs appear only in Appendix Table A.X.
