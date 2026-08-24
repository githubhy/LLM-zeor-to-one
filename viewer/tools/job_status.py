#!/usr/bin/env python3
"""Classify a background job as progressing / stalled / dead — one call, no stored state.

The harness only notifies on **exit**, so a job that hangs never reports anything, and a job that
is merely slow is indistinguishable from one that died. Both failure modes have bitten this repo,
in opposite directions:

  * **False ALIVE** — `.claude/rules/reset-durability.md`: after a container reset a dead run's
    lingering bash *wrapper* still matched `pgrep -f <cmd>`. Its conclusion, "detect death by
    checkpoint-mtime staleness, not `pgrep`", is half the answer.
  * **False DEAD** — measured upstream on a long sweep: `progress.log` went 19 minutes without a line
    while three workers sat at 99.7 % CPU. A *completion-granular* heartbeat is silent for a whole
    unit by construction, so staleness alone reads a healthy 30-minute unit as a hang.

So neither signal is sufficient alone, and this tool takes both:

  1. **CPU accumulation**, sampled twice over `--sample-secs`. Answers "is it computing *right
     now*", which no mtime can. It is also what excludes the wrapper: a process with wall time and
     no CPU is not doing work, whatever its command line says.
  2. **Watch-path freshness** — the newest mtime anywhere under `--watch`. Catches sub-unit
     progress (a per-shape sidecar landing mid-unit) that a completion log cannot see, and covers
     a worker that happens to be between units during the sample window.

The two are OR-ed for liveness and AND-ed for the stall verdict. `classify()` is pure so the
verdict is tested against fixtures rather than against live processes; see
`tests/tools/test_job_status.py`.

Usage:
    python3 viewer/tools/job_status.py                       # every job in .claude/background-jobs.json
    python3 viewer/tools/job_status.py --job eval-sweep
    python3 viewer/tools/job_status.py --match sc_c_cases --watch artifacts/.../sweeps
    python3 viewer/tools/job_status.py --json

Exit status is 0 for every verdict including DEAD and NONE: absence and death are *answers*, and a
caller that appends this line to each turn must not see a failure because nothing is running.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ALIVE = "alive-progressing"
STALLED = "alive-stalled"
DEAD = "dead"
NONE = "none"

REGISTRY = Path(".claude/background-jobs.json")

#: A process whose CPU time is under this fraction of its wall time, and which accumulated no CPU
#: during the sample window, is a wrapper rather than a worker. Deliberately generous: a real
#: worker that is even 5 % busy still counts, while the `/bin/bash -c …` wrapper that produced the
#: documented false-ALIVE sits at ~0.
WRAPPER_CPU_RATIO = 0.05

#: Newest write under the watch path older than this reads as "no file-level progress". One unit of
#: the slowest observed workload (~30 min) with headroom, so a long unit never trips it on its own.
DEFAULT_STALL_SECS = 2400.0


@dataclass(frozen=True)
class Worker:
    pid: int
    cmd: str
    elapsed_s: float
    cpu_s: float
    cpu_delta: float          # CPU seconds accumulated during the sample window

    @property
    def cpu_ratio(self) -> float:
        return (self.cpu_s / self.elapsed_s) if self.elapsed_s > 0 else 0.0

    @property
    def is_wrapper(self) -> bool:
        return self.cpu_delta <= 0.0 and self.cpu_ratio < WRAPPER_CPU_RATIO


def classify(workers, watch_age_s, watch_exists, stall_secs=DEFAULT_STALL_SECS):
    """The verdict, as a pure function of the two signals.

    `watch_age_s` is seconds since the newest write under the watch path, or None if there is
    nothing to read. `watch_exists` says whether the path is there at all — which is what
    separates *never started* from *died*.
    """
    real = [w for w in workers if not w.is_wrapper]
    fresh = watch_age_s is not None and watch_age_s < stall_secs

    if not real:
        # No process is doing work. Fresh files cannot resurrect it — they only date the corpse.
        return DEAD if watch_exists else NONE
    if any(w.cpu_delta > 0 for w in real) or fresh:
        return ALIVE
    return STALLED


def sample_workers(pattern, sample_secs=1.0):
    """Two `ps` snapshots `sample_secs` apart, joined on pid.

    Self-exclusion matters: the shell that runs this tool has the pattern in its own command line
    and would otherwise be counted as a job. It is filtered by pid, and would in any case be
    dropped as a wrapper.
    """
    mine = {str(subprocess.os.getpid()), str(subprocess.os.getppid())}
    rx = re.compile(pattern)

    def snap():
        out = subprocess.run(["ps", "-eo", "pid=,etimes=,cputimes=,args="],
                             capture_output=True, text=True, encoding="utf-8").stdout
        rows = {}
        for line in out.splitlines():
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            pid, et, ct, args = parts
            if pid in mine or not rx.search(args):
                continue
            if "job_status.py" in args:          # never report on ourselves
                continue
            try:
                rows[int(pid)] = (float(et), float(ct), args)
            except ValueError:
                continue
        return rows

    first = snap()
    if sample_secs and first:
        time.sleep(sample_secs)
        second = snap()
    else:
        second = first

    workers = []
    for pid, (et, ct, args) in second.items():
        prev_ct = first.get(pid, (et, ct, args))[1]
        workers.append(Worker(pid=pid, cmd=args, elapsed_s=et, cpu_s=ct,
                              cpu_delta=max(0.0, ct - prev_ct)))
    return workers


def newest_mtime(path: Path):
    """(age_seconds, exists) for the newest file at or under `path`."""
    if not path.exists():
        return None, False
    if path.is_file():
        return max(0.0, time.time() - path.stat().st_mtime), True
    newest = None
    for p in path.rglob("*"):
        try:
            if p.is_file():
                m = p.stat().st_mtime
                newest = m if newest is None else max(newest, m)
        except OSError:
            continue
    return (None if newest is None else max(0.0, time.time() - newest)), True


def count_progress(log: Path):
    """(ok, failed) from a batch progress log, or (None, None) if there is none to read.

    Matches the ` OK   ` / ` FAIL ` markers `sc_c_sweep_batch.sh` writes.
    """
    if not log or not log.exists():
        return None, None
    text = log.read_text(encoding="utf-8", errors="replace")
    return (len(re.findall(r" OK   ", text)), len(re.findall(r" FAIL ", text)))


def _fmt_age(s):
    if s is None:
        return "n/a"
    return f"{int(s // 60)}m" if s < 3600 else f"{s / 3600:.1f}h"


def report(name, cfg, sample_secs):
    watch = Path(cfg["watch"])
    workers = sample_workers(cfg["match"], sample_secs)
    age, exists = newest_mtime(watch)
    state = classify(workers, age, exists, cfg.get("stall_secs", DEFAULT_STALL_SECS))
    ok, failed = count_progress(Path(cfg["progress_log"]) if cfg.get("progress_log") else None)
    real = [w for w in workers if not w.is_wrapper]
    return {
        "job": name,
        "state": state,
        "workers": len(real),
        "wrappers_filtered": len(workers) - len(real),
        "newest_write_age_s": None if age is None else round(age, 1),
        "ok": ok,
        "failed": failed,
        "total": cfg.get("total"),
        "detail": [{"pid": w.pid, "elapsed_s": round(w.elapsed_s),
                    "cpu_s": round(w.cpu_s), "cpu_pct": round(100 * w.cpu_ratio),
                    "cpu_delta_s": round(w.cpu_delta, 2)} for w in real],
    }


def render(r):
    head = f"[{r['job']}] {r['state']}"
    bits = [f"{r['workers']} worker(s)"]
    if r["wrappers_filtered"]:
        bits.append(f"{r['wrappers_filtered']} wrapper(s) filtered")
    if r["ok"] is not None:
        done = f"{r['ok']} OK"
        if r["failed"]:
            done += f" + {r['failed']} FAIL"
        if r["total"]:
            done += f" of {r['total']}"
        bits.append(done)
    bits.append(f"newest write {_fmt_age(r['newest_write_age_s'])} ago")
    lines = [f"{head}: " + ", ".join(bits)]
    for d in r["detail"]:
        lines.append(f"    pid {d['pid']:<7} elapsed {d['elapsed_s'] // 60:.0f}m  "
                     f"cpu {d['cpu_pct']}%  (+{d['cpu_delta_s']}s this sample)")
    return "\n".join(lines)


def load_registry():
    if not REGISTRY.exists():
        return {}
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--job", help="a job name from .claude/background-jobs.json")
    ap.add_argument("--match", help="regex matched against process command lines")
    ap.add_argument("--watch", help="file or directory whose newest mtime is the progress signal")
    ap.add_argument("--progress-log", help="batch log carrying ' OK   ' / ' FAIL ' markers")
    ap.add_argument("--total", type=int, help="expected unit count, for the completion fraction")
    ap.add_argument("--stall-secs", type=float, default=DEFAULT_STALL_SECS)
    ap.add_argument("--sample-secs", type=float, default=1.0,
                    help="CPU sampling window; 0 skips the second snapshot")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.match:
        jobs = {a.job or "adhoc": {"match": a.match, "watch": a.watch or ".",
                                   "progress_log": a.progress_log, "total": a.total,
                                   "stall_secs": a.stall_secs}}
    else:
        reg = load_registry()
        jobs = {a.job: reg[a.job]} if a.job else reg

    if not jobs:
        out = {"jobs": []}
        print(json.dumps(out) if a.json else "[job-status] no jobs registered")
        return 0

    results = [report(n, c, a.sample_secs) for n, c in sorted(jobs.items())]
    if a.json:
        print(json.dumps({"jobs": results}, indent=1))
    else:
        print("\n".join(render(r) for r in results))
    return 0


if __name__ == "__main__":
    # A status line is routinely piped into `head`/`grep`, and a tool meant to be run at the end of
    # every turn must not traceback when its reader closes early. Exit quietly on SIGPIPE instead.
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except BrokenPipeError:
            pass
        raise SystemExit(0)
