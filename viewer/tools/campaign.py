#!/usr/bin/env python3
"""The campaign lifecycle state machine and owner-decision queue.

Phase 5 of `plans/2026-08-15-campaign-lifecycle-harness.md`. Extends rather than
replaces `check-plan-progress.py`: that gate owns wave/subset anti-drift and keeps
running unchanged; this owns the stage lifecycle, the population/basis layer, and
the decision queue the manifest never had.

THE GOVERNING PROPERTY: every stage predicate is RE-DERIVED from the descriptor,
never read from a status string. A `status: done` is an assertion; the predicate is
the evidence. This is the discipline check-plan-progress already applies to subsets
(it re-runs a subset's gates rather than trusting its status), lifted to the stage
level. A campaign that has drifted therefore reports as drifted, not as done.

THE EIGHT STAGES, and what each one's exit predicate actually tests:

    charter    the exit criterion exists and names a unit (a criterion that names no
               unit is not falsifiable -- several counts are simultaneously correct)
    enumerate  the population partition sums to its stated total
    attribute  every enumerated unit carries a disposition
    anchor     every published result declares a basis from the closed enum
    pilot      at least one unit has passed every gate it declares -- the rig is proven
               before scale, because four tools built against the first artifact family
               were each silently wrong on the second
               (field-notes/2026-07-30-structural-checks-that-pass-for-the-wrong-reason)
    scale      every wave marked complete has its planned units present
    close      coverage meets the charter's exit criterion
    signoff    reconciliation and audit recorded

MECHANISM 6 -- the decision queue. A decision with `state: open` and a `blocks: <stage>`
edge BLOCKS that stage. The supervisor surfaces it; it never infers an answer. The scope
calls SC-A..SC-G are exactly this: the owner's to decide, and the campaign should stop at
them rather than guess.

Autonomy contract (decisions/2026-08-15-execute-original-plan-over-verdict-rewrite):
autonomous within a wave, hard block at scope calls and wave go/no-go.

Usage:
    python viewer/tools/campaign.py status [DESCRIPTOR ...]
    python viewer/tools/campaign.py next   [DESCRIPTOR ...]

Exit codes: 0 OK, 1 a stage predicate failed, 2 nothing inspected.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("campaign_common", ROOT / "viewer/tools/campaign_common.py")
_cc = importlib.util.module_from_spec(_spec)     # type: ignore[arg-type]
sys.modules["campaign_common"] = _cc
_spec.loader.exec_module(_cc)                     # type: ignore[union-attr]
Scope, REFUSE = _cc.Scope, _cc.REFUSE
BASES, NOT_HEADROOM = _cc.BASES, _cc.NOT_HEADROOM



PASS_STATE, FAIL_STATE, REFUSE_STATE = "pass", "fail", "refuse"


@dataclass
class Verdict:
    """Three states, not two.

    `REFUSE` is deliberately distinct from `FAIL` (.claude/rules/campaign-lifecycle.md):
    a predicate that found problems is working; a predicate that had NOTHING to judge has
    no verdict to give, and reporting that as PASS is how `anchor` reported
    "0 result(s) carry a declared basis" as green while guarding the metric-basis
    discipline this whole campaign is organised around
    (bugs/2026-08-15-campaign-stage-predicates-pass-without-evidence).

    `passed` stays the first positional field so every existing call site is unchanged;
    a REFUSE is `passed=False` with `state=REFUSE_STATE`.
    """
    passed: bool
    reason: str
    blocked_by: str | None = None
    state: str = ""

    def __post_init__(self) -> None:
        if not self.state:
            self.state = PASS_STATE if self.passed else FAIL_STATE

    @staticmethod
    def refuse(reason: str) -> "Verdict":
        return Verdict(False, reason, state=REFUSE_STATE)


@dataclass
class Stage:
    name: str
    predicate: Callable[[dict], Verdict]


# ------------------------------------------------------------------ predicates

def _charter(d: dict) -> Verdict:
    c = d.get("charter") or {}
    crit = (c.get("exit_criterion") or "").strip()
    if not crit:
        return Verdict(False, "charter.exit_criterion is empty")
    unit = ((d.get("population") or {}).get("unit") or "").strip()
    # A criterion that never names the unit it counts is not falsifiable -- but the match
    # must be on any SUBSTANTIVE word of the unit, not its first token. An earlier version
    # keyed on the first token and so demanded the literal "mmlu" from a unit named
    # "MMLU subject splits (lm-eval-harness v0.4.x)", failing a criterion that correctly
    # says "every split ...". That is a check answering a question adjacent to the one asked.
    if unit:
        lo = crit.lower()
        words = [w.strip("()-").lower() for w in unit.split()]
        words = [w for w in words if w.isalpha() and len(w) >= 4]
        if words and not any(w in lo or w.rstrip("s") in lo for w in words):
            return Verdict(False, f"exit_criterion does not name the population unit {unit!r}")
    return Verdict(True, "exit criterion present and names its unit")


_ROW_SUFFIX = re.compile(r"_\d+$")


def _granularity(uid: str) -> str:
    """RETAINED FOR REFERENCE ONLY -- do not gate on this. See `_enumerate`.

    An earlier version read the `_N` suffix as a ROW index and called an unsuffixed id a
    CASE, then failed any units list holding both. That inference is WRONG, and measuring
    it is what showed why: in TS 38.521-4 the `_N` indexes a **variant**, each variant owns
    its own `Test Purpose` sub-clause (which is the enumeration rule for what a case IS),
    and no bare `5.2.2.1.10` case exists at all -- the base is not a spec concept. So the
    live descriptor's "113 row-shaped, 20 case-shaped" was 133 uniform VARIANTS, 113 of
    which the spec chose to index. The gate was a false positive on all 133.
    """
    return "row" if _ROW_SUFFIX.search(uid) else "case"


def _unit_tokens(text: str) -> set[str]:
    """Normalised content words: hyphens split, plurals folded, case ignored."""
    return {w.rstrip("s") for w in re.split(r"[^a-z0-9.]+", (text or "").lower()) if w}


def _enumerate(d: dict) -> Verdict:
    p = d.get("population") or {}
    total, part = p.get("total"), p.get("partition")
    if not isinstance(total, int) or not isinstance(part, dict):
        return Verdict(False, "population.total or .partition missing")
    s = sum(v for v in part.values() if isinstance(v, int))
    if s != total:
        return Verdict(False, f"partition sums to {s}, total is {total}")

    # A partition that sums is necessary and NOT sufficient: several counts are
    # simultaneously correct, so the descriptor must SAY which one it publishes, and its
    # visible label must not contradict that. The second half is the defect that actually
    # exists upstream -- PROMPT VARIANTS reported as "benchmark tasks", while the register's
    # own sibling field is named `of_covered_variants` and its reconciliation block says in
    # as many words that a published ratio must name its unit.
    #
    # `unit_granularity` is a FREE-FORM declared string, not a closed enum. An earlier
    # version required one of ("row", "case") and so rejected a scaling-law campaign,
    # whose unit is a "(model size, token budget) grid point" -- the closed-enum failure the
    # Phase-6 falsifier exists to catch, committed a second time in a second field.
    #
    # What this deliberately NO LONGER does is infer granularity from id SHAPE. The `_N`
    # suffix indexes a VARIANT, not a row; an unsuffixed id is a variant the task registry
    # chose not to index, not a coarser unit; and no bare base task exists in it at all. That
    # inference failed every live unit as "MIXED" when they are uniform -- a false positive
    # on the entire population, removed after measuring rather than after arguing.
    declared = (p.get("unit_granularity") or "").strip().lower()
    units = [u for u in (d.get("units") or []) if isinstance(u, dict) and u.get("id")]
    if units and not declared:
        return Verdict(False, "population.unit_granularity not declared - "
                              "several counts are simultaneously correct")
    # The visible label must CONTAIN the unit it declares. That is the whole invariant, and
    # it is one-directional on purpose: "benchmark task variants" legitimately names the
    # variant unit while mentioning tasks as a qualifier, and a rule that failed it for
    # containing the word "task" would be a false positive on a correct label. What it does
    # catch is the defect that exists: "benchmark tasks" declared at variant granularity --
    # a variant count wearing a task label, with no "variant" in sight.
    if units and not _unit_tokens(p.get("unit")) >= _unit_tokens(declared):
        return Verdict(False, f"population.unit label {p.get('unit')!r} does not name the "
                              f"{declared!r} it declares - a published ratio must name the "
                              f"unit it actually counts")
    return Verdict(True, f"partition sums to {total}"
                         + (f"; {len(units)} unit(s) declared at '{declared}' granularity"
                            if units else ""))


def _attribute(d: dict) -> Verdict:
    units = d.get("units") or []
    missing = [u.get("id", f"<units[{i}]>") for i, u in enumerate(units)
               if isinstance(u, dict) and not u.get("disposition")]
    if missing:
        return Verdict(False, f"{len(missing)} unit(s) with no disposition: {missing[:5]}")
    if not units:
        return Verdict(False, "no units enumerated yet")
    return Verdict(True, f"all {len(units)} unit(s) attributed")


def _anchor(d: dict) -> Verdict:
    results = [r for r in (d.get("results") or []) if isinstance(r, dict)]
    if not results:
        # The empty loop used to fall straight through to the success return. There is no
        # denominator here, so there is no verdict -- REFUSE, and say what would supply one.
        return Verdict.refuse(
            "no results to anchor - the basis gate has no denominator. Wire the per-case "
            "margins into descriptor.results (they live in the subset reports today)")
    bad = [r.get("id", "<no id>") for r in results
           if r.get("basis") is None or r.get("basis") not in BASES]
    if bad:
        return Verdict(False, f"{len(bad)} result(s) with no/invalid basis: {bad[:5]}")
    return Verdict(True, f"{len(results)} result(s) carry a declared basis")


def _pilot(d: dict) -> Verdict:
    """One unit through EVERY gate it declares. The rig is proven before scale."""
    units = [u for u in (d.get("units") or []) if isinstance(u, dict)]
    for u in units:
        gates = u.get("gates") or {}
        if gates and all(v == "pass" for v in gates.values()):
            return Verdict(True, f"pilot unit {u.get('id')!r} passed all {len(gates)} gate(s)")
    failing = [(u.get("id"), [k for k, v in (u.get("gates") or {}).items() if v != "pass"])
               for u in units if u.get("gates")]
    if failing:
        return Verdict(False, f"no unit has passed every gate; failing: {failing[:3]}")
    return Verdict(False, "no unit declares gates yet - the rig is unproven")


def _scale(d: dict) -> Verdict:
    waves = [w for w in (d.get("waves") or []) if isinstance(w, dict)]
    incomplete = [w.get("wave") for w in waves
                  if w.get("status") == "complete" and not w.get("units_present", True)]
    if incomplete:
        return Verdict(False, f"wave(s) marked complete with units missing: {incomplete}")
    return Verdict(True, f"{len(waves)} wave(s) consistent")


DONE_STATES = {"verified"}
"""What counts as done for the correctness half of coverage closure.

