#!/usr/bin/env python3
"""The campaign failure ledger and its restart-intensity ceiling.

P3 of `plans/2026-08-15-campaign-driver-v2.md` (inherited verbatim from v1.1 Phase 2).

WHY A CEILING AT ALL. An autonomous driver's failure mode is not crashing -- it is
retrying. A unit that is systematically broken will absorb an entire iteration budget in
re-attempts, and every one of them looks like progress to a loop that only counts
iterations. Erlang/OTP solved this with a supervisor restart intensity: MaxR restarts
within MaxT seconds, else give up and escalate to the layer above.

WHY NOT WALL-CLOCK. OTP keys on time because a supervised process restarts in
milliseconds, so a time window is a good proxy for "the same thing keeps breaking". A
campaign unit legitimately takes hours and the driver may idle for days between wakes, so
that proxy inverts: a time window either never fills (slow campaign) or fills with
unrelated failures (busy one). What the window is really approximating is directly
observable here, so this keys on it: **same unit, same stage, same signature**.

  three same-signature failures at one stage  -> ESCALATE (systematic)
  three failures spread across stages         -> keep going (transient)
  three different signatures at one stage      -> keep going (three problems, not one)

That second line is the load-bearing one. A ceiling that fires on it stops every hard
campaign on its first bad day, which is how a safety mechanism gets switched off.

DURABILITY. The ledger is on disk and re-read per instance. A count that dies with the
process is not a ceiling, and a container-snapshot rollback can revert local state at any
moment (.claude/rules/reset-durability.md), so the file is the record and it is committed.

Usage:
    from campaign_ledger import Ledger
    led = Ledger(Path("artifacts/<campaign>/failures.json"))
    led.record(unit="5.2.2.1.10_1", stage="close", signature="AssertionError@margin", commit=sha)
    if led.is_escalated(unit, stage, signature): ...
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

CEILING = 3
"""Attempts at one (unit, stage, signature) before the campaign declines to retry.

Three, from D8: "escalate on the third occurrence". Two is within the range of a genuine
transient (a flaky fetch, a race); by three the campaign is telling you something.
"""

_ENV_CEILING = "CAMPAIGN_RESTART_CEILING"


def _ceiling() -> int:
    try:
        return max(1, int(os.environ.get(_ENV_CEILING, "")))
    except ValueError:
        return CEILING


def _head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=10).stdout.strip() or "unknown"
    except Exception:
        return "unknown"


@dataclass
class Ledger:
    """An append-only failure record keyed on (unit, stage, signature)."""
    path: Path
    entries: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.entries = self._load()

    # ------------------------------------------------------------------ storage

    def _load(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # A corrupt ledger must not be silently treated as empty -- that would reset
            # every ceiling to zero, which is the one failure mode this file exists to
            # prevent. Refuse loudly by re-raising with the path named.
            raise ValueError(f"failure ledger at {self.path} is unreadable; "
                             f"refusing to proceed with a zeroed ceiling")
        return list(d.get("failures") or [])

    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({
            "schema": "campaign-failures/v1",
            "ceiling": _ceiling(),
            "_note": ("Keyed on (unit, stage, signature), NOT on wall-clock: a campaign unit "
                      "takes hours and the driver idles for days, so a time window is the "
                      "wrong axis. See viewer/tools/campaign_ledger.py."),
            "failures": self.entries,
        }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    # -------------------------------------------------------------------- write

    def record(self, *, unit: str, stage: str, signature: str,
               commit: str | None = None, at: str | None = None) -> dict:
        """Append one failure. Re-reads from disk first, so concurrent instances append
        rather than truncate (one writer is still the rule -- this is belt and braces)."""
        self.entries = self._load()
        prior = self.attempts(unit, stage, signature)
        e = {"unit": unit, "stage": stage, "signature": signature,
             "commit": commit or _head(), "attempt": prior + 1,
             "at": at or "unrecorded"}
        self.entries.append(e)
        self._flush()
        return e

    # --------------------------------------------------------------------- read

    def attempts(self, unit: str, stage: str, signature: str) -> int:
        return sum(1 for e in self.entries
                   if e.get("unit") == unit and e.get("stage") == stage
                   and e.get("signature") == signature)

    def is_escalated(self, unit: str, stage: str, signature: str) -> bool:
        return self.attempts(unit, stage, signature) >= _ceiling()

    def escalations(self) -> list[tuple[str, str, str]]:
        """Every (unit, stage, signature) at or over the ceiling."""
        seen: dict[tuple[str, str, str], int] = {}
        for e in self.entries:
            k = (e.get("unit", ""), e.get("stage", ""), e.get("signature", ""))
            seen[k] = seen.get(k, 0) + 1
        c = _ceiling()
        return [k for k, n in seen.items() if n >= c]

    def escalated_units(self, stage: str | None = None) -> set[str]:
        """Units the campaign has declined to retry, optionally at one stage."""
        return {u for u, s, _ in self.escalations() if stage is None or s == stage}
