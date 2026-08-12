#!/usr/bin/env python3
"""PreToolUse guard — block a FOREGROUND Bash call that backgrounds a long job.

Launching a long job with a trailing `&` / `nohup` / `setsid` / `disown` inside a
*foreground* tool call is the BG-RUNINBG anti-pattern (`.claude/rules/workflow.md`):
the harness reaps the call's child processes when the call returns, so the detached
job is killed the moment the launching call completes. The durable mechanism is the
Bash tool's own `run_in_background: true`. This rule was documented and still recurred
(N>=6 across upstream sessions: a long dependency install, two sweeps, and a
reduced-precision phase), so it is now a gate rather than only a rule.

Contract (Claude Code PreToolUse):
  - stdin  : JSON {tool_name, tool_input:{command, run_in_background, ...}, ...}
  - exit 0 : allow (optionally warn on stderr)
  - exit 2 : BLOCK — stderr is fed back to the model as the reason

Severity toggle: `.claude/foreground-bg-severity` in {off | warn | error}, default `error`.
  off  -> no-op;  warn -> stderr advisory but ALLOW (does not prevent the reap);
  error-> BLOCK (the only severity that actually prevents the bug).

FAILS OPEN: any parse/internal error allows the call. A guard bug must never block work.
Scoped to Bash only — PowerShell's `&` is the call operator, not backgrounding, so a
`&` detector there would false-positive massively (out of scope by design).
"""
import json
import os
import re
import sys


def detect(cmd: str):
    """Return a short reason string if `cmd` backgrounds a job, else None.

    High precision by construction: quoted spans are removed first (a literal `&`
    in a string / URL / quoted heredoc line is not job control), then `&&` and fd
    redirects are removed, so a *remaining* `&` can only be the job-control operator.
    We flag it only when it sits at a command-terminating position (end / `;` / `)` /
    `}` / newline) or before a loop/if terminator — which excludes bitwise-and in
    arithmetic (`$((a & b))`, the `&` is followed by an operand, not a terminator).
    """
    s = cmd
    # 1) remove quoted spans so a literal & inside them is never mistaken for job control
    s = re.sub(r"'[^']*'", " ", s)
    s = re.sub(r'"[^"]*"', " ", s)
    s = re.sub(r"`[^`]*`", " ", s)
    # 1b) strip trailing `#` comments (a `#` at line-start or after whitespace, to EOL).
    #     `$#` and `${#x}` are untouched (their `#` is not whitespace-preceded). This also
    #     exposes a `&` that a comment would otherwise hide: `cmd &  # note` -> `cmd &`.
    s = re.sub(r"(?m)(^|\s)#.*$", r"\1", s)
    # 2) explicit detach builtins/wrappers (workflow.md lists all three)
    m = re.search(r"(?<![\w./-])(nohup|setsid|disown)(?![\w-])", s)
    if m:
        return "detached with `%s`" % m.group(1)
    # 3) strip logical-AND and every fd-redirect form so only job-control & remains
    s = s.replace("&&", "  ")
    s = re.sub(r"[0-9]*>&[0-9-]*", " ", s)   # 2>&1, >&2, 1>&-
    s = re.sub(r"&>>?", " ", s)              # &>file, &>>file
    # 4) a remaining & at a command-terminating position => backgrounding
    if re.search(r"&\s*(?:;|\)|\}|\n|$)", s):
        return "trailing `&` backgrounds the job"
    if re.search(r"&\s*(?:done|fi|esac)\b", s):
        return "`&` inside a loop/if body backgrounds the job"
    return None


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        sys.exit(0)  # fail open

    if not isinstance(data, dict) or data.get("tool_name") != "Bash":
        sys.exit(0)
    ti = data.get("tool_input") or {}
    if not isinstance(ti, dict):
        sys.exit(0)
    # already using the correct mechanism -> allow (even if it redundantly has &)
    if ti.get("run_in_background") is True:
        sys.exit(0)
    cmd = ti.get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        sys.exit(0)

    proj = os.environ.get("CLAUDE_PROJECT_DIR") or "."
    try:
        with open(os.path.join(proj, ".claude", "foreground-bg-severity"), encoding="utf-8") as f:
            severity = f.read().strip().lower() or "error"
    except Exception:
        severity = "error"
    if severity == "off":
        sys.exit(0)

    try:
        reason = detect(cmd)
    except Exception:
        sys.exit(0)  # fail open on any detector error
    if not reason:
        sys.exit(0)

    msg = (
        "[foreground-background guard] %s.\n"
        "This backgrounds a job inside a FOREGROUND Bash call; the harness reaps the "
        "call's child processes when it returns, so the job is killed on return "
        "(bug class: .claude/rules/workflow.md BG-RUNINBG, recurred N>=6 across sessions).\n"
        "FIX: relaunch with the Bash tool's own `run_in_background: true` and remove the "
        "`&`/nohup/setsid/disown. Design the driver to flush+resume per unit of work so a "
        "relaunch recomputes nothing.\n"
        "If this is a deliberate short-lived server-and-kill within one call, set "
        "`.claude/foreground-bg-severity` to `off` (or `warn`) to bypass the gate."
    ) % reason

    if severity == "warn":
        sys.stderr.write("WARNING: " + msg + "\n")
        sys.exit(0)  # advisory only — does NOT prevent the reap
    # severity == "error" (default): block
    sys.stderr.write(msg + "\n")
    sys.exit(2)


if __name__ == "__main__":
    main()
