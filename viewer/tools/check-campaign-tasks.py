#!/usr/bin/env python3
"""Campaign TASK-MANIFEST gate — enforces the plan, so the plan does not depend on being remembered.

Renamed from check-campaign.py at the 2026-08-19 fork merge: two different gates had that
name on the two branches. The other one (still check-campaign.py) validates campaign/v1
DESCRIPTORS listed in .claude/campaigns; this one validates the TASK MANIFESTS under
campaigns/<slug>/. Disjoint populations, disjoint schemas, both live — see .githooks/pre-push.

Scans `campaigns/*/campaign.json` (directory existence IS the registration — no
opt-in registry, because registries drift: bugs/2026-07-09-13, where 8 of 14
declared wikis were structurally invisible to their gate).

Checks:
  1. MANIFEST      — schema, tiers resolve, deps resolve, no cycles.
  2. DEP ORDER     — a task marked `done` whose dependency is not done.
  3. TIER-FROM-OUTPUT — a task that WRITES an attribution IS tier A, whatever it
                    claims. Rigor cannot be downgraded by relabelling.
  4. GATE RECORDS  — a `done` task must carry tasks/<TID>/gates.json covering
                    every gate its tier requires.
  5. PRE-REGISTRATION — tier-A tasks: the pre-registration commit must PRECEDE the
                    first result commit (viewer/tools/lib/prereg.py). Same-commit
                    fails. Silent post-hoc edits to the thresholds block fail.
  6. A5 CLAIMED<=MEASURED — the configurations an attribution is CLAIMED for may
                    not exceed the ones it was MEASURED in. This is the exact
                    error of bugs/2026-07-04-21 (high): a UMa-only re-run
                    generalized, and provably false for UMi.
  7. MEASURE-FIRST — no phase-3/4 gate record may be committed before the
                    measure-first task's. Skipping it is impossible, not merely
                    discouraged.

Severity: campaign.json `gates.severity` (off|warn|error), overridable with
--severity. Only `error` blocks.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import prereg  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGNS = ROOT / "campaigns"
ATTR_RE = re.compile(r"^(T[\w.]+?)-")  # attributions/<TID>-<subject>.md


def err(findings, code, where, msg):
    findings.append(("error", code, where, msg))


def warn(findings, code, where, msg):
    findings.append(("warn", code, where, msg))


def check_campaign(cdir: Path, findings: list):
    man_path = cdir / "campaign.json"
    try:
        man = json.loads(man_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        err(findings, "CM-PARSE", str(man_path), f"unreadable manifest: {e}")
        return "error"

    sev = (man.get("gates") or {}).get("severity", "warn")
    slug = man.get("slug", cdir.name)
    tiers = man.get("tiers") or {}
    gate_defs = man.get("gate_defs") or {}
    tasks = {t["id"]: t for t in man.get("tasks", [])}

    if not tasks:
        err(findings, "CM-NOTASKS", slug, "manifest declares no tasks")
        return sev

    # 1 — manifest sanity
    for tid, t in tasks.items():
        if t.get("tier") not in tiers:
            err(findings, "CM-TIER", f"{slug}:{tid}", f"unknown tier {t.get('tier')!r}")
        # `obsolete` is a first-class outcome, not a synonym for done. A task whose PREMISE
        # was refuted must not be laundered into "done" — that turns a stale plan into a
        # false record. (T2.1 "digitize the reference CDFs" was scoped from a todo whose
        # premise was false: reference.py already returns the numeric CDFs. Nothing was
        # done; the task evaporated.) An obsolete task needs a REASON, not gate records.
        if t.get("status") not in ("todo", "in-progress", "done", "blocked", "obsolete"):
            err(findings, "CM-STATUS", f"{slug}:{tid}", f"bad status {t.get('status')!r}")
        if t.get("status") == "obsolete" and not t.get("obsoleted_by"):
            err(findings, "CM-NOREASON", f"{slug}:{tid}",
                "status=obsolete requires an `obsoleted_by` field saying WHAT refuted it — "
                "an unexplained obsolete is indistinguishable from a quietly dropped task")
        for d in t.get("deps", []):
            if d not in tasks:
                err(findings, "CM-DEP", f"{slug}:{tid}", f"dependency {d} does not exist")

    # 2 — dep order. An OBSOLETE dependency counts as satisfied: it will never be "done",
    # and a task that proceeded past it did so correctly, because the dep evaporated. Only a
    # dep that is still pending (todo / in-progress / blocked) can invalidate a done task.
    SATISFIED = ("done", "obsolete")
    for tid, t in tasks.items():
        if t.get("status") == "done":
            for d in t.get("deps", []):
                if d in tasks and tasks[d].get("status") not in SATISFIED:
                    err(findings, "CM-DEPORDER", f"{slug}:{tid}",
                        f"marked done but dependency {d} is {tasks[d].get('status')}")

    # 3 — tier derived from OUTPUT, not declaration
    attr_dir = cdir / "ledger" / "attributions"
    if attr_dir.is_dir():
        for f in sorted(attr_dir.glob("*.md")):
            m = ATTR_RE.match(f.name)
            if not m:
                warn(findings, "CM-ATTRNAME", str(f),
                     "attribution filename must start with <TID>- so its task is resolvable")
                continue
            tid = m.group(1)
            if tid not in tasks:
                err(findings, "CM-ATTRTASK", str(f), f"attribution references unknown task {tid}")
            elif tasks[tid].get("tier") != "A":
                err(findings, "CM-TIERDRIFT", f"{slug}:{tid}",
                    f"task WRITES an attribution ({f.name}) but is declared tier "
                    f"{tasks[tid].get('tier')!r}. A task that attributes a residual IS tier A.")

    # 4/5/6 — per-task gate records
    for tid, t in sorted(tasks.items()):
        tdir = cdir / "tasks" / tid
        gpath = tdir / "gates.json"
        required = (tiers.get(t.get("tier"), {}) or {}).get("requires", [])

        if t.get("status") != "done":
            continue

        if not gpath.exists():
            err(findings, "CM-NOGATES", f"{slug}:{tid}",
                f"marked done but has no tasks/{tid}/gates.json")
            continue

        try:
            g = json.loads(gpath.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            err(findings, "CM-GATEPARSE", str(gpath), f"unreadable: {e}")
            continue

        passed = {k for k, v in (g.get("gates") or {}).items() if v.get("passed")}
        for req in required:
            if req not in passed:
                err(findings, "CM-GATEMISS", f"{slug}:{tid}",
                    f"tier {t['tier']} requires gate {req!r} "
                    f"({gate_defs.get(req, 'no definition')}) — not recorded as passed")

        # 5 — pre-registration (tier A)
        if "pre-registration" in required:
            ppath = tdir / "pre-registration.md"
            if not ppath.exists():
                err(findings, "CM-NOPREREG", f"{slug}:{tid}", "tier-A task has no pre-registration.md")
            else:
                p = prereg.parse(ppath)
                for f in prereg.validate_content(p):
                    findings.append((f.level, f.code, f"{slug}:{tid}", f.message))

                results = [q for q in sorted(tdir.glob("*")) if q.name not in
                           ("pre-registration.md", "gates.json")]
                for f in prereg.verify(ROOT, ppath, results):
                    findings.append((f.level, f.code, f"{slug}:{tid}", f.message))

                # 6 — A5: claimed set may not exceed measured set
                claimed = set(p.frontmatter.get("claimed_for") or [])
                measured = set(g.get("measured") or [])
                if claimed and not measured:
                    err(findings, "CM-NOMEASURED", f"{slug}:{tid}",
                        f"claims {sorted(claimed)} but gates.json records no `measured` set")
                elif claimed - measured:
                    err(findings, "CM-A5", f"{slug}:{tid}",
                        f"attribution CLAIMED for {sorted(claimed)} but only MEASURED in "
                        f"{sorted(measured)}. Unmeasured: {sorted(claimed - measured)}. "
                        f"This is bugs/2026-07-04-21 exactly.")

    # 7 — MEASURE-FIRST hard dependency
    mf = man.get("measure_first_gate") or {}
    mf_task = mf.get("task")
    blocked = set(mf.get("blocks_phases") or [])
    if mf_task and blocked:
        mf_gates = cdir / "tasks" / mf_task / "gates.json"
        mf_commit = prereg.add_commit(ROOT, mf_gates) if mf_gates.exists() else None
        for tid, t in sorted(tasks.items()):
            if t.get("phase") not in blocked:
                continue
            gpath = cdir / "tasks" / tid / "gates.json"
            if not gpath.exists():
                continue
            g_commit = prereg.add_commit(ROOT, gpath)
            if g_commit is None:
                continue
            if mf_commit is None:
                err(findings, "CM-MEASUREFIRST", f"{slug}:{tid}",
                    f"phase-{t['phase']} work is committed but the MEASURE-FIRST gate "
                    f"({mf_task}) has not run. Its residual may already be closed by the "
                    f"blocking fix.")
            # ANCESTRY, not timestamps — same flaw the prereg unit tests exposed: a
            # commit's %ct is second-granularity and forgeable, so two scripted commits
            # in one second made this silently no-op, non-deterministically.
            elif not prereg.is_ancestor(ROOT, mf_commit[0], g_commit[0]) and (
                    prereg.is_boundary(ROOT, mf_commit[0])
                    or prereg.is_boundary(ROOT, g_commit[0])):
                # ASYMMETRIC, deliberately. `is_ancestor(A, B) == True` is sound even when A
                # is a boundary -- git FOUND a path, and the real add-commit of A is A or
                # earlier, so B descends from it either way. Only a FALSE answer is unsound:
                # the path may simply have been pruned away. So refuse here and nowhere else,
                # which keeps every sound verdict this clone can still give.
                findings.append(("refuse", "CM-NOHISTORY", f"{slug}:{tid}", prereg.NO_HISTORY))
            elif not prereg.is_ancestor(ROOT, mf_commit[0], g_commit[0]):
                # The violation is PERMANENT: add_commit() keys on the commit that ADDED
                # gates.json, so re-touching the file cannot launder it. Good — but a gate
                # that stays red forever on a known, remediated violation stops being a
                # signal for NEW ones, and a permanently-red gate is a gate people learn to
                # ignore. So there is exactly one way down, and it is not silence:
                #
                #   the task's gates.json must carry a `measure_first_remediation` block
                #   with `revalidated: true` and EVIDENCE that the finding was re-measured
                #   against the post-gate ledger.
                #
                # It then reports as a WARNING, forever, naming the evidence. It never
                # disappears, it never blocks, and a task that simply skipped the gate with
                # no remediation still ERRORS. The audit trail is the point; the red light
                # is not.
                rem = (json.loads(gpath.read_text(encoding="utf-8"))
                       .get("measure_first_remediation") or {})
                if rem.get("revalidated") and rem.get("evidence"):
                    warn(findings, "CM-MEASUREFIRST-REMEDIATED", f"{slug}:{tid}",
                         f"was committed BEFORE the MEASURE-FIRST gate ({mf_task}) — a real "
                         f"violation, permanently on the record. Re-validated against the "
                         f"post-gate ledger: {rem['evidence']}")
                else:
                    err(findings, "CM-MEASUREFIRST", f"{slug}:{tid}",
                        f"its gate record does not DESCEND from the MEASURE-FIRST gate "
                        f"({mf_task}) — so it was measured against a baseline we knew was "
                        f"about to change. If it has since been re-measured against the "
                        f"post-gate ledger, record that in gates.json under "
                        f"`measure_first_remediation` {{revalidated, evidence}} — it will "
                        f"then report as a permanent WARNING, not vanish.")

    return sev


def main() -> int:
    ap = argparse.ArgumentParser(description="Campaign gate.")
    ap.add_argument("--campaign", help="slug or directory name (default: all)")
    ap.add_argument("--severity", choices=("off", "warn", "error"))
    a = ap.parse_args()

    if not CAMPAIGNS.is_dir():
        print("[campaign] no campaigns/ directory — nothing to check")
        return 0

    dirs = [d for d in sorted(CAMPAIGNS.iterdir()) if (d / "campaign.json").exists()]
    if a.campaign:
        dirs = [d for d in dirs if a.campaign in (d.name, json.loads(
            (d / "campaign.json").read_text()).get("slug"))]
    if not dirs:
        print("[campaign] no campaign manifests found")
        return 0

    findings: list = []
    sev_max = "off"
    for d in dirs:
        s = check_campaign(d, findings)
        sev = a.severity or s
        if sev == "error" or (sev == "warn" and sev_max != "error"):
            sev_max = sev

    errors = [f for f in findings if f[0] == "error"]
    warns = [f for f in findings if f[0] == "warn"]
    refusals = [f for f in findings if f[0] == "refuse"]

    for level, code, where, msg in findings:
        if level == "info":
            continue
        print(f"[campaign] {level.upper():6s} {code:16s} {where}\n            {msg}")

    n = len(dirs)
    # REFUSE is not FAIL and it is emphatically not PASS. The ancestry checks were skipped,
    # so "all gates satisfied" would be a claim about checks that never ran.
    if refusals:
        print(f"[campaign] REFUSE — {n} campaign(s) inspected; the content gates ran, the "
              f"ORDERING gates did not (no git history). No pre-registration verdict.")
        return 2
    if not errors and not warns:
        print(f"[campaign] OK — {n} campaign(s), all gates satisfied")
        return 0

    print(f"[campaign] {len(errors)} error(s), {len(warns)} warning(s) across {n} campaign(s)")
    if errors and sev_max == "error":
        return 1
    if errors:
        print("[campaign] advisory (severity=warn) — not blocking")
    return 0


if __name__ == "__main__":
    sys.exit(main())
