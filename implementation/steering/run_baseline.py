"""A3 baseline: steering-method head-to-head on GPT-2-small. Sweeps each method's strength,
traces the success-vs-coherence(KL) Pareto, and ranks methods at MATCHED coherence (prompting's
KL budget). Bootstrap CI over the neutral eval prompts. Reuses sae_frontier for the SAE clamp."""
from __future__ import annotations

import numpy as np

from .core import Steerer, SteerConfig
from implementation.eap_ig.stats import bootstrap_ci
from implementation.eap_ig.utils import REPO_ROOT, save_json, save_npz, environment, git_commit

STUDY = "steering-headtohead"
ALPHAS = (0.0, 1.0, 2.0, 4.0, 6.0, 8.0, 12.0)
CLAMPS = (0.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0)


def _interp_success(sweep, kl_target):
    """Linear-interpolate success at kl_target from a [(kl,success)] sweep sorted by kl."""
    pts = sorted(sweep, key=lambda p: p[0])
    kls = [p[0] for p in pts]; succ = [p[1] for p in pts]
    if kl_target <= kls[0]:
        return succ[0]
    if kl_target >= kls[-1]:
        return succ[-1]
    return float(np.interp(kl_target, kls, succ))


def main() -> None:
    S = Steerer(SteerConfig(layer=6, device="cpu", seed=0))
    vec = S.diff_in_means_vector()
    sae, fidx = S.sae_clamp_setup()

    prompting = S.evaluate("prompting", 0)
    dim = [S.evaluate("diff_in_means", a, vec=vec) for a in ALPHAS]
    sae_c = [S.evaluate("sae_clamp", c, sae_clamp=(sae, fidx)) for c in CLAMPS]

    kl_budget = prompting["kl"]
    dim_sweep = [(r["kl"], r["success"]) for r in dim]
    sae_sweep = [(r["kl"], r["success"]) for r in sae_c]
    matched = {
        "prompting": prompting["success"],
        "diff_in_means": _interp_success(dim_sweep, kl_budget),
        "sae_clamp": _interp_success(sae_sweep, kl_budget),
    }
    ranking = sorted(matched, key=lambda k: matched[k], reverse=True)

    # bootstrap CI on each method's success at ~matched budget (nearest swept point)
    def _ci(res_list, kl_target):
        r = min(res_list, key=lambda x: abs(x["kl"] - kl_target))
        return bootstrap_ci(r["success_per"], n_boot=5000, seed=0)
    cis = {
        "prompting": bootstrap_ci(prompting["success_per"], n_boot=5000, seed=0),
        "diff_in_means": _ci(dim, kl_budget),
        "sae_clamp": _ci(sae_c, kl_budget),
    }

    summary = {
        "study": STUDY, "layer": 6, "kl_budget_matched": kl_budget, "sae_feature_idx": fidx,
        "methods": {
            "prompting": {"metrics": {"success_at_matched_kl": matched["prompting"],
                                      "success_ci95": list(cis["prompting"][1:]),
                                      "kl": prompting["kl"]}},
            "diff_in_means": {"metrics": {"success_at_matched_kl": matched["diff_in_means"],
                                          "success_ci95": list(cis["diff_in_means"][1:]),
                                          "kl": kl_budget}},
            "sae_clamp": {"metrics": {"success_at_matched_kl": matched["sae_clamp"],
                                      "success_ci95": list(cis["sae_clamp"][1:]),
                                      "kl": kl_budget}},
        },
        "ranking_at_matched_coherence": ranking,
        "pareto": {"diff_in_means": dim_sweep, "sae_clamp": sae_sweep,
                   "prompting_point": [prompting["kl"], prompting["success"]]},
        "seeds": [0],
    }
    base = REPO_ROOT / "artifacts" / STUDY
    save_json(base / "baseline" / "summary.json", summary)
    save_npz(base / "baseline" / "pareto.npz",
             dim_kl=np.array([p[0] for p in dim_sweep]), dim_succ=np.array([p[1] for p in dim_sweep]),
             sae_kl=np.array([p[0] for p in sae_sweep]), sae_succ=np.array([p[1] for p in sae_sweep]))
    save_json(base / "study-manifest.json", {
        "study": STUDY, "environment": environment(), "git_commit": git_commit(),
        "iterations": [{"phase": 3, "note": "steering head-to-head Pareto + matched-coherence ranking",
                        "ranking": ranking, "matched_success": matched}]})
    print("matched-coherence success:", {k: round(v, 3) for k, v in matched.items()})
    print("ranking @ matched coherence:", " > ".join(ranking))


if __name__ == "__main__":
    main()
