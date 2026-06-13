#!/usr/bin/env python3
"""Per-agent token + cost breakdown from a Claude Code session transcript.

The cost/latency metric for the deep-research-survey benchmark. Adapted from
superpowers' tests/claude-code/analyze-token-usage.py, but with explicit cache
pricing (cache-create and cache-read are not billed at the full input rate).

Aggregates:
  - main thread: sum over assistant `message.usage`
  - inline subagents: per-`agentId` from `toolUseResult.usage`
(Workflow subagents live in separate transcript files; run this per file or
point it at the workflow transcript dir with --also.)

Cost model (USD per 1e6 tokens, all configurable):
  input  = uncached input_tokens            * in_rate
  cwrite = cache_creation_input_tokens       * in_rate * 1.25
  cread  = cache_read_input_tokens           * in_rate * 0.10
  output = output_tokens                     * out_rate
Defaults in_rate=3, out_rate=15 (a mid-tier estimate; override per model).
These are ESTIMATES for relative before/after comparison, not billing truth.

Usage:
  python3 analyze_tokens.py SESSION.jsonl [--in-rate 3] [--out-rate 15] [--json]
                            [--also OTHER.jsonl ...]
"""
import argparse
import json
import sys
from collections import defaultdict


def accumulate(path, agents):
    """agents: dict label -> usage accumulator. Mutates in place."""
    def acc(label):
        a = agents.setdefault(label, defaultdict(int))
        a["_msgs"] += 0
        return a
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = rec.get("type")
            msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
            if t == "assistant" and msg.get("usage"):
                u = msg["usage"]
                a = acc("main")
                a["_msgs"] += 1
                a["input"] += u.get("input_tokens", 0)
                a["output"] += u.get("output_tokens", 0)
                a["cwrite"] += u.get("cache_creation_input_tokens", 0)
                a["cread"] += u.get("cache_read_input_tokens", 0)
            tur = rec.get("toolUseResult")
            if t == "user" and isinstance(tur, dict) and tur.get("agentId") and tur.get("usage"):
                u = tur["usage"]
                label = "agent:" + str(tur["agentId"])[:8]
                a = acc(label)
                a["_msgs"] += 1
                a["input"] += u.get("input_tokens", 0)
                a["output"] += u.get("output_tokens", 0)
                a["cwrite"] += u.get("cache_creation_input_tokens", 0)
                a["cread"] += u.get("cache_read_input_tokens", 0)


def cost(a, in_rate, out_rate):
    return (a["input"] * in_rate
            + a["cwrite"] * in_rate * 1.25
            + a["cread"] * in_rate * 0.10
            + a["output"] * out_rate) / 1_000_000


def main():
    ap = argparse.ArgumentParser(description="Per-agent token + cost from a CC transcript.")
    ap.add_argument("transcript")
    ap.add_argument("--also", nargs="*", default=[], help="additional transcripts (e.g. workflow subagents)")
    ap.add_argument("--in-rate", type=float, default=3.0)
    ap.add_argument("--out-rate", type=float, default=15.0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    agents = {}
    for p in [args.transcript, *args.also]:
        accumulate(p, agents)

    rows, tot = [], defaultdict(int)
    for label, a in sorted(agents.items(), key=lambda kv: -cost(kv[1], args.in_rate, args.out_rate)):
        c = cost(a, args.in_rate, args.out_rate)
        rows.append({"agent": label, "msgs": a["_msgs"], "input": a["input"],
                     "output": a["output"], "cache_read": a["cread"],
                     "cache_create": a["cwrite"], "cost_usd": round(c, 4)})
        for k in ("input", "output", "cread", "cwrite"):
            tot[k] += a[k]
    total_cost = round(sum(r["cost_usd"] for r in rows), 4)

    if args.json:
        print(json.dumps({"rows": rows, "total_cost_usd": total_cost,
                          "totals": dict(tot)}, indent=2))
        return

    print(f"=== token + cost breakdown: {args.transcript}"
          + (f" (+{len(args.also)} more)" if args.also else ""))
    print(f"{'agent':<18}{'msgs':>6}{'input':>10}{'output':>10}{'cache_rd':>12}{'cache_wr':>12}{'cost($)':>10}")
    print("-" * 78)
    for r in rows:
        print(f"{r['agent']:<18}{r['msgs']:>6}{r['input']:>10,}{r['output']:>10,}"
              f"{r['cache_read']:>12,}{r['cache_create']:>12,}{r['cost_usd']:>10.4f}")
    print("-" * 78)
    print(f"{'TOTAL':<18}{'':>6}{tot['input']:>10,}{tot['output']:>10,}"
          f"{tot['cread']:>12,}{tot['cwrite']:>12,}{total_cost:>10.4f}")
    print(f"\nEstimated cost: {total_cost:.4f} USD (in={args.in_rate}/out={args.out_rate} per 1e6; estimate only)")


if __name__ == "__main__":
    main()
