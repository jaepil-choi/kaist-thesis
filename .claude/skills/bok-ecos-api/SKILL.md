---
name: bok-ecos-api
description: Query and automate the Bank of Korea ECOS Open API without relying on XLS/XLSX documentation. Use for discovering Korean economic statistic table and item codes, retrieving bounded time series such as CPI/GDP/rates/FX, reading ECOS metadata or terminology, validating ECOS responses, and building reproducible ECOS data workflows.
---

# Bank of Korea ECOS API (adapter)

This skill is an adapter. It holds no ECOS instructions of its own.

The single source of truth is the shared agent skill at
`.agents/skills/bok-ecos-api/`, which is shared with Codex/OpenAI agents.

## What to do

1. Read `.agents/skills/bok-ecos-api/SKILL.md` in full, then follow it exactly
   as if its contents were written here — workflow, task routing, and
   guardrails included.
2. When that file says to read
   `references/api-reference.md`, read
   `.agents/skills/bok-ecos-api/references/api-reference.md`.
3. Every relative path inside those files is relative to the current repository
   root, not to this adapter. The CLI is
   `.agents/skills/bok-ecos-api/scripts/ecos_api.py`.

## Sync rule

Do not copy ECOS workflow, command examples, codes, or guardrails into this
file. Only the `description:` above is duplicated, because Claude Code needs it
in frontmatter for skill discovery — keep it byte-identical to the
`description:` in `.agents/skills/bok-ecos-api/SKILL.md`.

Any change to how ECOS is used goes in `.agents/skills/bok-ecos-api/`, and both
Claude and Codex pick it up with no edit here.
