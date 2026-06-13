# Proposed-mode addenda — global (load on demand)

Loaded only when `proposed` or any `flags:` is active (see `SKILL.md` → Modes and flags).
Apply each block iff `proposed` is set OR its id appears in the active `flags` set.

**[P2-4] Progressive-disclosure hygiene.** Keep this `SKILL.md` concise (aim < 500 lines); push detailed rules into per-phase reference files that cost zero tokens until read; open any reference file > 100 lines with a table of contents.

**[P2-5] MAST per-phase failure checks.** Add a failure check at each phase and map it to a MAST category: Outline → coverage-gap check (are all must-have questions represented?) [specification]; Evidence/Synthesis → attribution-drift + hallucination pass [verification]; Report → the existing citation-audit gate [verification]; cross-agent → boundary-validation at the evidence→synthesis handoff [inter-agent].
