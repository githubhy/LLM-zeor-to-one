#!/usr/bin/env python3
"""Study-frontier detector — rank documents by how little they have been interrogated.

Tier 1 of the `/study` session pattern (`.claude/commands/study.md`): the menu a study
session opens with must be COMPUTED, not chosen by feel, or it drifts toward whatever is
convenient to explain — the failure mode `decisions/2026-08-13-02` forbids.

The signal is Q&A folds. `survey-explainer-fold` fires only on a real question asked
while reading, so a `> **Note —**` blockquote is a recorded question. A document with many
sections and no folds has never been interrogated; that is the frontier.

Two refinements borrowed from the `teach` skill (decision 2026-08-14-01):

* **The menu is gated to the zone of proximal development.** Ranking by interrogation
  alone put mechanistic-interpretability-at-scale second on a menu for a reader whose
  attention derivation is still open. `.claude/study-prereqs` maps documents to the rung
  a reader must already hold; a document more than one rung above the reader is held back
  (reported, never silently dropped).
* **`--recall` is retrieval practice.** Fluency (answering with the corpus open) feels
  like mastery and is not storage strength. Re-answering an old fold from memory, oldest
  first, is spaced retrieval using the artifact the session already produces.

    python viewer/tools/study-frontier.py                 # ranked menu, least-read first
    python viewer/tools/study-frontier.py --top 5
    python viewer/tools/study-frontier.py --all           # ignore the prerequisite gate
    python viewer/tools/study-frontier.py --recall 3      # retrieval practice, oldest first
    python viewer/tools/study-frontier.py --json
    python viewer/tools/study-frontier.py --since HEAD~1  # pulse check: folds added

Exit codes: 0 normal; 1 for `--since` when zero folds were added (the session's guardrail
-- "a study session that produces zero folds did not happen"); 2 on a usage error.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import pathlib
import re
import subprocess
import sys
import time

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
LEAD_RE = re.compile(r"\*\*Note\s*[—–-]\s*(.*?)\*\*")
REFS_RE = re.compile(r"^references\.md$", re.I)

PREREQ_FILE = ".claude/study-prereqs"
READER_RUNG_FILE = ".claude/study-reader-rung"
DAY = 86400


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


# --- prerequisite gate (zone of proximal development) -----------------------

def load_prereqs(root: pathlib.Path = ROOT) -> list[tuple[int, str]]:
    """Parse `.claude/study-prereqs` into ordered (prereq_rung, glob) pairs."""
    path = root / PREREQ_FILE
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        rung, _, glob = line.partition(" ")
        if not glob.strip() or not rung.lstrip("Ll").isdigit():
            print(f"[study-frontier] ignoring malformed prereq line: {line!r}", file=sys.stderr)
            continue
        out.append((int(rung.lstrip("Ll")), glob.strip()))
    return out


def prereq_for(rel: str, prereqs: list[tuple[int, str]]) -> int | None:
    """First matching glob wins; None when unmapped (never a reason to hide)."""
    for rung, glob in prereqs:
        if fnmatch.fnmatch(rel, glob):
            return rung
    return None


def load_reader_rung(root: pathlib.Path = ROOT) -> int | None:
    """Read `.claude/study-reader-rung` (e.g. "L1"). None disables the gate."""
    path = root / READER_RUNG_FILE
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8").strip().lstrip("Ll")
    return int(raw) if raw.isdigit() else None


def apply_gate(rows: list[dict], reader_rung: int | None) -> tuple[list[dict], list[dict]]:
    """Split rows into (in reach, held back). A document is in reach when its
    prerequisite is at most one rung above the reader — that "+1" is the zone of
    proximal development. Unmapped documents and an unknown reader rung fail OPEN."""
    if reader_rung is None:
        return list(rows), []
    ceiling = reader_rung + 1
    reach = [r for r in rows if r.get("prereq") is None or r["prereq"] <= ceiling]
    held = [r for r in rows if r.get("prereq") is not None and r["prereq"] > ceiling]
    return reach, held


# --- recall queue (retrieval practice) --------------------------------------

def collect_folds(root: pathlib.Path = ROOT) -> list[dict]:
    """Every fold in the corpus, with its line number and the question it records."""
    out = []
    for top in FOLD_ROOTS:
        base = root / top
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            rel = path.relative_to(root).as_posix()
            if _kept_out(rel) or "_scratch" in path.parts:
                continue
            in_fence = False
            for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence or not FOLD_RE.match(line):
                    continue
                m = LEAD_RE.search(line)
                out.append({"path": rel, "line": n,
                            "lead": m.group(1).strip() if m else "(unlabelled fold)"})
    return out


def parse_blame_porcelain(text: str) -> dict[int, int]:
    """Map final-file line number -> author epoch from `git blame --line-porcelain`."""
    times: dict[int, int] = {}
    final_line = None
    for line in text.splitlines():
        parts = line.split(" ")
        if len(parts) >= 3 and len(parts[0]) == 40 and all(c in "0123456789abcdef" for c in parts[0]):
            final_line = int(parts[2])
        elif line.startswith("author-time ") and final_line is not None:
            times[final_line] = int(line.split(" ", 1)[1])
    return times


def blame_times(rel: str, root: pathlib.Path = ROOT) -> dict[int, int]:
    """Author epoch per line, or {} when the file is untracked / git is unavailable."""
    try:
        out = subprocess.run(["git", "-C", str(root), "blame", "--line-porcelain", "--", rel],
                             capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return {}
    return parse_blame_porcelain(out.stdout.decode("utf-8", "replace"))


def rank_recall(folds: list[dict], now: float | None = None) -> list[dict]:
    """Oldest fold first — the longest interval since it was last touched is the one
    most due for retrieval practice. Folds with no commit yet are not due at all."""
    now = time.time() if now is None else now
    dated = [f for f in folds if f.get("epoch")]
    dated.sort(key=lambda f: f["epoch"])
    for f in dated:
        f["age_days"] = int((now - f["epoch"]) // DAY)
    return dated


def recall_queue(root: pathlib.Path = ROOT, now: float | None = None) -> list[dict]:
    folds = collect_folds(root)
    by_file: dict[str, dict[int, int]] = {}
    for f in folds:
        if f["path"] not in by_file:
            by_file[f["path"]] = blame_times(f["path"], root)
        f["epoch"] = by_file[f["path"]].get(f["line"])
    return rank_recall(folds, now=now)


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
    ap.add_argument("--recall", type=int, nargs="?", const=1, metavar="N",
                    help="retrieval practice: the N oldest folds, to re-answer from memory")
    ap.add_argument("--all", action="store_true",
                    help="ignore the prerequisite gate and show every document")
    ap.add_argument("--reader-rung", metavar="Ln",
                    help="override .claude/study-reader-rung for this run")
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

    if args.recall is not None:
        queue = recall_queue()[:args.recall]
        if args.json:
            print(json.dumps({"recall": queue}, indent=1))
            return 0
        if not queue:
            print("[study-frontier] no committed folds yet — nothing to recall.")
            return 0
        print("[study-frontier] retrieval practice — answer from memory BEFORE reopening the file.")
        print("  (fluency with the corpus open is not storage strength; this is the gap "
              "docs/reader-frontier-2026-08-13.md measured.)\n")
        for f in queue:
            print(f"  {f['age_days']:>4}d  {f['lead']}")
            print(f"        {f['path']}:{f['line']}")
        return 0

    rows = collect()
    studies = collect_studies()

    prereqs = load_prereqs()
    for r in rows:
        r["prereq"] = prereq_for(r["path"], prereqs)
    if args.reader_rung:
        reader = int(args.reader_rung.lstrip("Ll")) if args.reader_rung.lstrip("Ll").isdigit() else None
    else:
        reader = load_reader_rung()
    if args.all:
        reader = None
    rows, held = apply_gate(rows, reader)

    if args.json:
        print(json.dumps({"frontier": rows[:args.top], "held_back": held,
                          "reader_rung": reader, "studies": studies}, indent=1))
        return 0

    if not rows:
        print("[study-frontier] no fold-bearing documents found — nothing to rank.", file=sys.stderr)
        return 2

    never = [r for r in rows if r["folds"] == 0]
    gate = f", reader rung L{reader}" if reader is not None else ", gate off"
    print(f"[study-frontier] {len(rows)} document(s); {len(never)} never interrogated{gate}.\n")
    print(f"  {'folds':>5} {'secs':>5} {'dens':>6} {'pre':>4}  document")
    print(f"  {'-'*5} {'-'*5} {'-'*6} {'-'*4}  {'-'*52}")
    for r in rows[:args.top]:
        pre = "-" if r["prereq"] is None else f"L{r['prereq']}"
        print(f"  {r['folds']:>5} {r['sections']:>5} {r['density']:>6.3f} {pre:>4}  {r['path']}")
    if len(rows) > args.top:
        print(f"\n  ... {len(rows) - args.top} more (raise --top to see them)")
    if held:
        print(f"\n  {len(held)} document(s) held back — prerequisite more than one rung "
              f"above L{reader} (--all to see them):")
        for r in held[:5]:
            print(f"    L{r['prereq']}  {r['path']}")

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
