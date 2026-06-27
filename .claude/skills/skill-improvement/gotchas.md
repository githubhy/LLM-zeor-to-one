# Gotchas — hard-won failure modes (read before improving any skill)

These are the lessons from running this process on `deep-research-survey` and
`reference-implementation-study`. In `full` mode they are binding.

1. **Lazy from day one.** Put improvement text in `addenda/<phase>.md` reached by one-line
   per-phase pointers from the start. Inlining then refactoring to lazy wastes a whole pass
   (and its own A/B). Original-mode load footprint must not grow except for the tiny selector + pointers.

2. **`NO_WRITE` in a prompt is NOT a sandbox.** Skill-execution agents (those that RUN the
   target skill) reliably write files anyway — across the two runs they created stray surveys,
   auto-created session logs (following CLAUDE.md), and once fetched real datasets/papers and
   MODIFIED a tracked MANIFEST. Only real isolation works: run them in a git worktree, or a
   namespaced sandbox dir, and prompt them to RETURN text. ALWAYS `git status` audit and use
   selective `git add` (never `-A`) before committing; surgically `rm` strays.

3. **Trust-but-verify agent results.** Agents over-report success (one claimed it "ran
   validators" it cannot run; another confabulated a checklist). Re-run any gate / check /
   metric yourself before believing it.

4. **The landscape is riddled with mis-citations.** The adversarial-verify stage caught
   misattributions, wrong-paper grafts, fabricated percentages, and
   percentage-points-as-fold-change. Cite landscape MECHANISMS, not numbers; re-verify any
   figure against a primary source before it becomes load-bearing (verify claimed benchmarks or
   model capabilities against the actual paper before using them as comparisons).

5. **Don't over-claim.** When a cheap test can't fairly decide an item (e.g. a proxy that
   isn't a faithful surrogate), mark it INCONCLUSIVE — never engineer the demo to flatter the
   claim. Report nulls straight; effects appear only when the test is genuinely hard AND the
   model is fallible enough to need the change.

6. **Collision-safe IDs.** Parallel sessions independently grab the same `bugs/`/`decisions/`
   `YYYY-MM-DD-NN` ids; this cost two renumbers. Check the INDEX for the date's max NN (or use
   a distinctive slug) before filing.

7. **Never `git clean` the runtime/pre-existing dirs.** `.venv`, `node_modules`, `_cache`,
   `__pycache__`, and pre-existing empty study dirs show up in `git clean -nd` — wiping them is
   a real hazard. Remove only the exact stray paths you created.

8. **Additive + default-off is the contract** — for ENHANCEMENTS. The target skill's baseline
   must be byte-for-byte unchanged in `original` mode; the diff should be purely additions
   (selector + pointers + addenda + optional flag-gated checks).

9. **Broken-dependency fix = rewrite, not a default-off flag.** Gotcha #8 assumes the original
   still works. When the improvement exists because the original is BROKEN (a removed API key,
   a dead service, a deleted dependency), the old default cannot remain the default — keeping a
   broken path "on" is not graceful. Rewrite the affected spine to the working approach and
   demote the broken path to an optional, capability-gated fallback (try it only if its key /
   service is present). Flag this deviation from #8 explicitly in the proposal.
