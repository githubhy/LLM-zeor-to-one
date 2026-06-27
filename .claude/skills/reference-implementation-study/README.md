# reference-implementation-study — updates & options

Maintainer/user-facing index of this skill's **improvement layer**: the switchable modes,
the per-item flag registry, and how each item is enforced. The canonical workflow lives in
`SKILL.md`; this README documents what the improvement flags do and how to turn them on.

The skill turns a completed `deep-research-survey` into working reference code, reproducible
comparative experiments, and an engineering recommendation, via 6 gated phases (Scenario →
Implementation/G1 → Baseline/G2 → Sensitivity/G3 → Precision/G4 → Report). The items below are
**additive enhancements** layered on that baseline — all default-off.

## Modes (selected via `$ARGUMENTS`)

| Mode | Effect |
|---|---|
| **`original`** (default) | Baseline 6-phase workflow only. No `addenda/` file is read — behaviour byte-for-byte unchanged. |
| **`proposed`** | Applies **all 13 improvement items** (P0-1 … P2-4). |
| **`flags: <ids>`** | Applies only the named items, e.g. `flags: P0-4,P0-5` — the per-item lattice for cherry-picking or item-by-item A/B ablation. |

**Lazy loading.** Improvement text lives in `addenda/` and costs zero tokens unless a non-`original`
mode is active. When a mode is set: read `addenda/global.md` once, then read `addenda/phase-N.md`
just-in-time when phase N begins — and only if `proposed` is set or one of that phase's item ids is
in the active `flags` set. Pass the active flags to the gate validator as `--flags <ids>` so its
optional checks fire. Record the active mode/flags in the study doc. Registry of record:
`bench/reference-implementation-study/items.json` (13 items) — **not yet present in this repo**.
The registry and bench scenarios are not mirrored here; `original` mode needs no registry, and the
`proposed`/`flags` modes are fully driven by the `addenda/` files (graceful degradation).

## The 13 items (two improvement passes)

A first improvement pass added 9 items; a second added 4. Grouped by tier:

| ID | Tier | Phase / Gate | What it adds | Pass |
|---|---|---|---|---|
| **P0-1** | P0 | 2 / G1 | Determinism *verified* (re-run + hash compare), not asserted | v1 |
| **P0-2** | P0 | 3 / G2 | Pairwise paired-seed significance + effect size (CIs are not a significance test) | v1 |
| **P0-3** | P0 | 4 | Global/variance-based SA (Morris then Sobol) — catches interactions OFAT misses | v1 |
| **P0-4** | P0 | 3 / G2 | Error-event Monte-Carlo stopping rule + binomial CI (Wilson / Clopper–Pearson) for rate metrics, replacing fixed-N + Gaussian-t | **v2** |
| **P0-5** | P0 | 2 / G1 | Correctness oracle (analytical / reference / metamorphic) — a wrong implementation fails G1 | **v2** |
| **P1-1** | P1 | 4 | Bayesian-optimisation HPO (Optuna / Ax) with a grid-vs-Bayesian switch rule | v1 |
| **P1-2** | P1 | 6 | Explicit multi-metric aggregation + sensitivity-to-weights | v1 |
| **P1-3** | P1 | global / G2 | Environment + provenance pinning (OS / Python / lib versions + git hash) | v1 |
| **P1-4** | P1 | 3 / G2 | Measured complexity/runtime — warmup + distribution (not a bare mean) + op-count + scaling cross-check on ≥2 sizes | **v2** |
| **P2-1** | P2 | 2 / G2 | Uniform data+metric contract via a registry, not just a uniform call interface | v1 |
| **P2-2** | P2 | 6 / G2 | Reproduce-from-artifacts validator + per-trial raw-output release | v1 |
| **P2-3** | P2 | 5 / G4 | Reduced-precision DoE over bit-width × quantization-structure (≥2 structures) | v1 |
| **P2-4** | P2 | 6 | Pareto / non-dominated analysis — dominated candidates excluded; the front is the defensible set | **v2** |

## Enforcement: gate-checked vs report-only

Nine items are **machine-checked at a gate** — `python validate_gate.py <study> <gate> [<topic>]
--flags <id>` appends an extra check that must pass. Authoritative `FLAG_GATE` map:

```
P0-1 → G1   P0-2 → G2   P0-4 → G2   P0-5 → G1
P1-3 → G2   P1-4 → G2   P2-1 → G2   P2-2 → G2   P2-3 → G4
```

Four items are **report-quality, judged (no gate check)**: P0-3, P1-1, P1-2, P2-4.

The flag checks are additive and gate-scoped: with no `--flags`, every gate behaves exactly as in
`original` mode. (Verified at the CLI: `G2` with no flags = 7/7 baseline checks; `G2 --flags
P0-4,P1-4` = 11/11 with the four extra lines present.)

## Practical flag-set recipes

- **Machine-checked rigor only** (all gate-enforced): `flags: P0-1,P0-2,P0-4,P0-5,P1-3,P2-1`
- **LLM eval study** (rate metrics + correctness dominate): `flags: P0-4,P0-5,P0-2,P1-4`
  — P0-4 is the highest-value addition here; fixed-N + Gaussian-t is the wrong estimator for
  pass@k / accuracy / win-rate (at a pass rate near 1e-2 on a hard benchmark, with only a handful
  of passing items, the Gaussian CI lower bound can go negative).
- **Everything**: `proposed`.

## Caveats

- **P1-1 (Bayesian HPO)** is the one item marked **inconclusive** from v1 — its edge only shows on
  ≥3-dim or expensive objectives and needs a real Optuna/Ax run to confirm, not a cheap proxy.
- The **v2 items (P0-4, P0-5, P1-4, P2-4)** are verified per-item (4/4) but were **not** exercised
  inside a full end-to-end 6-phase study (the v2 pass ran in `quick` mode, which skips the
  end-to-end A/B). P2-2 / P2-3 from v1 are similarly "mechanism-verified, not end-to-end."
- **P2-4 scope note:** a monotone positive-weight composite can never strictly rank a *dominated*
  candidate first. P2-4's value is *certifying* dominance (suboptimal under every positive
  weighting) and *enumerating* the defensible front — not "catching a skewed-weight win."

## Where things live

```
.claude/skills/reference-implementation-study/
├── SKILL.md                 # canonical workflow + Modes and flags selector
├── README.md                # this file
├── phases/phase-1..6-*.md   # the 6 phases (each has a one-line addendum pointer)
├── addenda/global.md        # P1-3 (loaded once in non-original mode)
├── addenda/phase-2.md       # P0-1, P0-5, P2-1
├── addenda/phase-3.md       # P0-2, P0-4, P1-4
├── addenda/phase-4.md       # P0-3, P1-1
├── addenda/phase-5.md       # P2-3
├── addenda/phase-6.md       # P1-2, P2-2, P2-4
├── signoff.py               # one-shot mechanical gate board (G1–G4 + REPORT + CITE)
└── validate_gate.py         # gates G1–G4 + additive --flags checks
```

## References

- Item registry: `bench/reference-implementation-study/items.json` (13 items) — **not present in
  this repo**; the registry, bench scenarios, landscape evidence, and verification runs are
  maintained upstream and are not mirrored here. The `addenda/` files are self-contained, so the
  `proposed`/`flags` modes run without them (graceful degradation).
- The 13 items landed across two improvement passes (a first pass adding 9, a second adding 4); the
  detailed improvement-pass proposals and implementation reports are not mirrored into this repo.
