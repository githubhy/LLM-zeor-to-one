#!/usr/bin/env python3
"""Behavioral assertions over a Claude Code session transcript (.jsonl).

The process-side benchmark for the `deep-research-survey` skill, modelled on
superpowers' integration tests (parse the transcript, assert behaviour) rather
than grading user-facing prose. Each check prints PASS / FAIL / WARN and the
script exits non-zero if any hard check FAILs.

Schema (verified against a live CC transcript, 2026-05-30):
  - assistant turn:   {"type":"assistant","message":{"content":[...],"usage":{...}}}
  - tool call block:  {"type":"tool_use","name":"Bash"|"Skill"|"Agent"|"Task"|"Workflow"|...,"input":{...}}
  - inline subagent:  {"type":"user","toolUseResult":{"agentId":..,"usage":{"output_tokens":N},"prompt":..,"content":[..]}}

Note on orchestration paths:
  - Classic skill (background Agent/Task): subagents appear inline as toolUseResult
    blocks in THIS transcript — silent-death detection works here.
  - Workflow tool: subagents run in a SEPARATE transcript dir; point --workflow-dir
    at it (or run assert_transcript.py per subagent .jsonl) to inspect those.

Usage:
  python3 assert_transcript.py SESSION.jsonl [--skill deep-research-survey]
                               [--survey-glob surveys/] [--json] [--max-questions 5]
"""
import argparse
import json
import re
import sys


def load(path):
    asst_turns, tool_uses, subagent_results = [], [], []
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
                asst_turns.append(rec)
            for c in (msg.get("content") or []):
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    tool_uses.append({"name": c.get("name"), "input": c.get("input") or {}})
            tur = rec.get("toolUseResult")
            if t == "user" and isinstance(tur, dict) and tur.get("agentId"):
                usage = tur.get("usage") or {}
                content = tur.get("content")
                subagent_results.append({
                    "agentId": tur.get("agentId"),
                    "output_tokens": usage.get("output_tokens", 0),
                    "has_content": bool(content),
                    "prompt": tur.get("prompt", "") or "",
                })
    return asst_turns, tool_uses, subagent_results


def _skill_uses(tool_uses, name):
    out = []
    for tu in tool_uses:
        if tu["name"] == "Skill":
            inp = tu["input"]
            if inp.get("skill") == name or inp.get("command") == name:
                out.append(tu)
    return out


def _bash_matches(tool_uses, pattern):
    rx = re.compile(pattern)
    return [tu for tu in tool_uses if tu["name"] == "Bash" and rx.search(str(tu["input"].get("command", "")))]


WRITE_VERBS = re.compile(r"write the section|draft the survey|synthesi[sz]e the|write the final|author the section", re.I)


