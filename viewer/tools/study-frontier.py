#!/usr/bin/env python3
"""Study-frontier detector — rank documents by how little they have been interrogated.

Tier 1 of the `/study` session pattern (`.claude/commands/study.md`): the menu a study
session opens with must be COMPUTED, not chosen by feel, or it drifts toward whatever is
convenient to explain — the failure mode `decisions/2026-08-13-02` forbids.

The signal is Q&A folds. `survey-explainer-fold` fires only on a real question asked
while reading, so a `> **Note —**` blockquote is a recorded question. A document with many
sections and no folds has never been interrogated; that is the frontier.

    python viewer/tools/study-frontier.py                 # ranked menu, least-read first
    python viewer/tools/study-frontier.py --top 5
    python viewer/tools/study-frontier.py --json
    python viewer/tools/study-frontier.py --since HEAD~1  # pulse check: folds added

Exit codes: 0 normal; 1 for `--since` when zero folds were added (the session's guardrail
-- "a study session that produces zero folds did not happen"); 2 on a usage error.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Directories scanned for the fold metric. Studies under docs/ carry no folds by
# construction (the fold instrument is survey-scoped), so they are reported separately.
FOLD_ROOTS = ("surveys", "wikis")
STUDY_GLOB = "docs/*-study.md"

# surveys/attention-demo is a tooling fixture, not research content (same rationale as
# .claude/crosslink-keepout), so it is never a study target.
KEEPOUT = {"surveys/attention-demo"}

HEADING_RE = re.compile(r"^#{2,6}\s+\S")
# A fold is a blockquote line carrying a "**Note —**" lead. Anchors and para markers may
# sit between the ">" and the bold run, so this is deliberately permissive.
FOLD_RE = re.compile(r"^\s*>.*\*\*Note\s*[—–-]")
REFS_RE = re.compile(r"^references\.md$", re.I)


def _kept_out(rel: str) -> bool:
    return any(rel == k or rel.startswith(k + "/") for k in KEEPOUT)


def scan_file(path: pathlib.Path) -> tuple[int, int]:
    """Return (n_sections, n_folds) for one markdown file."""
    sections = folds = 0
    in_fence = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if HEADING_RE.match(line):
            sections += 1
        if FOLD_RE.match(line):
            folds += 1
    return sections, folds


def collect(root: pathlib.Path = ROOT) -> list[dict]:
    """Per-file interrogation stats over the fold-bearing roots, least-read first."""
    rows = []
    for top in FOLD_ROOTS:
        base = root / top
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            rel = path.relative_to(root).as_posix()
            if _kept_out(rel) or "_scratch" in path.parts:
                continue
            if REFS_RE.match(path.name):
                continue
            sections, folds = scan_file(path)
            if sections == 0:
                continue  # index/front-matter stubs carry nothing to interrogate
            rows.append({
                "path": rel,
                "sections": sections,
                "folds": folds,
                "density": round(folds / sections, 4),
            })
    # Least-interrogated first; among equals, the bigger document has more at stake.
    rows.sort(key=lambda r: (r["density"], -r["sections"]))
    return rows


def collect_studies(root: pathlib.Path = ROOT) -> list[dict]:
    """docs/*-study.md — the L4 surface, which has no fold instrument of its own."""
    out = []
    for path in sorted(root.glob(STUDY_GLOB)):
        sections, folds = scan_file(path)
        out.append({"path": path.relative_to(root).as_posix(),
                    "sections": sections, "folds": folds})
    return out


def folds_added_since(ref: str, root: pathlib.Path = ROOT) -> tuple[int, list[str]]:
    """Count fold lines ADDED since `ref` (the session pulse check)."""
    try:
        diff = subprocess.run(
            ["git", "-C", str(root), "diff", "-U0", ref, "--", *FOLD_ROOTS],
            capture_output=True, check=True,
        ).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"[study-frontier] cannot diff against {ref!r}: {exc}", file=sys.stderr)
        return -1, []
    added, current = 0, "?"
    files = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            continue
        if line.startswith("+") and not line.startswith("+++"):
            if FOLD_RE.match(line[1:]):
                added += 1
                files.append(current)
    return added, sorted(set(files))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Rank documents by how little they have been interrogated.")
    ap.add_argument("--top", type=int, default=8, help="menu size (default 8)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--since", metavar="REF",
                    help="pulse check: count folds added since REF; exit 1 if none")
    args = ap.parse_args(argv)

    if args.since:
        added, files = folds_added_since(args.since)
        if added < 0:
            return 2
        if args.json:
            print(json.dumps({"since": args.since, "folds_added": added, "files": files}, indent=1))
        elif added == 0:
            print(f"[study-frontier] 0 folds added since {args.since} — "
                  "a study session that produces zero folds did not happen "
                  "(decisions/2026-08-13-02).")
        else:
            print(f"[study-frontier] {added} fold(s) added since {args.since}:")
            for f in files:
                print(f"    {f}")
        return 0 if added > 0 else 1

    rows = collect()
    studies = collect_studies()
    if args.json:
        print(json.dumps({"frontier": rows[:args.top], "studies": studies}, indent=1))
        return 0

    if not rows:
        print("[study-frontier] no fold-bearing documents found — nothing to rank.", file=sys.stderr)
        return 2

    never = [r for r in rows if r["folds"] == 0]
    print(f"[study-frontier] {len(rows)} document(s); {len(never)} never interrogated.\n")
    print(f"  {'folds':>5} {'secs':>5} {'dens':>6}  document")
    print(f"  {'-'*5} {'-'*5} {'-'*6}  {'-'*52}")
    for r in rows[:args.top]:
        print(f"  {r['folds']:>5} {r['sections']:>5} {r['density']:>6.3f}  {r['path']}")
    if len(rows) > args.top:
        print(f"\n  ... {len(rows) - args.top} more (raise --top to see them)")

    if studies:
        unread = [s for s in studies if s["folds"] == 0]
        print(f"\n  L4 surface — {len(studies)} study report(s), {len(unread)} with no folds.")
        print("  (docs/ has no fold instrument; interrogate these by retro-audit instead:")
        print("   what did it find, what would falsify it, does it survive a population split?)")
        for s in studies[:args.top]:
            print(f"    {s['path']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
