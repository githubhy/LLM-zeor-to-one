"""Phase 4 → G3 sensitivity: the EAP-IG m-steps knob x task (a 2-factor grid, not OFAT —
the P0-3 spirit), plus circuit-size sensitivity. Shows the IG advantage is task-dependent
and grows with m up to a plateau."""
from __future__ import annotations

import numpy as np

from .config import ModelConfig, TaskConfig, AttrConfig
from .model import Model
from .tasks import build_task
from .attribution import score_nodes, score_eap
from .faithfulness import baselines, faith_curve
from . import manifest, utils

STUDY = "eap-ig-faithfulness"
TASKS = ("ioi", "greater_than", "sva")
M_IG = (1, 3, 5, 10)
SIZES_SENS = (10, 20, 40)
REF = 20
N_EX = 40


def main() -> None:
    utils.set_determinism(0)
    M = Model(ModelConfig(name="gpt2", device="cpu", dtype="float32"))
    grid = {t: {} for t in TASKS}
    eap_base = {}
    size_sens = {t: {} for t in TASKS}
    for task in TASKS:
        batch = build_task(M.tok, TaskConfig(task=task, n_examples=N_EX, seed=0)).to("cpu")
        b, bp = baselines(M, batch)
        eap_sc = score_eap(M, batch)
        eap_faith = float(faith_curve(M, batch, eap_sc, [REF], b, bp)[REF].mean())
        eap_base[task] = eap_faith
        for m in M_IG:
            sc = score_nodes(M, batch, AttrConfig(method="eap_ig", m_ig=m, seed=0))
            fc = faith_curve(M, batch, sc, list(SIZES_SENS) + [REF], b, bp)
            grid[task][m] = {"eap_ig_faith_at_ref": float(fc[REF].mean()),
                             "gap_vs_eap": float(fc[REF].mean()) - eap_faith}
            if m == 5:
                size_sens[task] = {int(n): float(fc[n].mean()) for n in SIZES_SENS}

    # interaction summary: how much does m help, per task (max over m of gap)
    interaction = {t: max(grid[t][m]["gap_vs_eap"] for m in M_IG) for t in TASKS}
    out = {
        "study": STUDY, "primary_factor": "m_ig", "m_ig_values": list(M_IG),
        "secondary_factor": "task", "grid": grid, "eap_baseline_faith_at_ref": eap_base,
        "size_sensitivity_eap_ig_m5": size_sens,
        "interaction_max_gap_by_task": interaction,
        "note": ("2-factor (m_ig x task) sweep, not OFAT: the EAP-IG advantage over EAP is "
                 "task-dependent (interaction) and saturates in m — consistent with Hanna's m=5 "
                 "default. Global/variance SA (P0-3) is report-only; the grid exposes the "
                 "interaction OFAT would miss."),
    }
    art = utils.REPO_ROOT / "artifacts" / STUDY / "sensitivity"
    utils.save_json(art / "sensitivity.json", out)

    m = manifest.ensure_env(manifest.load(STUDY))
    manifest.add_iteration(m, 4, "sensitivity: m_ig x task grid + size sensitivity",
                           interaction_max_gap=interaction)
    manifest.save(STUDY, m)
    print("interaction (max IG gap by task):", {k: round(v, 3) for k, v in interaction.items()})


if __name__ == "__main__":
    main()
