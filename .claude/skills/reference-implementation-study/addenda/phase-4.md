# Proposed-mode addendum — Phase 4 (load on demand)

Apply each block iff `proposed` is set OR its id is in the active `flags` set (`P0-3`, `P1-1`).

**[P0-3] Global / variance-based sensitivity (replaces OFAT-only).** One-factor-at-a-time grid
sweeps cannot detect parameter interactions and waste budget on non-influential parameters.
Use a two-stage global SA instead: (1) **Morris elementary-effects screening** to cheaply rank
all parameters by influence and flag interactions; (2) **Sobol variance-based indices**
(first-order + total) on the influential few. OFAT remains a fallback for a cheap visual
one-parameter picture. Use SALib (or equivalent). Store the design matrix + indices as a
persistent artifact.

**[P1-1] Bayesian-optimisation HPO.** Phase 4 is named "Sensitivity & Optimisation" but ships
no optimiser beyond grid. For tuning, use Bayesian optimisation (Optuna TPE or Ax/BoTorch) with
an explicit switch rule: **grid** when the space is <=2 dims and each eval is cheap; **Bayesian**
when >=3 dims or each evaluation is itself a multi-seed eval study (expensive objective — e.g. a
full benchmark pass per trial). Store the full optimisation trace (trials + values) as an artifact
so the search is auditable.
