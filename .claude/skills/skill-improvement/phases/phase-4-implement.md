# Phase 4: Implement (lazy flag-lattice)

## Goal
Make every proposed item an independently-toggleable, lazily-loaded, default-off flag.

## Steps (use `templates/lazy-flag-lattice.md` + `templates/items.schema.json`)
- Add a `## Modes and flags` selector to the target `SKILL.md`: `original` (default,
  unchanged) | `proposed` (all) | `flags: <ids>`. Include the lazy-loading paragraph.
- Create `addenda/<phase>.md` (and `addenda/global.md` for cross-phase items): one
  item-labelled block per improvement. Add a one-line pointer to each affected phase file that
  NAMES the phase's item ids (so a flag check can short-circuit the read). Build lazy from day
  one (gotcha #1).
- Write `bench/<target>/items.json` (registry: id, flag, phase, test_type, claim, test).
- If the skill has a validator/gate script, extend it with ADDITIVE, flag-gated checks
  (`--flags <ids>`) so structural items are machine-checked. Confirm default (no-flags)
  behavior is identical.

## Deliverable
The switchable skill (purely additive diff) + items.json.
