# Launch the markdown viewer, auto-installing viewer/ dependencies on first run.
#
# Fixes the common "Error: Cannot find module 'ws'" crash, which happens when
# `node viewer/serve.js ...` is run before `cd viewer; npm install` — serve.js
# hard-requires `ws` (and uses `chokidar`/`ignore`), so a missing
# viewer/node_modules aborts startup. This wrapper installs the deps once, then
# forwards all arguments to serve.js unchanged. If no content root is supplied
# it defaults to serving surveys/, so a bare `-p <port>` invocation just works.
#
# Usage (relative paths resolve the same as serve.js, from the repo root):
#   scripts\serve-viewer.ps1                              # serves surveys/ on :3000
#   scripts\serve-viewer.ps1 -p 3500                      # serves surveys/ on :3500
#   scripts\serve-viewer.ps1 surveys/llms-for-coding -p 3500
#   scripts\serve-viewer.ps1 reports/ --allow .
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$viewerDir = Join-Path $repoRoot 'viewer'

# `ws` is the hard dependency whose absence produces the MODULE_NOT_FOUND crash;
# use it as the canary for "dependencies installed". A bare node_modules\ dir is
# not enough — a partial install can have the dir without ws.
if (-not (Test-Path (Join-Path $viewerDir 'node_modules\ws'))) {
    Write-Host 'viewer/node_modules missing - installing dependencies (one-time)...'
    Push-Location $viewerDir
    try {
        if (Test-Path (Join-Path $viewerDir 'package-lock.json')) {
            npm ci
        } else {
            npm install
        }
        if ($LASTEXITCODE -ne 0) { throw "npm install failed (exit $LASTEXITCODE)." }
    } finally {
        Pop-Location
    }
}

# Detect whether the caller already named a content root (a positional dir/file,
# --root, or --config). serve.js aborts with "no content roots" when none is
# given, so default to surveys/ for a friction-free `-p <port>` launch.
$argList = @($args)
$haveRoot = $false
for ($i = 0; $i -lt $argList.Count; $i++) {
    $a = $argList[$i]
    if ($a -eq '--root' -or $a -eq '--config') { $haveRoot = $true; $i++ }   # flag + value, provides a root
    elseif ($a -eq '-p' -or $a -eq '--port' -or $a -eq '--allow') { $i++ }   # flag + value, no root
    elseif ($a -like '-*') { }                                               # bare flag, no value
    else { $haveRoot = $true }                                               # positional dir/file = a root
}

$serveArgs = $argList
if (-not $haveRoot) {
    $surveysDir = Join-Path $repoRoot 'surveys'
    Write-Host "No content root given - defaulting to $surveysDir"
    $serveArgs = @($surveysDir) + $argList
}

# CWD is left as the caller's so any relative paths they pass resolve as documented.
$serve = Join-Path $viewerDir 'serve.js'
& node $serve @serveArgs
exit $LASTEXITCODE
