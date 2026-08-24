"""Shared denominator self-report for every campaign gate.

Phase 3 of `plans/2026-08-15-campaign-lifecycle-harness.md` (mechanism 2, generalized).

The measured problem: a gate that cannot read its corpus reports the same green as a
gate that read it and agreed. `check-value-ledger` matched 12 of 811 files and
`validate-refs` matched 1, both exit 0; scope defects outnumbered logic defects three
to one in that sweep (`field-notes/2026-07-31-blind-gates.md`). The fix is not a better
matcher -- it is making every gate state its own denominator and REFUSE when it does
not have one.

Contract for a consuming gate:

    scope = Scope("my-gate")
    for path in targets:
        try:    doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:  scope.could_not_read(path, str(e)); continue
        scope.saw(path)
        ...
    print(scope.render())
    if scope.verdict() is REFUSE:
        return 2            # NOT 0 -- "did not look" is never a pass

`REFUSE` is deliberately distinct from `FAIL`. A gate that found problems is working;
a gate that could not establish a denominator has no verdict to give, and conflating
the two is what let the blind gates read as agreement.
"""
from __future__ import annotations

import sys
from pathlib import Path

OK = "OK"
REFUSE = "REFUSE"

#: THE closed basis enum -- one definition, imported by every campaign gate.
#: Three copies drifted apart inside a single upstream build session before this was
#: consolidated: a register and its gate disagreed, and every margin sat in the disagreement.
#: A quantity is not a number until it names which of these it is measured against.
BASES = {
    "reference-performance",  # the reference REPRODUCED under our own harness and prompt;
                              # THIS is the only basis on which a margin is capability headroom
    "published-value",        # a vendor model-card / paper / leaderboard headline number. It is
                              # reference performance PLUS a configuration stack (prompt template,
                              # few-shot k and exemplar pool, decoding params, harness version,
                              # answer-extraction rule), so a margin against it is mostly harness
                              # and prompt difference (.claude/rules/sim-report-completeness.md
                              # [opt:SIM-REQBASIS])
    "requirement",            # a declared target threshold the result must clear; synonym of
                              # published-value for descriptors not using that vocabulary
    "published-mean",         # the mean/aggregate over independent published reproductions. NOT
                              # reference performance: it carries every contributor's own
                              # configuration delta, which our harness does not pay
    "harness-baseline",       # a published number re-scored under a THIRD party's harness -- the
                              # published value plus that harness's own scoring conventions
    "closed-form-target",     # a residual vs an analytic prediction (a scaling-law loss, a
                              # pass@k-vs-k curve)
    "absolute",               # a standalone measured value, not a margin against anything
    "none",                   # explicitly not a margin (explicit n/a beats silent absence)
}

#: A margin against these is NOT capability headroom -- it is mostly the configuration stack.
NOT_HEADROOM = {"requirement", "published-value", "published-mean", "harness-baseline"}


class Scope:
    """Tracks what a gate actually inspected, so it can report and refuse honestly."""

    def __init__(self, gate: str, extra: str = "") -> None:
        self.gate = gate
        self.extra = extra
        self.read: list[str] = []
        self.unreadable: list[tuple[str, str]] = []
        self.skipped: list[tuple[str, str]] = []

    def saw(self, path) -> None:
        self.read.append(str(path))

    def could_not_read(self, path, reason: str) -> None:
        self.unreadable.append((str(path), reason))

    def skip(self, path, reason: str) -> None:
        """Deliberately out of scope -- recorded, never silent."""
        self.skipped.append((str(path), reason))

    @property
    def named(self) -> int:
        return len(self.read) + len(self.unreadable) + len(self.skipped)

    def render(self) -> str:
        parts = [
            f"[{self.gate}] scope: {len(self.read)} read of {self.named} named",
            f"{len(self.unreadable)} unreadable",
            f"{len(self.skipped)} skipped",
        ]
        if self.extra:
            parts.append(self.extra)
        return "; ".join(parts)

    def verdict(self) -> str:
        """REFUSE when there is no denominator -- nothing named, or nothing readable."""
        if self.named == 0 or not self.read:
            return REFUSE
        return OK

    def emit(self, stream=None) -> None:
        """Emit the denominator self-report.

        `stream` governs EVERY line, banner included. It did not: the banner had a bare
        `print()` so it always went to stdout while the detail lines honoured `stream`,
        which split one report across two channels and broke `campaign.py next --json`
        (a driver pipes stdout into a parser). Default stays stdout so existing gate
        output is unchanged; a caller that needs a clean stdout passes stderr.
        """
        out = stream if stream is not None else sys.stdout
        print(self.render(), file=out)
        for p, why in self.unreadable:
            print(f"  UNREADABLE  {p}: {why}", file=out)
        for p, why in self.skipped:
            print(f"  skipped     {p}: {why}", file=out)

    def refuse_message(self) -> str:
        if self.named == 0:
            return (
                f"[{self.gate}] REFUSING: nothing to inspect. A green gate must mean "
                f"'looked and found nothing', never 'did not look'."
            )
        return (
            f"[{self.gate}] REFUSING: {self.named} path(s) named, none readable/in-scope. "
            f"That is a scope failure, not a pass."
        )


def severity_from(path: Path, default: str = "warn") -> str:
    """Read a `.claude/<x>-severity` toggle, falling back to `default`."""
    if path.exists():
        v = path.read_text(encoding="utf-8").strip().lower()
        if v in {"off", "warn", "error"}:
            return v
    return default


class PersistenceMismatch(RuntimeError):
    """What a tool reported does not match what it wrote. See .claude/rules/reported-vs-persisted.md."""


def assert_persisted(expected: dict, read_actual, *, what: str = "state") -> None:
    """Compare what a tool BELIEVES it wrote against what re-reading the artifact returns.

    `expected` maps a unit id to the value the tool is about to report; `read_actual` takes a unit
    id and returns the value as it stands ON DISK. Raises `PersistenceMismatch` naming every
    divergence.

    The failure this exists for: `ingest_rung2_verdicts.py` printed "HELD (promotion withheld)" on
    every run for a week while both affected units sat at `state: verified` in their artifacts --
    the write happened before the demotion, so the demotion lived only in the process that logged
    it. Nobody opened the artifact, because every log line said it was protected
    (`bugs/2026-08-23-cross-cutting-hold-reported-but-never-persisted`).

    Call it AFTER writing and BEFORE printing the summary, so the summary is a statement about the
    artifacts rather than about the tool's intentions.
    """
    bad = []
    for unit, want in sorted(expected.items()):
        try:
            got = read_actual(unit)
        except Exception as exc:  # noqa: BLE001 - an unreadable artifact IS a mismatch
            bad.append(f"  {unit}: reported {what}={want!r} but the artifact is unreadable ({exc})")
            continue
        if got != want:
            bad.append(f"  {unit}: reported {what}={want!r} but the artifact holds {got!r}")
    if bad:
        raise PersistenceMismatch(
            f"{len(bad)} of {len(expected)} unit(s) do not match what was reported — the summary "
            f"describes something other than the artifacts:\n" + "\n".join(bad))