def run_checks(args):
    asst_turns, tool_uses, subagent_results = load(args.transcript)
    checks = []  # (name, status, detail, hard)

    def add(name, status, detail, hard=True):
        checks.append((name, status, detail, hard))

    # 1. Skill invoked (or run via Workflow orchestration)
    sk = _skill_uses(tool_uses, args.skill)
    wf = [tu for tu in tool_uses if tu["name"] == "Workflow"]
    if sk:
        add("skill_invoked", "PASS", f"Skill '{args.skill}' invoked {len(sk)}x")
    elif wf:
        add("skill_invoked", "WARN", f"no direct Skill call, but {len(wf)} Workflow run(s) (orchestration path)")
    else:
        add("skill_invoked", "FAIL", f"no Skill '{args.skill}' and no Workflow call found")

    # 2. Evidence collection was actually dispatched (not all on main thread)
    agents = [tu for tu in tool_uses if tu["name"] in ("Agent", "Task")]
    n_dispatch = len(agents) + len(wf)
    add("evidence_dispatched", "PASS" if n_dispatch else "WARN",
        f"{len(agents)} Agent/Task + {len(wf)} Workflow dispatch(es)", hard=False)

    # 3. No silent agent death (inline subagents only)
    if subagent_results:
        dead = [s for s in subagent_results if s["output_tokens"] == 0 or not s["has_content"]]
        rate = len(dead) / len(subagent_results)
        add("no_silent_agent_death",
            "PASS" if not dead else "FAIL",
            f"{len(dead)}/{len(subagent_results)} inline subagents produced no output "
            f"(silent-death rate {rate:.0%})")
    else:
        add("no_silent_agent_death", "WARN",
            "no inline subagents in this transcript (Workflow path? inspect --workflow-dir)", hard=False)

    # 4. Citation gate ran (the skill's hard gate / proposal P0-2's hardened form)
    cite = (_skill_uses(tool_uses, "citation-audit")
            or _bash_matches(tool_uses, r"check-citation-sources|validate-refs|citation"))
    add("citation_gate_invoked", "PASS" if cite else "FAIL",
        "citation-audit skill or check-citation-sources/validate-refs invoked" if cite
        else "no citation gate detected before completion")

    # 5. A survey deliverable was written
    survey_writes = [tu for tu in tool_uses if tu["name"] in ("Write", "Edit")
                     and args.survey_glob in str(tu["input"].get("file_path", ""))]
    add("survey_written", "PASS" if survey_writes else "WARN",
        f"{len(survey_writes)} write/edit under '{args.survey_glob}'"
        if survey_writes else f"no deliverable under '{args.survey_glob}' (proposal/prompt mode?)",
        hard=False)

    # 6. Agent-sizing discipline (heuristic, soft): question marks as a question proxy
    oversized = []
    for a in agents:
        prompt = str(a["input"].get("prompt", ""))
        q = prompt.count("?")
        if q > args.max_questions:
            oversized.append(q)
    add("agent_sizing", "PASS" if not oversized else "WARN",
        f"all evidence agents <= {args.max_questions} questions" if not oversized
        else f"{len(oversized)} agent(s) exceed {args.max_questions} questions (~{oversized})",
        hard=False)

    # 7. Synthesis stayed on main thread (heuristic, soft)
    writer_agents = [s for s in subagent_results if WRITE_VERBS.search(s["prompt"])]
    add("synthesis_on_main_thread", "PASS" if not writer_agents else "WARN",
        "no subagent prompt looks like section writing" if not writer_agents
        else f"{len(writer_agents)} subagent prompt(s) look like synthesis (should be main-thread)",
        hard=False)

    return checks, {"main_turns": len(asst_turns), "tool_calls": len(tool_uses),
                    "inline_subagents": len(subagent_results)}


def main():
    ap = argparse.ArgumentParser(description="Behavioral assertions over a CC session transcript.")
    ap.add_argument("transcript")
    ap.add_argument("--skill", default="deep-research-survey")
    ap.add_argument("--survey-glob", default="surveys/")
    ap.add_argument("--max-questions", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    checks, stats = run_checks(args)
    hard_fail = any(s == "FAIL" and hard for _, s, _, hard in checks)

    if args.json:
        print(json.dumps({
            "transcript": args.transcript,
            "stats": stats,
            "checks": [{"name": n, "status": s, "detail": d, "hard": h} for n, s, d, h in checks],
            "passed": not hard_fail,
        }, indent=2))
    else:
        glyph = {"PASS": "  [PASS]", "FAIL": "  [FAIL]", "WARN": "  [warn]"}
        print(f"=== deep-research-survey transcript assertions: {args.transcript}")
        print(f"    main turns={stats['main_turns']} tool calls={stats['tool_calls']} "
              f"inline subagents={stats['inline_subagents']}\n")
        for n, s, d, _ in checks:
            print(f"{glyph[s]} {n}: {d}")
        print(f"\nSTATUS: {'PASSED' if not hard_fail else 'FAILED'}")
    sys.exit(1 if hard_fail else 0)


if __name__ == "__main__":
    main()
