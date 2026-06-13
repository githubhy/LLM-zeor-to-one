#!/usr/bin/env python3
"""Aggregate per-run result JSONs into a baseline-vs-improved comparison table.

LLM runs are noisy, so a single before/after pair is an anecdote. This reads N
result files per arm, computes mean / stdev / 95% CI per metric, and prints the
delta with a crude significance flag (CIs disjoint). Pure stdlib.

Each result file is JSON: {"arm": "baseline"|"improved", "metrics": {name: number_or_bool, ...}}
Booleans are treated as 0/1 (so e.g. silent_death or gate_passed become rates).

Usage:
  python3 ab_compare.py results/*.json
  python3 ab_compare.py --baseline 'results/base_*.json' --improved 'results/imp_*.json'
"""
import argparse
import glob
import json
import math
import statistics as st
from collections import defaultdict


def load(paths):
    arms = defaultdict(lambda: defaultdict(list))
    for p in paths:
        try:
            rec = json.load(open(p))
        except Exception as e:  # noqa: BLE001
            print(f"  (skip {p}: {e})")
            continue
        arm = rec.get("arm", "unknown")
        for k, v in (rec.get("metrics") or {}).items():
            if isinstance(v, bool):
                v = 1.0 if v else 0.0
            if isinstance(v, (int, float)):
                arms[arm][k].append(float(v))
    return arms


def ci95(xs):
    n = len(xs)
    if n == 0:
        return (float("nan"), float("nan"), float("nan"))
    m = st.mean(xs)
    if n == 1:
        return (m, m, m)
    sd = st.stdev(xs)
    half = 1.96 * sd / math.sqrt(n)
    return (m, m - half, m + half)


def main():
    ap = argparse.ArgumentParser(description="Baseline-vs-improved metric comparison with CIs.")
    ap.add_argument("results", nargs="*", help="result JSON files (arm read from each file)")
    ap.add_argument("--baseline", help="glob for baseline runs (overrides arm field)")
    ap.add_argument("--improved", help="glob for improved runs (overrides arm field)")
    args = ap.parse_args()

    if args.baseline or args.improved:
        arms = defaultdict(lambda: defaultdict(list))
        for arm, pat in (("baseline", args.baseline), ("improved", args.improved)):
            for p in glob.glob(pat or ""):
                rec = json.load(open(p))
                for k, v in (rec.get("metrics") or {}).items():
                    v = 1.0 if v is True else 0.0 if v is False else v
                    if isinstance(v, (int, float)):
                        arms[arm][k].append(float(v))
    else:
        paths = []
        for r in args.results:
            paths.extend(glob.glob(r))
        arms = load(paths)

    base, imp = arms.get("baseline", {}), arms.get("improved", {})
    metrics = sorted(set(base) | set(imp))
    nb = max((len(v) for v in base.values()), default=0)
    ni = max((len(v) for v in imp.values()), default=0)

    print(f"=== A/B comparison  (baseline n={nb}, improved n={ni}) ===\n")
    print(f"{'metric':<26}{'baseline':>20}{'improved':>20}{'delta':>10}{'sig?':>6}")
    print("-" * 82)
    for m in metrics:
        bm, blo, bhi = ci95(base.get(m, []))
        im, ilo, ihi = ci95(imp.get(m, []))
        delta = im - bm if not (math.isnan(im) or math.isnan(bm)) else float("nan")
        disjoint = (not any(map(math.isnan, [blo, bhi, ilo, ihi]))) and (ihi < blo or ilo > bhi)
        bcol = "n/a" if math.isnan(bm) else f"{bm:.3f}[{blo:.2f},{bhi:.2f}]"
        icol = "n/a" if math.isnan(im) else f"{im:.3f}[{ilo:.2f},{ihi:.2f}]"
        dcol = "n/a" if math.isnan(delta) else f"{delta:+.3f}"
        print(f"{m:<26}{bcol:>20}{icol:>20}{dcol:>10}{('YES' if disjoint else ''):>6}")
    print("\nsig? = 95% CIs disjoint (crude; with small n prefer a real test + more runs).")


if __name__ == "__main__":
    main()