`legacy-verified` is deliberately absent: D7 made the 32 pre-2026-08-15 units a COUNTABLE
backlog rather than a silent grandfathering, so they are attributed, covered, and not done.
"""


def _unit_done(u: dict) -> bool:
    """D9, all three clauses. A `state: verified` with no discrimination proof is exactly
    the FALSE POSITIVE clause 3 exists to catch -- it is indistinguishable from a genuine
    pass by every other check in the system, which is why it needs its own."""
    v = u.get("verification") or {}
    if (v.get("state") or "") not in DONE_STATES:
        return False
    proof = v.get("discrimination_proof") or {}
    return bool(proof.get("discriminates"))


def _close(d: dict) -> Verdict:
    """Coverage closure is BOTH halves (v2 s1.2): every member dispositioned AND every
    in-scope unit done. This returned True as soon as an attribution COUNT existed --
    the accounting half alone, which is the same defect the v2 plan's own first draft
    committed in prose while this committed it in code."""
    pop = d.get("population") or {}
    inreg = pop.get("in_register") or {}
    attributed = inreg.get("attributed")
    units = [u for u in (d.get("units") or []) if isinstance(u, dict)]

    if attributed is None:
        # THE MESSAGE'S SECOND ROUTE, now actually implemented.
        #
        # This REFUSE told the reader to "supply population.in_register.attributed, OR
        # enumerate the population as units and count their dispositions" -- and then
        # checked only the first, refusing before it ever looked at the units. The
        # calibration campaign takes the second route (125 units, every one carrying a
        # disposition, no external register to hold a count) and was refused anyway, by
        # a gate naming the very thing it had already done. The comment here even said
        # "exposed by the calibration campaign" while the code kept refusing it.
        #
        # A denominator derived from enumerated dispositions is strictly better evidence
        # than a hand-written count: it is re-derived from the units themselves rather
        # than asserted alongside them.
        dispositioned = [u for u in units if u.get("disposition")]
        if dispositioned:
            attributed = len(dispositioned)
        else:
            # Genuinely no denominator by EITHER route -> REFUSE, not FAIL. A gate that
            # found problems is working; a gate that cannot establish a denominator has
            # no verdict to give, and conflating the two is what this harness exists to
            # stop.
            return Verdict.refuse("no attribution count recorded and no unit carries a "
                                  "disposition - closure is unmeasurable; supply "
                                  "population.in_register.attributed, or enumerate the "
                                  "population as units with dispositions")
    if not units:
        return Verdict.refuse("attribution count recorded but no units enumerated - "
                              "closure cannot be re-derived from a count alone")

    in_scope = [u for u in units if u.get("disposition") == "in-scope"]
    undone = [u.get("id", "<no id>") for u in in_scope if not _unit_done(u)]
    if undone:
        legacy = sum(1 for u in in_scope
                     if (u.get("verification") or {}).get("state") == "legacy-verified")
        detail = f" ({legacy} legacy-verified)" if legacy else ""
        return Verdict(False, f"{len(undone)} of {len(in_scope)} in-scope unit(s) not "
                              f"verified{detail}: {undone[:3]}")
    return Verdict(True, f"{attributed} attributed; all {len(in_scope)} in-scope unit(s) verified")


def _signoff(d: dict) -> Verdict:
    if not (d.get("signoff") or {}).get("reconciled"):
        return Verdict(False, "no reconciliation recorded")
    return Verdict(True, "reconciled")


STAGES = [
    Stage("charter", _charter),
    Stage("enumerate", _enumerate),
    Stage("attribute", _attribute),
    Stage("anchor", _anchor),
    Stage("pilot", _pilot),
    Stage("scale", _scale),
    Stage("close", _close),
    Stage("signoff", _signoff),
]


STAGE_NAMES = {s.name for s in STAGES}


def stages_for(desc: dict) -> list[Stage]:
    """The stage list THIS campaign has (D10 rejected one universal state machine).

    A calibration campaign has no pilot unit and no external sign-off; forcing it through the
    conformance lifecycle means either inventing stages it does not have or leaving it
    permanently blocked on them. So a descriptor may declare a subset -- omission is the
    point. The ORDER, though, is always the lifecycle's own: a descriptor that could
    reorder stages would make `blocked_by` meaningless.
    """
    declared = desc.get("stages")
    if not isinstance(declared, list) or not declared:
        return list(STAGES)
    want = {s for s in declared if s in STAGE_NAMES}
    return [s for s in STAGES if s.name in want]


def evaluate(desc: dict) -> dict[str, Verdict]:
    """Re-derive every stage predicate. Order matters: a stage is blocked by the first
    earlier stage that fails, and by any open decision naming it."""
    out: dict[str, Verdict] = {}
    blockers = {
        dec.get("blocks"): f"decision:{dec.get('id')}"
        for dec in (desc.get("decisions") or [])
        if isinstance(dec, dict) and dec.get("state") == "open" and dec.get("blocks")
    }
    first_failed: str | None = None
    for st in stages_for(desc):
        v = st.predicate(desc)
        # Only a FAILING stage carries a blocker. Annotating a passing stage with the
        # earlier failure is noise that reads as a cascade where none exists -- caught by
        # running the tool against the real descriptor, not by any test.
        if first_failed is not None:
            v.blocked_by = first_failed
        out[st.name] = v
        if not v.passed and first_failed is None:
            first_failed = st.name
    # An OPEN owner decision blocks its stage regardless of whether the stage's own
    # predicate is met -- that is mechanism 6: the campaign stops and asks rather than
    # inferring an answer. It overrides an upstream blocker because it is the more
    # specific and more actionable reason.
    for stage_name, blocker in blockers.items():
        if stage_name in out:
            out[stage_name].blocked_by = blocker
    return out


ACTION_KINDS = {"work", "decision", "done", "escalated"}
"""The closed enum a driver dispatches on.

