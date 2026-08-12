# Reset-Durability Rule

Loaded on demand by `CLAUDE.md`. Read this at the start of any long cloud session,
and before deferring/parking work, launching a long-running job, or reconciling a
container reset. Consolidates the reset-recovery discipline that was previously
scattered across `docs/cloud-transition-checklist.md`, `.claude/rules/workflow.md`,
and session field-notes.

## The rule

**Origin is the only durable store. A container-snapshot rollback can revert local
git — working tree, `.git`, *and even the `origin/<branch>` remote-tracking ref* — to
an earlier snapshot at any moment. Only what you have **pushed to origin (GitHub)**
survives. Therefore: commit **and push** after every meaningful step; a local commit
is not safe until it is pushed.**

This is not hypothetical. One cloud session (2026-07-26) absorbed **nine**
container-snapshot rollbacks; every one was recovered with zero loss *because* work
was pushed at each step. Earlier sessions saw the same (an earlier long session ×2;
cloud-transition). The single near-loss in all of them was a commit that was
**blocked from pushing by a gate** and then destroyed by a reset before it reached
origin (see § "A blocked push is not a safe checkpoint").

## Recognising a reset

Symptoms (any one): `git log -1` shows an *old* commit you know you moved past; the
working tree has reappeared "modifications"/untracked files you did not make (stale
snapshot debris); `git rev-parse origin/<branch>` disagrees with GitHub. **The local
`origin/<branch>` ref is itself stale** after a rollback — do not trust it; re-fetch.

## Recovery procedure (never force-push)

```bash
git fetch origin <branch>                     # refresh the STALE local ref from GitHub
git rev-parse --short origin/<branch>         # confirm origin still has your work
git log --oneline -3 origin/<branch>          # eyeball the real tip
git reset --hard origin/<branch>              # local -> the true tip
```

- **Never force-push to "reconcile" a reset.** After a rollback local is an *older*
  (or diverged) state; a force-push would clobber origin's good state with the stale
  snapshot — turning a survivable reset into real data loss. `reset --hard origin` is
  the only correct direction.
- **Distinguish stale debris from tracked files before deleting.** Files that show as
  *untracked* under a rollback HEAD may actually be *committed on origin* (they look
  untracked only because the rollback HEAD predates their commit). After
  `reset --hard origin`, re-check: `git status` deletions (`D`) mean you removed a
  tracked file — `git restore` it. Verify with
  `git cat-file -e origin/<branch>:<path>` before `rm`. (Measured upstream: four tracked
  result artifacts were mistaken for debris and `rm`'d, then restored.)
- Post-reset, re-establish ephemeral env the rollback wiped: `pip install -r
  requirements.lock.txt` (pin your deps so this is deterministic), `git config
  core.hooksPath .githooks`.

## A blocked push is not a safe checkpoint

The window between `git commit` and a **successful** `git push` is exactly where a
reset bites — a committed-but-unpushed change lives only in the reset-vulnerable local
`.git`. So when a push is **blocked** (a pre-push gate fails, network error, etc.):

- **Resolve the gate and push immediately**, or
- **Park the work on a scratch ref right now**: `git push origin HEAD:refs/heads/wip-<slug>`
  (a WIP branch bypasses nothing important but makes the commit durable), then fix the
  gate.
- **Do not proceed to other work** leaving the commit local-only. (2026-07-26: a
  gate-blocked G0-wiki commit was destroyed by a reset in exactly this window.)

## Long-running jobs

A reset kills in-flight compute and reverts its outputs unless they are checkpointed
and pushed. Per `.claude/rules/workflow.md`:

- Launch via the tool's own **`run_in_background: true`**, never `nohup … &` inside a
  foreground call (that child is reaped when the call returns).
- **Flush-and-resume per unit of work** (per-point/per-file) to a checkpoint, so a
  reset mid-job loses at most one unit and a relaunch re-uses completed units at zero
  recompute.
- **Exactly one live writer per checkpoint file** — to extend/re-scope, kill first,
  then relaunch; to parallelise, one output file per worker, merge at analysis time.
- **Detect a job's death by checkpoint-mtime staleness, not `pgrep`.** After a reset a
  dead run's lingering bash *wrapper* still matches `pgrep -f <cmd>`, giving a false
  "alive" signal; the true signal is the checkpoint file not advancing (and the real
  worker process — e.g. the `python` interpreter — being gone).

## Break-glass: recover un-pushed work from agent transcripts

If a reset destroys an un-pushed commit whose files a **subagent** authored, the files
are recoverable from the agent's transcript: parse
`~/.claude/projects/<project>/<session>/subagents/agent-*.jsonl`, replay each `Write`
(content) then each `Edit` (`old_string`→`new_string`, in order) whose `file_path`
matches the lost file, then re-run any idempotent normalizers (`renumber-*`, linters)
and verify against the agent's reported metrics (line/tag counts). This is a
**break-glass**, not a substitute for pushing — measured once (2026-07-26, two G0 wikis
recovered verbatim), tracked for tooling if it recurs
(`todos/2026-07-26-recover-from-transcript-helper.md`).

## Enforcement

No mechanical gate can *force* a push (the harness controls resets, not the repo). The
Stop-hook `~/.claude/stop-hook-git-check.sh` is the backstop: it flags uncommitted /
unpushed / unverified-signature changes at turn end — treat every such flag as "push
now," and after a reset resolve it by **re-syncing to origin** (above), not by
committing stale debris.

## Cross-references

- `docs/cloud-transition-checklist.md` — the original reset-recovery findings (item c)
  and the "everything committed and pushed" sign-off; `decisions/2026-07-20-cloud-bg-jobs-survive-no-reaper.md`.
- `.claude/rules/workflow.md` — `[opt:BG-RUNINBG]`, flush-and-resume, single-writer-per-checkpoint.
- `field-notes/2026-07-26-reset-recovery-and-whole-branch-merge.md` — the 9-reset session:
  blocked-push near-loss, transcript recovery, checkpoint-staleness death detection.
- `CLAUDE.md` capture conventions (`prompts/`, `todos/`, `decisions/`, `bugs/`,
  `field-notes/`) — the durable *knowledge* layer that survives resets and compaction.
