# Proposed-mode addenda — global (load on demand)

Loaded only when `proposed` or any `flags:` is active (see `SKILL.md` → Modes and flags).
Apply each block iff `proposed` is set OR its id appears in the active `flags` set.

**[P1-3] Environment + provenance pinning.** Into `artifacts/<study>/study-manifest.json`,
record an `environment` block per iteration — OS, Python version, and the versions of the
load-bearing libraries (numpy, scipy, torch / transformers, and any eval-harness packages) —
plus the current git commit hash (and dirty/clean status). This is the Sacred/DVC
reproducibility mechanism: a stored config + seed is only reproducible if the environment that
produced it is also pinned. With flag `P1-3`, `validate_gate.py --flags P1-3` checks the manifest
carries the env block + git hash.
