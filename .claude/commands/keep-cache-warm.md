---
description: Keep the Anthropic prompt cache warm by self-paced /loop wake-ups
---

You are running a self-paced cache-warmer loop. Execute these steps once per firing.

**Step 0 — Stopped?** If the user has asked to stop the cache warmer (this turn or earlier in the conversation), skip Steps 1–2: do NOT run the tick (it would recreate the marker) and do NOT re-arm. Reply with a one-line stop acknowledgment and end the turn — plain text with no tool calls is deliverable.

**Step 1 — Tick.** Run this; it refreshes the liveness marker, prunes dead-session markers, and prints the live cache TTL as one integer (`ttl_seconds`):

```bash
PROJ="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
TICK="$PROJ/.claude/hooks/cache-warmer-tick.sh"
[ -f "$TICK" ] || TICK="$HOME/.claude/hooks/cache-warmer-tick.sh"
bash "$TICK"
```

**Step 2 — Arm, as the turn's final action.** Call `ScheduleWakeup` with:

- `delaySeconds` = `max(60, ttl_seconds - 30)` — 30 s safety margin under the TTL ceiling; 60 s floor against a nonsense detector value
- `reason` = `"cache-warm — next refresh at <next-time>"`
- `prompt` = exactly `/keep-cache-warm` — the slash command re-expands to these instructions when the wakeup fires (if it ever arrives unexpanded, invoke the `keep-cache-warm` skill yourself and continue)

**There is no ack step (bug 2026-06-11-03, reopened).** On claude-code 2.1.173+ the harness terminates the turn at the `ScheduleWakeup` call — the model is never re-invoked after the tool result, so nothing written after the call ever gets generated, and text written before a trailing tool call is hidden as inter-tool status. A firing turn therefore ends silently on the arm call; that is expected and correct for an idle housekeeping turn. Do not write an ack before the call (it would only land in the transcript, not the screen) and do not attempt one after.

**User turns never re-arm.** For the same reason, no answer-bearing turn may contain a `ScheduleWakeup` call — arm-first kills the answer before it is generated; arm-last hides it. The UserPromptSubmit hook (`cache-warmer-extend.sh`) only touches the liveness marker silently; the wakeup armed by the last firing fires on its original schedule even while the user is active. A firing landing during an active session is cheap (the cache is already warm) and harmless.

**Marker.** `.claude/cache-warmer.<session-id>.active` exists while the loop runs; its mtime is the liveness signal (refreshed by the tick and by the hook on every user prompt) that lets the tick GC markers of dead sessions.

**Stopping.** Loop until the user asks to stop; never stop on your own. To stop: delete this session's marker file and do not re-arm. The one already-pending wakeup will fire once; on that firing, Step 0 applies — acknowledge the stop, run nothing, arm nothing.
