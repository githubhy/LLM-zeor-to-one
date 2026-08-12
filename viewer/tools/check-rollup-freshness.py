#!/usr/bin/env python3
"""Rollup-freshness gate — catches the staleness the signoff gate structurally CANNOT.

`check-signoff-checklist.py` proves every quoted number equals the artifact it names. That is
value-vs-artifact. It says nothing about whether that artifact is still the CURRENT baseline, or
whether the page's *prose* (wave statuses, subset counts) still matches the program manifest. Both
holes were real, not hypothetical:

  * On 2026-07-16 the master rollup asserted `Wave 2 | planned` and `Wave 3 | planned` and "8 done
    subsets" while the manifest held both waves complete and 17 done subsets. Every gate was green.
  * The same page quoted the pre-W3.3 flat-CE margins (A = -0.48) long after W3.3 re-baselined the
    program onto the Wiener estimator (A = -2.23). The signoff gate PASSED, because `A_nms.json`
    genuinely still contains -0.48 — a superseded artifact cited with perfect accuracy.

A gate that checks numbers cannot catch citing the wrong artifact. This one checks the two things it
can: the page's asserted program status against the manifest (the scope oracle), and any citation of
an artifact that a `supersedes` rule marks as no longer the live baseline.

Checks:
  1. status-drift  — a `| <wave> | ... | <status> |` row whose status disagrees with the manifest.
  2. count-drift   — an asserted "<N> done subsets" that disagrees with the manifest's done count.
  3. superseded    — a ```signoff line citing an artifact matched by a `supersedes` rule, where a
                     live replacement exists (e.g. `X_nms.json` -> `X_nms_wiener.json`), unless the
                     page explicitly exempts that case.

The supersede rules live in the manifest under `rollup_freshness` so they are data, not code:

    "rollup_freshness": {
      "supersedes": [{"pattern": "_nms.json", "replacement": "_nms_wiener.json",
                      "reason": "W3.3 unified the program on the Wiener estimator (decision 2026-07-15-01)",
                      "exempt": ["SR_nms.json", "SRT_nms.json"]}]
    }

Usage:
    python viewer/tools/check-rollup-freshness.py ROLLUP.md [--manifest M.json] [--check]

Exit codes: 0 PASS, 1 FAIL (drift), 2 usage.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DEFAULT_MANIFEST = "artifacts/nr-pdsch-demod/program-manifest.json"
SIGNOFF_RE = re.compile(r"```signoff\s*\n(.*?)\n```", re.DOTALL)
CITE_RE = re.compile(r"<-\s*(?P<path>\S+\.json)\s*::")
# "| 3 | Margin quantification (...) | **complete** (3/3 families) |"  -> wave 3, status text
STATUS_ROW_RE = re.compile(r"^\|\s*(?P<wave>\d+)\s*\|[^|]*\|\s*(?P<status>[^|]+?)\s*\|\s*$", re.M)
COUNT_RE = re.compile(r"\*\*(?P<n>\d+)\s+done\s+subsets?\.?\*\*", re.I)


def _norm(s: str) -> str:
    return re.sub(r"[*_`]", "", s).strip().lower()


def check(page: Path, manifest: Path):
    text = page.read_text(encoding="utf-8")
    man = json.loads(manifest.read_text(encoding="utf-8"))
    problems: list[str] = []

    # --- 1. status drift -------------------------------------------------
    truth = {w["wave"]: w.get("status", "planned") for w in man.get("waves", [])}
    for m in STATUS_ROW_RE.finditer(text):
        wave = int(m["wave"])
        if wave not in truth:
            continue
        claimed, actual = _norm(m["status"]), truth[wave].lower()
        # the row may add detail ("complete (3/3 families)"); require it to START with the truth word
        if not claimed.startswith(actual):
            problems.append(
                f"status drift: page says wave {wave} is {claimed!r} but the manifest says "
                f"{actual!r} — the page is stale (or the manifest is wrong; reconcile, do not paper over)")

    # --- 2. done-subset count drift --------------------------------------
    n_done = sum(1 for w in man.get("waves", []) for s in w.get("subsets", [])
                 if s.get("status") == "done")
    for m in COUNT_RE.finditer(text):
        if int(m["n"]) != n_done:
            problems.append(
                f"count drift: page asserts {m['n']} done subsets but the manifest has {n_done}")

    # --- 3. superseded-artifact citation ---------------------------------
    rules = (man.get("rollup_freshness") or {}).get("supersedes") or []
    cited = {m["path"] for b in SIGNOFF_RE.findall(text) for m in CITE_RE.finditer(b)}
    root = manifest.parent.parent.parent if manifest.is_absolute() else Path.cwd()
    for path in sorted(cited):
        name = Path(path).name
        for rule in rules:
            pat, rep = rule.get("pattern"), rule.get("replacement")
            if not pat or not name.endswith(pat) or name in (rule.get("exempt") or []):
                continue
            live_name = name[: -len(pat)] + rep
            live = Path(path).with_name(live_name)
            if (Path.cwd() / live).is_file():
                problems.append(
                    f"superseded citation: {name} is cited but {live_name} exists and supersedes it "
                    f"({rule.get('reason', 'superseded')}). The signoff gate cannot catch this — it "
                    f"only proves the number matches the artifact, not that the artifact is live.")
    return problems


def main() -> int:
    argv = [a for a in sys.argv[1:] if a != "--check"]
    manifest = Path(DEFAULT_MANIFEST)
    if "--manifest" in argv:
        i = argv.index("--manifest")
        manifest = Path(argv[i + 1])
        del argv[i:i + 2]
    if len(argv) != 1:
        print("Usage: check-rollup-freshness.py ROLLUP.md [--manifest M.json] [--check]",
              file=sys.stderr)
        return 2
    page = Path(argv[0])
    for p in (page, manifest):
        if not p.is_file():
            print(f"ERROR: not a file: {p}", file=sys.stderr)
            return 2

    problems = check(page, manifest)
    if problems:
        for p in problems:
            print(f"  [-] {p}")
        print(f"rollup-freshness: FAIL ({len(problems)} drift(s)) -- {page.name}", file=sys.stderr)
        return 1
    print(f"rollup-freshness: PASS (status + counts match the manifest; no superseded citation) "
          f"-- {page.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
