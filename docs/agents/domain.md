# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring
the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root, or
- **`CONTEXT-MAP.md`** at the repo root if it exists — it points at one `CONTEXT.md` per
  context. Read each one relevant to the topic.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't
suggest creating them upfront. The `/domain-modeling` skill (reached via
`/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or
decisions actually get resolved.

As of setup, none of them exist yet. That is the expected starting state.

## File structure

This is a **single-context** repo — one `CONTEXT.md` and one `docs/adr/` at the root. No
monorepo signals were present at setup (no workspace manifest, no `packages/*/src`).

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-....md
│   └── 0002-....md
└── viewer/, surveys/, .claude/
```

If this repo ever splits into genuinely independent contexts, switch to a root
`CONTEXT-MAP.md` pointing at per-context `CONTEXT.md` files, with context-scoped
`docs/adr/` beside each.

## Scope: what these docs govern here

This repo is a **deep-research survey project**, not a conventional application, so the
ADR/CONTEXT machinery applies to a narrower surface than usual:

- **In scope** — the harness and tooling: `viewer/` (the markdown viewer app and its
  `tools/` gate suite), `.claude/` (rules, skills, commands, hooks), `.githooks/`,
  `scripts/`. Architectural decisions about *these* belong in `docs/adr/`.
- **Not in scope** — survey *content* under `surveys/**`. That is governed by its own
  conventions: `order.json` manifests, `references.md` with the source-tag invariant, and
  the rules in `.claude/rules/` (`math-authoring.md`, `citation-integrity.md`,
  `cross-linking.md`). Do not file an ADR to justify a survey's technical claim — that is
  what the survey's own derivations and citations are for.

**Where decisions already live.** This repo predates these docs and already has a durable
decision trail in `decisions/` (dated records with *Context / Decision / Alternatives
considered / Consequences / Refs*, indexed in `decisions/INDEX.md`, and gated at pre-push).
`docs/adr/` and `decisions/` are not rivals: `decisions/` is the operational trail for
"why we did it this way in this session", ADRs are for durable architectural commitments a
future reader must not silently violate. When in doubt, write a `decisions/` record — that
is the convention `CLAUDE.md` mandates, and it is the one that is mechanically checked.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a
hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms
the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're
inventing language the project doesn't use (reconsider) or there's a real gap (note it for
`/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently
overriding:

> *Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…*
