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


HEREDOC = re.compile(r"<<-?\s*'?\"?(\w+)'?\"?[^\n]*\n.*?\n\1\b", re.S)


def strip_heredocs(cmd: str) -> str:
    """Remove `<<'X' ... X` bodies: a heredoc body is DATA, not commands.

    A script that WRITES `foo &` or a `pgrep -f` line into a file is not running either.
    Both detectors need this and both learned it the same way -- by firing on a heredoc in
    this session's own work, the pgrep one on its own test harness and the `&` one on a
    docstring containing matrix column separators.
    """
    return HEREDOC.sub(" ", cmd)


def detect(cmd: str):
    """Return a short reason string if `cmd` backgrounds a job, else None.

    High precision by construction: quoted spans are removed first (a literal `&`
    in a string / URL / quoted heredoc line is not job control), then `&&` and fd
    redirects are removed, so a *remaining* `&` can only be the job-control operator.
    We flag it only when it sits at a command-terminating position (end / `;` / `)` /
    `}` / newline) or before a loop/if terminator — which excludes bitwise-and in
    arithmetic (`$((a & b))`, the `&` is followed by an operand, not a terminator).
    """
    s = strip_heredocs(cmd)
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


PGREP_F = re.compile(r"(?<![\w./-])pgrep\s+(?:-\w*\s+)*-\w*f\w*\s+(\S+)")


def detect_pgrep_selfmatch(cmd: str):
    """Return a reason if `cmd` runs `pgrep -f <literal>` that will match its OWN shell.

    `pgrep -f PATTERN` matches against full command lines, and the shell running it has
    PATTERN on its own command line -- so it ALWAYS matches itself unless the pattern is
    written so it cannot, conventionally by bracketing one character (`[g]ithooks/...`).

    Two failure modes, both measured in this repo:
      * `until ! pgrep -f "x"; do sleep 5; done` never exits. One such waiter sat for
        3.7 hours on 2 seconds of CPU, holding a background slot and deferring a goal
        check-in by 160 minutes.
      * a one-shot `pgrep -f "x"` reads as "the job is running" when nothing is, which was
        reported to the user as fact twice in one session.

    High precision: only flags a `-f` pgrep whose pattern contains no `[` (the bracket
    trick) and is not a variable expansion (whose value we cannot see).
    """
    # A heredoc body is DATA, not commands: a script that WRITES this pattern into a file
    # is not running it. Found immediately -- the guard blocked its own test harness, whose
    # cases are written through a heredoc. Strip `<<'X' ... X` and `<<X ... X` bodies first.
    scan = strip_heredocs(cmd)
    for m in PGREP_F.finditer(scan):
        pat = m.group(1).strip().strip("'\"")   # the quotes are shell syntax, not pattern
        if not pat or pat.startswith("$") or pat.startswith("-"):
            continue                      # a variable's value is not knowable here
        if "[" in pat:
            continue                      # bracket trick: cannot match itself
        looped = re.search(r"\b(?:until|while)\b[^\n;]{0,200}?" + re.escape(m.group(0)[:24]),
                           scan) is not None
        return ("`pgrep -f %s` matches its own shell, so this loop never exits" % pat
                if looped else
                "`pgrep -f %s` matches its own shell and always reports a match" % pat)
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
    cmd = ti.get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        sys.exit(0)
    # `run_in_background: true` is the correct mechanism for the & class, so that detector
    # is skipped below -- but a self-matching pgrep is if anything WORSE in the background,
    # where the deadlock is invisible until a check-in notices it. So it is checked first,
    # for both kinds of call.
    backgrounded = ti.get("run_in_background") is True

    proj = os.environ.get("CLAUDE_PROJECT_DIR") or "."
    try:
        with open(os.path.join(proj, ".claude", "foreground-bg-severity"), encoding="utf-8") as f:
            severity = f.read().strip().lower() or "error"
    except Exception:
        severity = "error"
    if severity == "off":
        sys.exit(0)

    # --- self-matching pgrep (its own severity toggle; different failure mode) ---
    try:
        pg = detect_pgrep_selfmatch(cmd)
    except Exception:
        pg = None                          # fail open
    if pg:
        try:
            with open(os.path.join(proj, ".claude", "pgrep-selfmatch-severity"),
                      encoding="utf-8") as f:
                pgsev = f.read().strip().lower() or "error"
        except Exception:
            pgsev = "error"
        if pgsev != "off":
            pmsg = (
                "[pgrep self-match guard] %s.\n"
                "`pgrep -f` matches FULL COMMAND LINES, and the shell running it carries "
                "the pattern on its own -- so it matches itself. An `until ! pgrep -f ...` "
                "waiter therefore never exits (measured: 3.7 h on 2 s of CPU, holding a "
                "background slot), and a one-shot check reads as \"still running\" when "
                "nothing is.\n"
                "FIX: bracket one character -- `pgrep -f \"[g]ithooks/pre-push\"` -- or use "
                "`python3 tools/job_status.py`, which reads CPU accumulation and watch-path "
                "freshness instead of a name match (.claude/rules/workflow.md BG-REPORT).\n"
                "Bound every wait loop regardless: an unbounded `until` has no failure mode "
                "that reports itself.\n"
                "Toggle: `.claude/pgrep-selfmatch-severity` in {off | warn | error}."
            ) % pg
            if pgsev == "warn":
                sys.stderr.write("WARNING: " + pmsg + "\n")
            else:
                sys.stderr.write(pmsg + "\n")
                sys.exit(2)

    if backgrounded:
        sys.exit(0)      # correct mechanism for the & class; nothing left to check

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
