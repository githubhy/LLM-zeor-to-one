#!/usr/bin/env python3
"""Migrate `.claude/crosslink-rejected.json` from basename-keyed to path-keyed pair_keys.

`bugs/2026-07-10-18`: `pair_key` was `base#sec|base#sec`. Four surveys in one corpus group
carry a `fundamentals.md`, so two genuinely different pairs could share a key — and
rejecting one suppressed the other. `generate_candidates` now keys on the repo-relative
path.

The migration is not a rename. Resolving `fundamentals.md#1.2` back to a file requires
exactly the information the bug destroyed. So:

  1. **Unique.** `(base, sec)` names exactly one section in exactly one group -> rewrite.
  2. **Score-disambiguated.** `(base, sec)` is ambiguous, but the ledger recorded the pair's
     cosine, and exactly one candidate combination reproduces it within tolerance -> rewrite,
     and say so. (Scores recorded before the 2026-07-10 container roll-up are stale, so this
     will not always resolve.)
  3. **Ambiguous or stale.** Everything else is written to a report for human adjudication and
     **carried through unchanged**. Never dropped, never guessed. A silently dropped rejection
     re-surfaces as a gap forever; a silently wrong one suppresses a real link forever.

Read-only by default. `--write` rewrites the ledger; `--report FILE` dumps the unresolved set.

    python viewer/tools/migrate-rejection-ledger.py
    python viewer/tools/migrate-rejection-ledger.py --write --report temp/ledger-adjudicate.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / ".claude" / "crosslink-rejected.json"
SCOPE = ROOT / ".claude" / "crosslink-scope"

_spec = importlib.util.spec_from_file_location("cl", ROOT / "viewer" / "tools" / "crosslink.py")
cl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cl)

TOL = 5e-4  # scores are stored rounded to 4 dp


def split_side(side: str) -> tuple[str, str]:
    base, sec = side.rsplit("#", 1)
    return base, sec


def build_index():
    """(base, sec) -> [(group, section_index, path)] and per-group vectors."""
    idx = defaultdict(list)
    per_group = {}
    for name, paths in cl.load_scope(str(SCOPE)).items():
        secs, _, _ = cl.parse_paths(cl.expand_paths(paths))
        vecs, _ = cl.build_vectors(secs)
        per_group[name] = (secs, vecs)
        for i, s in enumerate(secs):
            idx[(s["base"], s["sec"])].append((name, i, s["path"]))
    return idx, per_group


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = data.get("rejected", [])
    idx, per_group = build_index()

    migrated, by_score, unresolved = [], [], []
    for e in entries:
        key = e["pair_key"]
        if "/" in key:                      # already path-keyed; idempotent
            migrated.append(e)
            continue
        try:
            l, r = key.split("|")
            (lb, ls), (rb, rs) = split_side(l), split_side(r)
        except ValueError:
            unresolved.append({**e, "reason": "unparseable pair_key"})
            continue

        lc, rc = idx.get((lb, ls), []), idx.get((rb, rs), [])
        if not lc or not rc:
            unresolved.append({**e, "reason": f"section not found ({len(lc)} x {len(rc)})"})
            continue

        combos = [(x, y) for x in lc for y in rc if x[0] == y[0] and x[2] != y[2]]
        if not combos:
            unresolved.append({**e, "reason": "no same-group combination"})
            continue

        if len(combos) == 1:
            (g, i, p1), (_, j, p2) = combos[0]
            migrated.append({**e, "pair_key": "|".join(sorted([f"{p1}#{ls}", f"{p2}#{rs}"]))})
            continue

        # Ambiguous. Try the recorded cosine as a fingerprint.
        want = e.get("score")
        hits = []
        if want is not None:
            for (g, i, p1), (_, j, p2) in combos:
                secs, vecs = per_group[g]
                if abs(cl.cosine(vecs[i], vecs[j]) - want) <= TOL:
                    hits.append((p1, p2))
        if len(hits) == 1:
            p1, p2 = hits[0]
            by_score.append({**e, "pair_key": "|".join(sorted([f"{p1}#{ls}", f"{p2}#{rs}"]))})
            migrated.append(by_score[-1])
        else:
            unresolved.append({**e, "reason": f"{len(combos)} combinations, "
                                              f"{len(hits)} match the recorded score",
                               "combinations": [[c[0][2], c[1][2]] for c in combos]})
            migrated.append(e)          # carried through UNCHANGED, never dropped

    print(f"ledger entries:            {len(entries)}")
    print(f"  uniquely resolved:       {len(migrated) - len(by_score) - len(unresolved)}")
    print(f"  score-disambiguated:     {len(by_score)}")
    print(f"  UNRESOLVED (adjudicate): {len(unresolved)}")
    for u in unresolved:
        print(f"    {u['pair_key']}  score={u.get('score')}  -- {u['reason']}")
        for c in u.get("combinations", [])[:4]:
            print(f"        {c[0]}  <->  {c[1]}")

    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(json.dumps({"unresolved": unresolved}, indent=1,
                                             ensure_ascii=True), encoding="utf-8")
        print(f"\nadjudication report -> {a.report}")

    if a.write:
        if unresolved:
            print("\nrefusing to --write while entries are unresolved: a carried-through "
                  "basename key silently collides under the new scheme. Adjudicate first.",
                  file=sys.stderr)
            return 2
        migrated.sort(key=lambda r: r["pair_key"])
        LEDGER.write_text(json.dumps({"rejected": migrated}, indent=1, ensure_ascii=True),
                          encoding="utf-8")
        print(f"\nwrote {len(migrated)} path-keyed entries -> {LEDGER}")
    else:
        print("\n(dry run; pass --write to rewrite the ledger)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
