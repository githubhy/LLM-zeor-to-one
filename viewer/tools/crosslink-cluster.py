#!/usr/bin/env python3
"""crosslink-cluster.py — derive / validate the corpus groups in `.claude/crosslink-scope`.

`crosslink.py` scans each `[group]` of the scope file as an INDEPENDENT TF-IDF
corpus. Which surveys belong in which group is a modelling choice, and this tool
makes it reproducible instead of a matter of taste.

Method
------
* A **unit** is one survey directory, one top-level `surveys/*.md`, or one wiki.
* IDF is computed over **sections** (~3.3k docs), not units (~50). Unit-level IDF
  leaves a strong shared-LLM background (transformer / loss / tokens) that drags
  every pair toward ~0.2 and makes average linkage chain the whole corpus into
  one blob. Terms with df < 3 or df > 35% of sections are dropped.
* A unit vector is the L2-normalized sum of its section tf-idf vectors.
* Grouping is **complete linkage** (merge on the worst pair), which resists the
  chaining that average linkage suffers here. Wikis and satellite surveys are
  then assigned by nearest-survey rather than by linkage, because complete
  linkage strands a small satellite whose worst pair against a big group is low.

Commands
--------
    python viewer/tools/crosslink-cluster.py propose [--cut 0.20]
    python viewer/tools/crosslink-cluster.py validate [--scope-file .claude/crosslink-scope]

`validate` prints per-group cohesion and, crucially, the **inter-group edges the
grouping forgoes** — a high severed edge is the honest cost of a group boundary
and belongs in the scope file's header comment.

Pure stdlib. Deterministic: no randomness, no wall-clock.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

_spec = importlib.util.spec_from_file_location("crosslink", HERE / "crosslink.py")
cl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cl)

SKIP_DIRS = {"_scratch", "archive", "figures", "llr-figures", "method-search"}
SKIP_FILES = {"index.md", "references.md"}
MIN_DF = 3
MAX_DF_FRAC = 0.35


def unit_files() -> dict[str, list[Path]]:
    units: dict[str, list[Path]] = {}
    sdir = ROOT / "surveys"
    for d in sorted(p for p in sdir.iterdir() if p.is_dir()):
        if d.name in SKIP_DIRS:
            continue
        fs = [f for f in sorted(d.rglob("*.md"))
              if f.name not in SKIP_FILES and not f.name.startswith("_")
              and not any(part in SKIP_DIRS for part in f.relative_to(d).parts)]
        if fs:
            units[d.name] = fs
    for f in sorted(sdir.glob("*.md")):
        if f.name not in SKIP_FILES and not f.name.startswith("_"):
            units[f.stem] = [f]
    for f in sorted((ROOT / "wikis").glob("*.md")):
        units["wiki:" + f.stem] = [f]
    return units


def build_unit_vectors(units):
    unit_secs = {}
    for k, fs in units.items():
        secs = []
        for f in fs:
            got = cl.extract_file(str(f))
            if got:
                secs.extend(Counter(s["tokens"]) for s in got)
            else:                       # unnumbered doc: fall back to whole file
                secs.append(Counter(cl.tokenize(f.read_text(encoding="utf-8"))))
        unit_secs[k] = [s for s in secs if s]

    all_secs = [s for v in unit_secs.values() for s in v]
    n = len(all_secs)
    df = Counter()
    for s in all_secs:
        for t in s:
            df[t] += 1
    idf = {t: math.log((n + 1) / (d + 1)) + 1.0 for t, d in df.items()}
    hi = MAX_DF_FRAC * n

    def secvec(s):
        v = {t: (1 + math.log(c)) * idf[t] for t, c in s.items()
             if MIN_DF <= df[t] <= hi}
        norm = math.sqrt(sum(w * w for w in v.values())) or 1.0
        return {t: w / norm for t, w in v.items()}

    vecs = {}
    for k, secs in unit_secs.items():
        acc = Counter()
        for s in secs:
            for t, w in secvec(s).items():
                acc[t] += w
        norm = math.sqrt(sum(w * w for w in acc.values())) or 1.0
        vecs[k] = {t: w / norm for t, w in acc.items()}
    return vecs, n


def cosine(va, vb):
    if len(va) > len(vb):
        va, vb = vb, va
    return sum(w * vb.get(t, 0.0) for t, w in va.items())


def propose_cmd(args):
    units = unit_files()
    vecs, nsec = build_unit_vectors(units)
    names = sorted(vecs)
    surveys = [x for x in names if not x.startswith("wiki:")]
    wikis = [x for x in names if x.startswith("wiki:")]
    sim = {}

    def S(a, b):
        if a == b:
            return 1.0
        k = (a, b) if a < b else (b, a)
        if k not in sim:
            sim[k] = cosine(vecs[a], vecs[b])
        return sim[k]

    print(f"sections={nsec}  units={len(names)}  surveys={len(surveys)}  wikis={len(wikis)}\n")

    clusters = [[s] for s in surveys]
    while len(clusters) > 1:
        best, bi, bj = -1.0, None, None
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                d = min(S(a, b) for a in clusters[i] for b in clusters[j])
                if d > best:
                    best, bi, bj = d, i, j
        if best < args.cut:
            break
        clusters[bi] += clusters[bj]
        del clusters[bj]

    clusters.sort(key=len, reverse=True)
    print(f"=== proposed groups (complete linkage, cut {args.cut}) ===")
    for n, c in enumerate(clusters, 1):
        worst = min((S(a, b) for a in c for b in c if a < b), default=float("nan"))
        print(f"\n[group-{n}]   worst intra pair {worst:.3f}" if len(c) > 1
              else f"\n[group-{n}]   (single survey)")
        for s in sorted(c):
            print(f"  surveys/{s}")
        for w in sorted(wikis, key=lambda w: -max(S(w, s) for s in c)):
            owner = max(surveys, key=lambda s: S(w, s))
            if owner in c:
                print(f"  wikis/{w[5:]}.md            # -> {owner} {S(w, owner):.3f}")
    return 0


def validate_cmd(args):
    groups = cl.load_scope(args.scope_file)
    units = unit_files()
    vecs, _ = build_unit_vectors(units)

    def unit_of(p: str) -> str:
        p = p.replace("\\", "/")
        if p.startswith("wikis/"):
            return "wiki:" + Path(p).stem
        rest = p[len("surveys/"):]
        return rest[:-3] if rest.endswith(".md") else rest

    gu, missing = {}, []
    for g, paths in groups.items():
        us = []
        for p in paths:
            u = unit_of(p)
            (us if u in vecs else missing).append(u)
        gu[g] = us
    if missing:
        print(f"!! not in vector space: {missing}", file=sys.stderr)

    print(f"{'group':<20s} {'units':>5s} {'mean-intra':>11s} {'min-intra':>10s}  worst pair")
    print("-" * 84)
    for g, us in gu.items():
        pairs = [(a, b) for i, a in enumerate(us) for b in us[i + 1:]]
        if not pairs:
            print(f"{g:<20s} {len(us):5d}      (single unit — intra-survey links only)")
            continue
        vals = [cosine(vecs[a], vecs[b]) for a, b in pairs]
        mn = min(vals)
        a, b = pairs[vals.index(mn)]
        print(f"{g:<20s} {len(us):5d} {sum(vals)/len(vals):11.3f} {mn:10.3f}  {a[:26]} <> {b[:26]}")

    print("\nINTER-GROUP max edge — the links these groups deliberately forgo:")
    gnames = list(gu)
    worst = []
    for i, a in enumerate(gnames):
        for b in gnames[i + 1:]:
            cands = [(cosine(vecs[x], vecs[y]), x, y) for x in gu[a] for y in gu[b]]
            if not cands:
                continue
            sc, x, y = max(cands)
            worst.append((sc, a, b, x, y))
    for sc, a, b, x, y in sorted(worst, reverse=True):
        flag = "  <-- thin boundary" if sc >= 0.45 else ""
        print(f"  {sc:.3f}  {a} <> {b}   ({x} <> {y}){flag}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("propose", help="cluster surveys -> proposed groups")
    p.add_argument("--cut", type=float, default=0.20)
    p.set_defaults(func=propose_cmd)
    v = sub.add_parser("validate", help="cohesion + severed edges of the current scope")
    v.add_argument("--scope-file", default=str(ROOT / ".claude" / "crosslink-scope"))
    v.set_defaults(func=validate_cmd)
    args = ap.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
