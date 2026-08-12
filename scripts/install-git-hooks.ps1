# Point git at the tracked hooks directory. One config setting, once per clone.
#
# This script used to copy .githooks/* into .git/hooks/. A copy is a SNAPSHOT:
# every later edit to the source silently diverged, and nothing detected it. On
# 2026-07-09 the installed copy dated from 2026-05 and ran 5 of the source's 9
# checks -- the crosslink gate (at --severity=error), the section-ownership gate
# and the depth-tier gate never ran on push at all. bugs/2026-07-09-10.
#
# `core.hooksPath` makes git read `.githooks/` directly. No copy, nothing to
# re-install after a pull, and drift is structurally impossible. The path is
# relative, so it resolves correctly inside a git worktree too.
#
# `.githooks/pre-push` additionally refuses to run unless core.hooksPath points
# at .githooks, so a clone that overrides it cannot silently execute a stale gate.

$ErrorActionPreference = 'Stop'
$repoRoot = (git rev-parse --show-toplevel).Trim()
Set-Location $repoRoot

$src = Join-Path $repoRoot '.githooks'
if (-not (Test-Path $src)) { Write-Error "Source $src not found." }

git config core.hooksPath .githooks

# A leftover copy from the old installer is dead code under core.hooksPath -- but
# it would spring back to life the moment anyone unset the config.
$gitCommon = (git rev-parse --git-common-dir).Trim()
$dst = Join-Path $gitCommon 'hooks'
Get-ChildItem -Path $src -File | ForEach-Object {
    $stale = Join-Path $dst $_.Name
    if (Test-Path $stale) {
        Remove-Item $stale -Force
        Write-Host "Removed stale copy: $stale"
    }
}

Write-Host "core.hooksPath = $(git config --get core.hooksPath)"
Write-Host 'Active hooks:'
Get-ChildItem -Path $src -File | ForEach-Object { Write-Host "  $($_.Name)" }
