# Install tracked git hooks into .git/hooks/.
# Re-run after pulling new hook templates.

$ErrorActionPreference = 'Stop'
$repoRoot = (git rev-parse --show-toplevel).Trim()
$src = Join-Path $repoRoot '.githooks'
# Use --git-common-dir so the hooks land in the main repo's .git/hooks/
# even when run from inside a git worktree.
$gitCommon = (git rev-parse --git-common-dir).Trim()
$dst = Join-Path $gitCommon 'hooks'

if (-not (Test-Path $src)) {
    Write-Error "Source $src not found."
}

Get-ChildItem -Path $src -File | ForEach-Object {
    $target = Join-Path $dst $_.Name
    Copy-Item -Path $_.FullName -Destination $target -Force
    Write-Host "Installed: .git/hooks/$($_.Name)"
}

Write-Host "Done. Hooks active for this clone."
