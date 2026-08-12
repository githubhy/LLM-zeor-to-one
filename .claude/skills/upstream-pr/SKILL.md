---
name: upstream-pr
description: Open a pull request from a fork to its upstream (parent) repository. Use when the user wants to send this fork's merged work upstream and the session is scoped to the fork ONLY — the GitHub MCP `create_pull_request` is denied for the upstream ("not configured for this session") and cross-owner `add_repo` fails ("cross-tier adds not supported"). Produces the ready-to-click GitHub cross-fork compare URL, a PR title/body derived from the commits, and the new-session-rooted-at-upstream alternative. Also covers the collaborator case — if the user has write access to the upstream they can self-merge the PR, push the branch direct, or root a session at the upstream.
---

# Upstream PR (fork → parent)

## The constraint this exists for

A Claude Code session is scoped to a set of repositories (usually just the fork
you are working in). Opening a PR **on the upstream** is a write to a *different*
repo, so both tool paths are blocked:

- `mcp__github__create_pull_request` with `owner: <upstream>` is **denied**:
  `Access denied: repository "<upstream>" is not configured for this session.
  Allowed repositories: <fork>`.
- `add_repo <upstream-owner>/<repo>` **fails**:
  `cross-tier adds are not supported in v1 … add a repo from the same owner as
  the existing sources`.

So the PR cannot be created with the tools from a fork-scoped session. This skill
produces everything the user needs to open it in ~2 clicks, and names the one
path that *would* let a session create it programmatically. There is also **no
"get repository parent" MCP tool** here, so a fork-scoped session cannot even
auto-detect the upstream — you must get `owner/repo` from the user.

## When to use

- The user asks to "PR / merge / send the updates to the upstream" (or names the
  parent repo) and this session is scoped to the fork.
- You have confirmed the upstream `owner/repo` (ask if unknown).

## Procedure

1. **Get the three coordinates.**
   - `FORK_OWNER` / `REPO` — from `git remote -v` (the `origin` you push to).
   - `UPSTREAM_OWNER` — the parent repo's owner (**ask the user**; cannot be read
     from a fork-scoped session).
   - `BASE` — the upstream's default branch (usually `main`); `HEAD_BRANCH` — the
     fork branch carrying the updates (usually `main` once your PRs merged there,
     or the feature branch).

2. **Emit the cross-fork compare URL** — GitHub pre-fills the PR (title, body,
   diff, "Create pull request" button) from it:

   ```
   https://github.com/<UPSTREAM_OWNER>/<REPO>/compare/<BASE>...<FORK_OWNER>:<REPO>:<HEAD_BRANCH>
   ```

   The `owner:repo:branch` head form is the unambiguous one; `owner:branch` also
   works when the repo names match.

3. **Derive a PR title + body** from the commits on `HEAD_BRANCH` not yet
   upstream. `git log --oneline origin/<BASE>..<HEAD_BRANCH>` is a good local
   proxy (it lists the fork's own recent merges); or summarize the specific
   merged PRs. Hand the user copy-paste title + body.

4. **State the scope caveat.** The compare shows *everything* that differs
   between the two repos, not only the recent work — a fork-scoped session cannot
   read the upstream to measure the divergence. Tell the user to eyeball the
   compare diff first: if the upstream is far behind, the PR is the whole fork
   divergence, not just this session's changes.

5. **Offer the programmatic alternative.** To have a Claude Code session create
   the PR itself, start a **new session rooted at the UPSTREAM repo**
   (`<UPSTREAM_OWNER>/<REPO>` as the initial source). From there,
   `create_pull_request` with `head: <FORK_OWNER>:<HEAD_BRANCH>` is in scope.

## Collaborator on the upstream

If the user has **write access** to the upstream (a collaborator/maintainer),
the endgame is simpler — but this **still does not extend a fork-scoped Claude
session's reach**. The session's repo allowlist is fixed at session start; the
user's GitHub permissions do not widen it, so the tools still cannot target the
upstream from a fork-scoped session. What their access changes is what *they*
can do, and you should offer these rather than assume an external maintainer:

- **Self-merge.** They open the compare-URL PR and **merge it themselves** — no
  maintainer round-trip.
- **Push direct (skip the fork).** From a checkout that has the upstream as a
  remote, they push the branch straight to the upstream and open a same-repo PR
  (or merge) — no fork PR at all.
- **Root a session at the upstream.** A collaborator can start a new Claude Code
  session with the upstream as the initial repo; from *that* session Claude
  creates + merges the PR programmatically (`head: <FORK_OWNER>:<HEAD_BRANCH>`).

## Do not

- **Do not claim the PR was created** — a fork-scoped session cannot create it.
  Report the URL and the denial honestly; do not fabricate success.
- **Do not `curl`/WebFetch the upstream** to check divergence or fork metadata:
  it is out of session scope, and (if private) WebFetch 404s.
- **Do not `add_repo` the upstream and stop when it errors** — the cross-tier
  error is expected; fall through to the compare-URL path.

## Worked instance

Worked shape — `<you>/<repo>` (fork) → `<upstream-owner>/<repo>`
(upstream). MCP `create_pull_request` denied; `add_repo <upstream-owner>` failed
cross-tier; handed the user
`https://github.com/<upstream-owner>/<repo>/compare/main...<you>:<repo>:main`
plus a title/body, and they opened it. Session log:
an upstream session log recording the first fork→upstream PR.