`done` exists because ABSENT must never be how "finished" is expressed: a driver reading
an absent action as "nothing to do" cannot tell a COMPLETE campaign from a BROKEN
evaluator, and those call for opposite responses. `escalated` is produced by the failure
ledger (P3) once the restart-intensity ceiling fires.
"""


def _units_for_stage(desc: dict, stage: str) -> list[str]:
    """Which units a work action is about. A driver handed `work` with no ids must guess."""
    units = [u for u in (desc.get("units") or []) if isinstance(u, dict)]
    if stage == "close":
        return [u.get("id", "<no id>") for u in units
                if u.get("disposition") == "in-scope" and not _unit_done(u)]
    if stage == "attribute":
        return [u.get("id", "<no id>") for u in units if not u.get("disposition")]
    if stage == "enumerate":
        declared = ((desc.get("population") or {}).get("unit_granularity") or "").lower()
        return [str(u["id"]) for u in units
                if u.get("id") and _granularity(str(u["id"])) != declared]
    return []


def next_action_obj(desc: dict, ledger=None) -> dict:
    """The machine-readable next action. Always an object, never None.

    `ledger` is a campaign_ledger.Ledger. When supplied, units the restart-intensity
    ceiling has already exhausted are WITHHELD from the work action rather than re-issued
    -- and when that leaves nothing to work on, the action is `escalated`. Escalation is
    per-unit: one exhausted unit must not stop a campaign that still has workable ones.
    """
    states = evaluate(desc)
    campaign = desc.get("campaign", "<unnamed>")
    for st in stages_for(desc):
        v = states[st.name]
        blocked_decision = v.blocked_by and v.blocked_by.startswith("decision:")
        if not (v.passed and not blocked_decision):
            if blocked_decision:
                dec_id = v.blocked_by.split(":", 1)[1]
                dec = next((x for x in (desc.get("decisions") or [])
                            if isinstance(x, dict) and x.get("id") == dec_id), {})
                return {"campaign": campaign, "stage": st.name, "kind": "decision",
                        "detail": f"open decision {dec_id!r} blocks stage {st.name!r} - "
                                  f"the owner decides; the campaign does not infer it",
                        "unit_ids": [], "blocked_by": v.blocked_by,
                        "state": v.state, "decision": dec}
            ids = _units_for_stage(desc, st.name)
            exhausted = sorted(ledger.escalated_units(st.name)) if ledger is not None else []
            workable = [i for i in ids if i not in set(exhausted)]
            if exhausted and ids and not workable:
                # Every unit this stage could act on has hit the ceiling. Re-issuing any of
                # them is the retry loop the ceiling exists to stop.
                return {"campaign": campaign, "stage": st.name, "kind": "escalated",
                        "detail": f"every unit at stage {st.name!r} has hit the restart "
                                  f"ceiling; the campaign declines to retry",
                        "unit_ids": [i for i in ids if i in set(exhausted)],
                        "blocked_by": v.blocked_by, "state": v.state,
                        "escalations": [list(e) for e in ledger.escalations()]}
            return {"campaign": campaign, "stage": st.name, "kind": "work",
                    "detail": v.reason, "unit_ids": workable,
                    "blocked_by": v.blocked_by, "state": v.state,
                    "withheld_escalated": [i for i in ids if i in set(exhausted)]}
    return {"campaign": campaign, "stage": None, "kind": "done",
            "detail": "every stage predicate is met and no decision is open",
            "unit_ids": [], "blocked_by": None, "state": PASS_STATE}


def next_action(desc: dict) -> str | None:
    """The single next actionable thing, or None when the campaign is complete."""
    states = evaluate(desc)
    for st in stages_for(desc):
        v = states[st.name]
        if not v.passed:
            if v.blocked_by and v.blocked_by.startswith("decision:"):
                return f"BLOCKED on {v.blocked_by} - the owner decides; the campaign does not infer it"
            if v.state == REFUSE_STATE:
                return f"stage '{st.name}': REFUSE - {v.reason}"
            return f"stage '{st.name}': {v.reason}"
    return None


# ------------------------------------------------------------------------- CLI

def _registered() -> list[Path]:
    f = ROOT / ".claude/campaigns"
    if not f.exists():
        return []
    return [ROOT / ln.split("#", 1)[0].strip()
            for ln in f.read_text(encoding="utf-8").splitlines()
            if ln.split("#", 1)[0].strip()]


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "status"
    as_json = "--json" in argv
    paths = [Path(a) for a in argv[1:] if not a.startswith("--")] or _registered()

    scope = Scope("campaign")
    descs: list[tuple[Path, dict]] = []
    for p in paths:
        try:
            descs.append((p, json.loads(p.read_text(encoding="utf-8"))))
            scope.saw(p)
        except FileNotFoundError:
            scope.could_not_read(p, "not found")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            scope.could_not_read(p, type(e).__name__)

    if scope.verdict() == REFUSE:
        print(scope.refuse_message(), file=sys.stderr)
        return 2

    if as_json:
        # stdout carries JSON and nothing else -- the driver pipes it straight into a
        # parser, so the scope banner goes to stderr where it is still auditable.
        scope.emit(stream=sys.stderr)
        actions = [next_action_obj(d) for _, d in descs]
        print(json.dumps(actions, indent=1))
        return 0 if all(a["kind"] == "done" for a in actions) else (
            2 if any(a.get("state") == REFUSE_STATE for a in actions) else 1)

    scope.emit()

    rc = 0
    for path, d in descs:
        states = evaluate(d)
        print(f"\n{d.get('campaign', path.name)}")
        for st in stages_for(d):
            v = states[st.name]
            # A stage with a blocker renders BLOCKED even when its own predicate is met:
            # its predicate passing does not make it enterable, and "PASS <- charter" reads
            # as a contradiction rather than as "not reachable yet".
            if v.blocked_by:
                mark = "BLOCKED"
            elif v.state == REFUSE_STATE:
                mark = "REFUSE"
            else:
                mark = "PASS" if v.passed else "FAIL"
            suffix = f"  <- {v.blocked_by}" if v.blocked_by else ""
            print(f"  {mark:8s} {st.name:10s} {v.reason}{suffix}")
        # The exit code reports the FIRST actionable stage -- the same one `next` names.
        # An earlier version let any REFUSE anywhere set rc=2, so a campaign whose real
        # problem was a FAIL at `enumerate` exited "could not establish a denominator"
        # while `next` correctly said enumerate. Code and next-action must not disagree.
        # Found by running the tool against the live descriptor, not by a fixture.
        first = next((states[s.name] for s in stages_for(d) if not states[s.name].passed), None)
        if first is not None:
            rc = max(rc, 2 if first.state == REFUSE_STATE else 1)
        if cmd == "next":
            print(f"\n  NEXT: {next_action(d) or 'campaign complete'}")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
