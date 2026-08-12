---
description: Keep the Anthropic prompt cache warm by self-paced /loop wake-ups
---

You are running a self-paced cache-warmer loop. Execute these steps once per firing.

**Step 0 — Stopped?** If the user has asked to stop the cache warmer (this turn or earlier in the conversation), skip Steps 1–2: do NOT run the tick (it would recreate the marker) and do NOT re-arm. Reply with a one-line stop acknowledgment and end the turn — plain text with no tool calls is deliverable.

**Step 1 — Tick.** Run this; it refreshes the liveness marker, garbage-collects markers from dead sessions (mtime older than 24 h), and prints the live cache TTL as one integer (`ttl_seconds`):

```bash
PROJ="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
TICK="$PROJ/.claude/hooks/cache-warmer-tick.sh"
[ -f "$TICK" ] || TICK="$HOME/.claude/hooks/cache-warmer-tick.sh"
bash "$TICK"
```

**Step 2 — Arm the next wakeup.** Call `ScheduleWakeup` with:

- `delaySeconds` = `max(60, ttl_seconds - 30)` — 30 s safety margin under the TTL ceiling; 60 s floor against a nonsense detector value
- `reason` = `"cache-warm — next refresh at <next-time>"`
- `prompt` = exactly `/keep-cache-warm` — the slash command re-expands to these instructions when the wakeup fires (if it ever arrives unexpanded, invoke the `keep-cache-warm` skill yourself and continue)

**Harness note (2026-07-14 — supersedes the 2.1.173 turn-terminal assumption).** On the current harness the model *is* re-invoked after a `ScheduleWakeup` call, and any final text it then writes displays normally (validated: 82/85 re-invoked, 0 answer-swallows). So a firing may end with a one-line ack, and — crucially — an answer-bearing turn may safely call `ScheduleWakeup`. This reverses the old constraint (bug 2026-06-11-03 on claude-code 2.1.173, where a `ScheduleWakeup` terminated the turn and swallowed the answer). See upstream bug 2026-07-14-03 and upstream decision 2026-07-14-01.

**User turns re-arm the wakeup (auto-extend).** A firing lost during an interactive burst is otherwise unrecoverable and kills the loop (upstream bug 2026-07-14-03). So the UserPromptSubmit hook (`cache-warmer-extend.sh`) injects a re-arm instruction on every user turn while the warmer is active: call `ScheduleWakeup` early (delay read from the marker content), then answer. Each user turn pushes the wakeup out to `now + delay`, so a firing only lands once the session goes idle and the loop can never be left with no pending wakeup. Disable via the kill switch `.claude/cache-warmer-autoextend` = `off` (falls back to idle-only firing).

**Marker.** `.claude/cache-warmer.<session-id>.active` exists while the loop runs; its mtime is the liveness signal — refreshed by the tick and by the UserPromptSubmit hook on every user prompt — that the tick's dead-session GC keys on. The marker's *content* carries the last detected TTL and re-arm delay (`ttl=… delay=…`), written by the tick and read by the extend hook so the user-turn re-arm uses the correct delay. Each tick globs the markers and removes any whose mtime is older than a 24 h window (`GC_WINDOW=86400` in `cache-warmer-tick.sh`), so a dead session's marker is auto-collected within a day; `install-cache-warmer.sh --uninstall` clears them all at once. This GC is intended behaviour: upstream bug 2026-07-10-13 defect (2) proposed deleting the sweep but was **superseded 2026-07-11** — the merge kept origin's fixed probe order `stat -c %Y || stat -f %m` (upstream bug 2026-07-10-07, upstream bug 2026-07-10-22) instead. Keep the two `stat` probes GNU-first and in separate command substitutions; do **not** collapse them back into one `$(A || B)` (that is the exact defect that made the GC silently never run).

**Stopping.** Loop until the user asks to stop; never stop on your own. To stop: delete this session's marker file and do not re-arm. The one already-pending wakeup will fire once; on that firing, Step 0 applies — acknowledge the stop, run nothing, arm nothing.
