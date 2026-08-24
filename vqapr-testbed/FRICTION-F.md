# Fresh-user vqapr friction log — Mission F

### F-001 -- The installed package did not put `vqapr` on my command path

**Doing:** Running the mission's first documented discovery command, `vqapr --help`, from a fresh test directory.
**Expected:** The installed `vqapr` command would print its top-level help so I could discover the supported workflow.
**Got:** The shell returned `error: command not found: vqapr` with exit code 127.
**Cost:** I could not begin CLI discovery or create any scaffold until I found a different invocation route.
**Fix:** Ensure the distribution installs the `vqapr` console script into the active environment, or state the required launcher command prominently in the installed skill and mission setup.
**Severity:** blocked
**Resolved:** `docs/implementations/055`. The installed skill now opens with both invocation forms:
bare `vqapr` for an activated environment and `uv run vqapr` for a uv-managed project. It explains
that a working uv command with a missing bare command means the environment is not activated, not
that the package is absent.

### F-002 -- A fresh scaffold target was reported as already existing

**Doing:** Creating every offered scaffold, beginning with `uv run vqapr new dataset --out dataset.yaml`.
**Expected:** The fresh run directory contained only `MISSION.md`, so the command would create `dataset.yaml` and continue to the remaining scaffolds.
**Got:** The first command returned structured `cli.input.file_exists`, saying `dataset.yaml already exists`, and the command chain stopped.
**Cost:** I had to stop scaffold generation and investigate whether the command created a partial artifact or whether the workspace was not actually fresh.
**Fix:** A refusing scaffold should distinguish a pre-existing file from a file it just created, and scaffold creation should be atomic with an unambiguous success response.
**Severity:** surprised

### F-003 -- The run template requires an Exchange that the CLI cannot scaffold

**Doing:** Registering every dependency named by the generated run spec after using every relevant `vqapr new` scaffold.
**Expected:** Because `exchange` is a required run-spec key naming a registered `Exchange`, `vqapr new` or the skill would provide the component shape and declaration.
**Got:** `vqapr new --help` offers only `datamodel` and `strategy` component scaffolds; neither the generated run spec nor the installed skill explains how to create the required Exchange.
**Cost:** The documented CLI path ended with an unregistrable required dependency, forcing public-API introspection or package-source inspection before a complete run could even be attempted.
**Fix:** Add `vqapr new exchange <id>` with a runnable implementation and declaration, or provide a built-in exchange ID explicitly in the run-spec template.
**Severity:** blocked
**Deferred:** the user explicitly reserved the Python public interface for a separate ground-up
rebuild. An Exchange scaffold would freeze the current constructor/import contract into generated
code, so 055 deliberately does not build it.

### F-004 -- The public Exchange class was not directly registerable as an object

**Doing:** Filling the missing scaffold gap with the documented public `KrxExchange` constructor and registering the resulting named object.
**Expected:** A declaration's `object_name` would accept the constructed public exchange object, or the public registration documentation would state that it must instead name a zero-argument factory/class.
**Got:** Registration refused with `component.load.construction_failed` and `TypeError: 'KrxExchange' object is not callable`; the diagnostic clearly identified the immediate mismatch.
**Cost:** One failed registration and another hand-written component iteration were required, though the structured refusal made the correction direction clear.
**Fix:** Document the callable/config contract beside `register_exchange`, and cover it in an exchange scaffold.
**Severity:** slowed
**Deferred:** same public-interface rebuild boundary as F-003. No current Python constructor or
registration callable contract was changed.

### F-005 -- The generated run spec says dates are valid, but the runner crashes on them

**Doing:** Ran `uv run vqapr run spec.yaml` after registering the dataset, components, execution input, agendas, and configs, using the scaffold's documented ISO date form for `start` and `end`.
**Expected:** The generated comments say each boundary may be an “ISO-8601 date or datetime,” so `"2024-01-02"` and `"2024-01-10"` would pass preflight.
**Got:** The command returned an unstructured `ValueError: start must be timezone-aware` at stage `unhandled`, with no failures or retry precondition.
**Cost:** The run could not start, and the error neither identifies the required timezone nor provides a valid boundary example.
**Fix:** Either accept date boundaries as the scaffold promises by interpreting them in the declared agenda timezone, or scaffold timezone-aware datetimes and return a structured input diagnostic.
**Severity:** slowed
**Resolved:** 055. The template now emits timezone-aware datetime boundaries. Bare dates and naive
datetimes are refused as `cli.input.value_invalid` with an explicit-offset example, rather than
reaching preflight as an unhandled ValueError.

### F-006 -- Filtering strategy configs by their component ID returned zero matches

