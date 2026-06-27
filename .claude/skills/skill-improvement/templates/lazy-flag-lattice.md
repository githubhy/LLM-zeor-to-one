# Template — lazy flag-lattice for a target skill (Phase 4)

Copy this into the TARGET skill, substituting `<ITEM-ids>` and phase names. The improvement
layer must be PURELY ADDITIVE and DEFAULT-OFF.

## 1. Add to the target `SKILL.md` (after its intro, before its first section)

```markdown
## Modes and flags

Selected from the skill arguments (`$ARGUMENTS`):

- **`original`** (default) — baseline workflow only. Do NOT read any `addenda/` file. Current behavior, unchanged.
- **`proposed`** — apply ALL improvements (<first-id> … <last-id>).
- **`flags: <ids>`** — apply ONLY the named items, e.g. `flags: P0-1,P0-2` (per-item ablation).

**Lazy loading.** The improvement addenda live in `addenda/` and cost zero tokens unless a
non-`original` mode is active. When `proposed`/`flags:` is set: read `addenda/global.md` once,
then read `addenda/<phase>.md` just-in-time when you begin that phase — only if `proposed` is
set or one of that phase's item ids (named in the phase's pointer) is in the active `flags`
set. Apply a block iff `proposed` OR its id is in `flags`. Default stays `original` — no
`addenda/` file is read. Registry: `bench/<target>/items.json`.
```

## 2. One `addenda/<phase>.md` per phase that has items

```markdown
# Proposed-mode addendum — <Phase> (load on demand)
Apply each block iff `proposed` is set OR its id is in the active `flags` set (<ids>).

**[<id>] <Title>.** <What it changes, why, and — if machine-checkable — which validator flag enforces it.>
```

## 3. One-line pointer appended to each affected phase file

```markdown
## Proposed-mode addendum

Loaded on demand. If `proposed` or any of `flags: <ids>` is active, read `addenda/<phase>.md`
and apply the active blocks. In `original` mode, skip — do not read it.
```

## 4. (If the skill has a validator/gate script) add ADDITIVE flag-gated checks

Parse `--flags <ids>`; after the base checks, append per-item checks whose target gate matches
the current gate. With no flags the script must behave IDENTICALLY to before. Verify both.
