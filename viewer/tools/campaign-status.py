#!/usr/bin/env python3
"""Campaign status — the session-resume mechanism.

A campaign outlives the context that authored it. Sessions compact, agents fan out,
weeks pass. The harness's own task list is session-scoped, so the durable state has
to live on disk: campaign.json + the ledger. This renders it.

A fresh session with ZERO context should be able to run this and know exactly what
to do next.

  python viewer/tools/campaign-status.py                # all campaigns, summary
  python viewer/tools/campaign-status.py --residuals    # + the ledger table
  python viewer/tools/campaign-status.py --next         # just the next actionable task
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGNS = ROOT / "campaigns"
# `obsolete` = the task was REFUTED, not completed (its premise died). It must render
# distinctly from "done" -- laundering a refuted task into a tick is how a stale plan
# becomes a false record.
TICK = {"done": "x", "in-progress": "~", "blocked": "!", "todo": " ", "obsolete": "-"}


def load(cdir: Path):
    man = json.loads((cdir / "campaign.json").read_text(encoding="utf-8"))
    lpath = cdir / "ledger/measured.json"
    led = json.loads(lpath.read_text(encoding="utf-8")) if lpath.exists() else {"rows": []}
    return man, led


def actionable(tasks: dict) -> list:
    """Tasks whose deps are all done — the genuine work-front."""
    out = []
    for tid, t in tasks.items():
        if t["status"] in ("done", "obsolete"):
            continue
        if all(tasks[d]["status"] in ("done", "obsolete")
               for d in t.get("deps", []) if d in tasks):
            out.append(t)
    return sorted(out, key=lambda t: (t["phase"], t["id"]))


def main() -> int:
    ap = argparse.ArgumentParser(description="Campaign status / session resume.")
    ap.add_argument("--campaign")
    ap.add_argument("--residuals", action="store_true")
    ap.add_argument("--next", action="store_true")
    a = ap.parse_args()

    if not CAMPAIGNS.is_dir():
        print("no campaigns/")
        return 0
    dirs = [d for d in sorted(CAMPAIGNS.iterdir()) if (d / "campaign.json").exists()]
    if a.campaign:
        dirs = [d for d in dirs if a.campaign in d.name]

    for cdir in dirs:
        man, led = load(cdir)
        tasks = {t["id"]: t for t in man["tasks"]}
        phases = {p["id"]: p for p in man["phases"]}
        rows = led.get("rows", [])

        done = sum(1 for t in tasks.values() if t["status"] == "done")
        front = actionable(tasks)

        if a.next:
            for t in front[:5]:
                print(f"{t['id']:6s} [tier {t['tier']}] {t['title']}")
            continue

        print(f"\n=== {man['title']}  ({man['slug']}) ===")
        print(f"plan: {man['plan']}")
        print(f"gates: severity={man.get('gates',{}).get('severity')}   "
              f"tasks: {done}/{len(tasks)} done")

        # per-phase progress
        print("\nphases:")
        for pid in sorted(phases):
            ts = [t for t in tasks.values() if t["phase"] == pid]
            d = sum(1 for t in ts if t["status"] in ("done", "obsolete"))
            bar = "".join(TICK[t["status"]] for t in sorted(ts, key=lambda x: x["id"]))
            block = " [BLOCKING]" if phases[pid].get("blocking") else ""
            print(f"  {pid}  {d}/{len(ts):<2d} [{bar}] {phases[pid]['title']}{block}")

        mf = man.get("measure_first_gate") or {}
        if mf.get("task"):
            st = tasks.get(mf["task"], {}).get("status", "?")
            print(f"\nMEASURE-FIRST gate ({mf['task']}): {st.upper()} — "
                  f"blocks phases {mf.get('blocks_phases')}")

        if rows:
            outside = [r for r in rows if not r["residual"]["inside_envelope"]]
            inside = len(rows) - len(outside)
            # TWO definitions of "real gap" have been in active use across this campaign's
            # documents, and no document ever declared which it was on: (A) outside the envelope,
            # and (B) outside AND the sim's CI misses the envelope. Definition B reproduces the
            # historical counts exactly (T4.4's "25 -> 23", T4.2's "23 -> 22", "13 of 15"), so
            # "N of M remaining gaps" sentences are unreadable without knowing M. Both are printed,
            # labelled, so a reader can never again quote one and mean the other.
            # (2026-08-16 reconciliation; decisions/2026-08-16-real-gap-has-two-definitions.md)
            def _ci_misses(r):
                lo, hi = r["reference"]["envelope"]
                ci = (r["sim"] or {}).get("ci95")
                return True if not ci else (ci[1] < lo or ci[0] > hi)

            resolved = [r for r in outside if _ci_misses(r)]
            print(f"\nledger: {len(rows)} rows — {inside} inside the inter-company envelope "
                  f"(NOT defects)")
            print(f"        real gaps: {len(outside)} outside the envelope [definition A] · "
                  f"{len(resolved)} also CI-resolved [definition B]")
            if len(outside) != len(resolved):
                amb = [r["id"] for r in outside if r not in resolved]
                print(f"        the {len(outside) - len(resolved)} row(s) A counts and B does not "
                      f"(CI overlaps the envelope): {', '.join(amb)}")
            nb = sum(1 for r in rows if not (r["reference"] or {}).get("basis"))
            nc = sum(1 for r in rows if (r["sim"] or {}).get("ci95") is None)
            if nb or nc:
                print(f"        gaps: {nb} rows without a metric BASIS, {nc} without a CI")

        if a.residuals and rows:
            print("\n  real gaps (outside the envelope), worst first:")
            for r in sorted(outside, key=lambda r: -abs(r["residual"]["value"]))[:12]:
                lo, hi = r["reference"]["envelope"]
                print(f"    {r['id']:26s} resid {r['residual']['value']:+9.2f} {r['units']:3s}"
                      f"  sim {r['sim']['value']:9.2f}  env [{lo:.1f}, {hi:.1f}]  {r['status']}")

        print("\nNEXT (deps satisfied):")
        for t in front[:6]:
            print(f"  {t['id']:6s} [tier {t['tier']}] {t['title'][:78]}")
        if not front:
            print("  — nothing actionable; every remaining task is blocked")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
