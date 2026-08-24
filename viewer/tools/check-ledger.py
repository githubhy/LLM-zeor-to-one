#!/usr/bin/env python3
"""Calibration-ledger gate — the ledger may not drift into fiction.

Checks, per campaign:
  1. FRESH      — the ledger matches what build-ledger.py would produce from the
                  committed artifacts. A stale ledger is a lie with a timestamp.
  2. ENVELOPE   — every row carries the inter-company envelope. Comparing to the
                  Mean alone lets you "root-cause" a residual that sits inside the
                  18-21 company spread and was never a defect.
  3. BASIS      — every row states what is averaged, over what population, with
                  what normalization. A disagreement that dissolves under basis
                  reconciliation was never a model finding.
  4. CI         — every measured value carries an uncertainty
                  (.claude/rules/sim-report-completeness.md: CI on every result).
  5. TRACEABLE  — sim.artifact exists on disk.
  6. ATTRIBUTIONS — each ledger/attributions/*.md resolves to a real row, states a
                  bucket from the four, and quantifies the closure.

Severity from the campaign's gates.severity (off|warn|error); --severity overrides.
Only `error` blocks. Rows are EXPECTED to fail BASIS/CI on day one — that visible
gap is the point, and it closes with T2.4/T2.5.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGNS = ROOT / "campaigns"
BUCKETS = {"sim_bug", "convention_or_basis", "model_scope_gap", "genuine_model_error"}
STATUSES = {"OPEN", "LEAD", "ATTRIBUTED", "CLOSED", "SCOPED-OUT"}
CLOSURE_RE = re.compile(r"^\s*closure:", re.M | re.I)
BUCKET_RE = re.compile(r"^\s*bucket:\s*(\S+)", re.M | re.I)
ROWREF_RE = re.compile(r"^\s*row:\s*(\S+)", re.M | re.I)


def check(cdir: Path, findings: list) -> str:
    man = json.loads((cdir / "campaign.json").read_text(encoding="utf-8"))
    sev = (man.get("gates") or {}).get("severity", "warn")
    slug = man.get("slug", cdir.name)
    lpath = cdir / "ledger/measured.json"

    # The ledger SCHEMA and this CHECKER are universal; the BUILDER cannot be —
    # it reads domain artifacts. So each campaign declares its own. (Caught by the
    # upstream second-campaign fit test: the gate was telling one campaign to run
    # a sibling campaign's builder.)
    builder = man.get("ledger_builder")

    if builder is None:
        if lpath.exists():
            findings.append(("warn", "LG-NOBUILDER", slug,
                             "a ledger exists but campaign.json declares no `ledger_builder` — "
                             "it cannot be checked for staleness, so it may be hand-edited fiction"))
        else:
            findings.append(("info", "LG-NOLEDGER", slug,
                             "campaign declares no ledger_builder and has no ledger — skipped"))
            return sev
    elif not lpath.exists():
        findings.append(("error", "LG-MISSING", slug,
                         f"no ledger/measured.json — run `python {builder}`"))
        return sev

    # 1 — freshness (only possible when the campaign declares a builder)
    if builder:
        r = subprocess.run(
            [sys.executable, str(ROOT / builder), "--campaign", cdir.name, "--check"],
            capture_output=True, text=True, cwd=ROOT, check=False,
        )
        # Exit 2 is RESERVED by build-ledger.py for "stale". Any OTHER nonzero exit means the
        # builder could not run at all (missing dependency, import error, unreadable artifact) —
        # a different defect with a different fix. Reporting those as LG-STALE sent the reader to
        # regenerate a ledger that was already byte-identical, hiding a missing `openpyxl` behind
        # a bogus staleness claim on every fresh clone (bugs/2026-08-09-01).
        if r.returncode == 2:
            findings.append(("error", "LG-STALE", slug,
                             f"ledger is STALE vs the artifacts — regenerate with `python {builder}`"))
        elif r.returncode != 0:
            tail = (r.stderr or r.stdout or "").strip().splitlines()
            why = tail[-1] if tail else f"exit {r.returncode}"
            findings.append(("error", "LG-BUILDER-FAILED", slug,
                             f"`python {builder} --check` could not run (exit {r.returncode}) — "
                             f"the ledger's freshness is UNKNOWN, not stale: {why}"))

    led = json.loads(lpath.read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in led.get("rows", [])}
    if not rows:
        findings.append(("error", "LG-EMPTY", slug, "ledger has no rows"))
        return sev

    for rid, row in rows.items():
        where = f"{slug}:{rid}"
        ref = row.get("reference") or {}
        sim = row.get("sim") or {}

        if not ref.get("envelope"):
            findings.append(("error", "LG-ENVELOPE", where,
                             "no inter-company envelope — a residual inside the spread is not a defect, "
                             "and you cannot tell without it"))
        if ref.get("basis") in (None, "", "TBD"):
            findings.append(("error", "LG-BASIS", where,
                             "reference.basis is null — state what is averaged, over what population, "
                             "with what normalization, BEFORE comparing (T2.4)"))
        if sim.get("ci95") is None:
            findings.append(("error", "LG-CI", where,
                             "sim.ci95 is null — sim-report-completeness requires CI on every result (T2.5)"))
        art = sim.get("artifact")
        if art and not (ROOT / art).exists():
            findings.append(("error", "LG-ARTIFACT", where, f"sim.artifact not on disk: {art}"))
        if row.get("status") not in STATUSES:
            findings.append(("error", "LG-STATUS", where, f"bad status {row.get('status')!r}"))

    # 6 — attributions
    adir = cdir / "ledger/attributions"
    if adir.is_dir():
        for f in sorted(adir.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            where = str(f.relative_to(ROOT))
            m = ROWREF_RE.search(text)
            if not m:
                findings.append(("error", "LG-ATTR-ROW", where, "no `row:` field naming the ledger row"))
            elif m.group(1) not in rows:
                findings.append(("error", "LG-ATTR-ROW", where,
                                 f"references unknown ledger row {m.group(1)!r}"))
            b = BUCKET_RE.search(text)
            if not b:
                findings.append(("error", "LG-ATTR-BUCKET", where,
                                 f"no `bucket:` — must be one of {sorted(BUCKETS)}"))
            elif b.group(1) not in BUCKETS:
                findings.append(("error", "LG-ATTR-BUCKET", where,
                                 f"bucket {b.group(1)!r} not one of {sorted(BUCKETS)}"))
            if not CLOSURE_RE.search(text):
                findings.append(("error", "LG-ATTR-CLOSURE", where,
                                 "no `closure:` — an attribution must state how much of the gap the "
                                 "cause closes at the representative operating point, and what remains"))
    return sev


def main() -> int:
    ap = argparse.ArgumentParser(description="Calibration-ledger gate.")
    ap.add_argument("--campaign")
    ap.add_argument("--severity", choices=("off", "warn", "error"))
    ap.add_argument("--root", help=argparse.SUPPRESS)   # test-only: scan a synthetic tree
    a = ap.parse_args()

    global ROOT, CAMPAIGNS                              # noqa: PLW0603
    if a.root:
        ROOT = Path(a.root).resolve()
        CAMPAIGNS = ROOT / "campaigns"

    if not CAMPAIGNS.is_dir():
        print("[ledger-gate] no campaigns/ — nothing to check")
        return 0

    dirs = [d for d in sorted(CAMPAIGNS.iterdir()) if (d / "campaign.json").exists()]
    if a.campaign:
        dirs = [d for d in dirs if a.campaign in (d.name,)]

    findings: list = []
    sev_max = "off"
    for d in dirs:
        s = a.severity or check(d, findings)
        if s == "error" or (s == "warn" and sev_max != "error"):
            sev_max = s

    if not findings:
        print(f"[ledger-gate] OK — {len(dirs)} campaign(s)")
        return 0

    by_code: dict = {}
    for level, code, where, msg in findings:
        by_code.setdefault(code, []).append((where, msg))
    for code, items in sorted(by_code.items()):
        print(f"[ledger-gate] {code}: {len(items)} row(s)")
        for where, msg in items[:3]:
            print(f"                {where} — {msg}")
        if len(items) > 3:
            print(f"                … and {len(items) - 3} more")

    errs = sum(1 for f in findings if f[0] == "error")
    print(f"[ledger-gate] {errs} error(s)")
    if errs and sev_max == "error":
        return 1
    if errs:
        print("[ledger-gate] advisory (severity=warn) — not blocking")
    return 0


if __name__ == "__main__":
    sys.exit(main())