**Doing:** Confirming the registered `f_krx_strategy` binding with `vqapr list strategy-configs --id f_`.
**Expected:** `--id` is documented as filtering declaration identity, and registration had reported strategy config ID `f_krx_strategy`.
**Got:** The filtered list returned zero items; an unfiltered list showed only agenda IDs, including `f-daily-rebalance`, and omitted the strategy component IDs that identify the configs.
**Cost:** I had to repeat the list without a filter and infer which hidden strategy config the agenda belonged to.
**Fix:** Include the strategy component/config ID in each list item and apply `--id` to that identity (or clearly name the filter as agenda filtering).
**Severity:** surprised
**Resolved:** 055. `list strategy-configs` now includes the nested strategy component ID, and
`--id` filters it. A test registers `my-alpha` and retrieves exactly one config with
`--id my-alpha`.

### F-007 -- The execution and agenda scaffolds produce an impossible same-instant fill

**Doing:** Retried the run with timezone-aware boundaries while retaining the generated `daily-rebalance` and `same_day` execution defaults, both at 15:30 Asia/Seoul.
**Expected:** Independently generated first-run templates would compose into a valid minimal run after their IDs and paths were filled in.
**Got:** Structured preflight refused all seven strategy occurrences with `preflight.execution.target_outside_horizon`, even though each reported target timestamp was visibly inside the run's date horizon.
**Cost:** The run remained blocked until I reasoned beyond the message that a close-known-at-15:30 decision cannot execute at that same instant and redesigned the cadence to leave a later executable snapshot.
**Fix:** Generate mutually compatible agenda and execution defaults, and state explicitly that execution must occur strictly after the strategy occurrence rather than only “inside the run horizon.”
**Severity:** slowed
**Resolved:** 055. Generated strategy/valuation occurrences are 15:29 and execution remains 15:30;
the template and preflight diagnostic explicitly say execution is strictly later. The generated
run end includes the final 15:30 target.

### F-008 -- Correcting the scaffolded cadence requires new identities all the way through

**Doing:** Moving the already-registered strategy occurrence from 15:00 to 14:59 so the 15:00 close snapshot would be a later execution target.
**Expected:** Re-registering the corrected agenda/config declaration during first-run setup would replace the invalid value or the CLI would provide an explicit workspace edit/reset path.
**Got:** Registration refused with `workspace.agenda.register.conflict`; the only offered remedy was a new identity, which also makes the existing strategy binding unusable.
**Cost:** A one-minute cadence correction now requires a new agenda ID, a new strategy component ID/config, and corresponding run-spec changes to preserve the immutable prior declarations.
**Fix:** Make generated defaults causally valid; additionally document a safe fresh-workspace reset/edit workflow for setup corrections.
**Severity:** slowed
**Resolved:** 055 for the CLI-independent part. Defaults are causally ordered. The skill explains
that registrations are immutable: preserve provenance with new IDs after meaningful work, or, in
a disposable first-run workspace, obtain destructive-reset approval, retain authored declarations,
remove only project-local `.vqapr/` state, and re-register.

### F-009 -- Correcting scaffold scheduling requires minting a second set of IDs

**Doing:** Changed the execution selector and agenda cadence to put fills after decisions, then re-registered the corrected declarations.
**Expected:** Before any successful run, re-registering the same IDs would replace declarations that only this fresh workspace had created.
**Got:** Structured conflicts said both IDs must keep their original declarations or use new identities; there is no update or unregister verb in top-level help.
**Cost:** I had to duplicate execution-input, agenda, and config identities and update the run spec instead of correcting the first-run declarations in place.
**Fix:** Document registration immutability in the templates and provide a safe workspace-local remove/replace workflow for declarations that have never participated in a run.
**Severity:** slowed
**Resolved:** same 055. All registration templates warn about immutability and distinguish
disposable setup reset from provenance-preserving new identities. No unsafe automatic replace verb
was added.

## Outcome

- **Stop condition fired:** 1 — one full run completed.
- **Entries:** 9 total — 2 blocked, 5 slowed, 2 surprised.
- **Run completed:** Yes. `uv run vqapr run f-run-spec.yaml` returned `ok: true`, `stage: run.complete`, `occurrences: 6`, and `account_version: 1`.
- **Worst friction:** F-003. The generated run spec required a registered Exchange, but neither the CLI scaffolds nor the installed skill supplied the required component/declaration path.
- **Package versus user/domain friction:** F-002 was testbed concurrency rather than package behavior. The remaining entries describe CLI availability, scaffold/documentation, listing, diagnostics, causality defaults, or immutable-registration friction; the KRX close-time correction itself followed the documented domain rule.
- **Installed skill:** It materially helped by making `available_at` semantics explicit; I proved `2015-01-02 15:00:00+09:00` round-trips through UTC as `2015-01-02 06:00:00+00:00` before converting the slice. It hindered the run path by omitting the Exchange construction remedy.
- **Wanted to inspect package source:** Yes, especially when no Exchange scaffold existed and when an in-horizon timestamp was reported as outside the horizon. I did not inspect implementation or installed source; I used public imports and CLI-created diagnostics inside `run-F`.
