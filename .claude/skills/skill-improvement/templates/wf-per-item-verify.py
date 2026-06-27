#!/usr/bin/env python3
"""Template — Phase 5a per-item verification (deterministic where possible).
For OUTPUT items: demonstrate the proposed mechanism on a known-answer task.
For STRUCTURAL items: build a PROPOSED artifact set + a BASELINE set and show the target
skill's flag-gated validator DISCRIMINATES (passes proposed, fails baseline). Emit verdicts.
Mark INCONCLUSIVE any item a cheap test cannot fairly decide (do NOT rig the demo)."""
import json, subprocess, sys
from pathlib import Path
verdicts = {}

def output_item_example():
    # EXAMPLE pattern (replace with the target item's known-answer task):
    # build a task whose answer is known, run baseline-method vs proposed-method, compare.
    return {"item":"<id>", "claim":"<claim>", "pass": None, "verdict":"inconclusive",
            "note":"replace with a real known-answer demo; mark inconclusive if a cheap test can't fairly decide it"}

def structural_item_example():
    # EXAMPLE: build proposed vs baseline artifacts, run the target validator with --flags,
    # assert proposed passes the flag checks and baseline fails them.
    # validate = "<path>/validate_gate.py"  # or the target skill's checker
    # subprocess.run([sys.executable, validate, study, gate, "--flags", "<ids>"], ...)
    return {"item":"<id>", "claim":"validator --flags discriminates proposed vs baseline",
            "pass": None, "verdict":"inconclusive", "note":"wire to the target skill's validator"}

def _status(v): return 'PASS' if v.get('pass') else ('INCONCLUSIVE' if v.get('verdict')=='inconclusive' else 'FAIL')
for fn in (output_item_example, structural_item_example):
    v = fn(); verdicts[v['item']] = v
    print(f"[{_status(v)}] {v['item']}: {v['claim']}")
json.dump(verdicts, open(Path(__file__).parent/"verdicts.json","w"), indent=2)
print("SUMMARY:", {k:_status(v) for k,v in verdicts.items()})
