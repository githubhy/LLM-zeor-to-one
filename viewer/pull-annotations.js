'use strict';
const fs = require('fs');
const path = require('path');
const { mergeDocs } = require('./lib/annotation-merge');

async function pullAnnotations({ base, token, sidecarDir, fetch: f }) {
  const fetchImpl = f || fetch;
  const auth = token ? { Authorization: 'Bearer ' + token } : {};
  const root = base.replace(/\/$/, '');
  const manRes = await fetchImpl(`${root}/api/annotations-manifest`, { headers: auth });
  const manifest = manRes.ok ? await manRes.json() : { entries: [] };
  const files = Array.isArray(manifest.files)
    ? manifest.files
    : [...new Set((manifest.entries || []).map((e) => e.file))];
  let filesChanged = 0, highlightsAdded = 0, tombstonesApplied = 0;
  for (const file of files) {
    const res = await fetchImpl(`${root}/api/annotations/${encodeURIComponent(file)}`, { headers: auth });
    if (!res.ok) continue;
    const remote = await res.json();
    const dest = path.join(sidecarDir, `${file}.json`);
    let local = { version: 1, file, highlights: [] };
    if (fs.existsSync(dest)) { try { local = JSON.parse(fs.readFileSync(dest, 'utf8')); } catch { /* keep default */ } }
    const merged = mergeDocs(local, remote, file);
    const before = JSON.stringify(local), after = JSON.stringify(merged);
    if (before !== after) {
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      fs.writeFileSync(dest, JSON.stringify(merged, null, 2));
      filesChanged++;
      const localById = new Map((local.highlights || []).map((h) => [h.id, h]));
      for (const h of merged.highlights) {
        const prior = localById.get(h.id);
        if (!prior && !h.deleted) highlightsAdded++;
        if (h.deleted && !(prior && prior.deleted)) tombstonesApplied++;
      }
    }
  }
  return { filesChanged, highlightsAdded, tombstonesApplied };
}

// Recursively list sidecar file-keys (relative path minus `.json`) under sidecarDir.
function listSidecarFiles(sidecarDir) {
  const out = [];
  function walk(dir, prefix) {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const rel = prefix ? `${prefix}/${e.name}` : e.name;
      if (e.isDirectory()) walk(path.join(dir, e.name), rel);
      else if (e.name.endsWith('.json')) out.push(rel.slice(0, -'.json'.length));
    }
  }
  if (fs.existsSync(sidecarDir)) walk(sidecarDir, '');
  return out;
}

// Desktop → cloud seed/refresh: PUT each local sidecar to the live API (the
// server merges, so re-running is safe). Mirror of pullAnnotations.
async function pushAnnotations({ base, token, sidecarDir, fetch: f }) {
  const fetchImpl = f || fetch;
  const headers = Object.assign({ 'Content-Type': 'application/json; charset=utf-8' }, token ? { Authorization: 'Bearer ' + token } : {});
  const root = base.replace(/\/$/, '');
  let filesPushed = 0, highlightsPushed = 0;
  for (const file of listSidecarFiles(sidecarDir)) {
    let doc;
    try { doc = JSON.parse(fs.readFileSync(path.join(sidecarDir, `${file}.json`), 'utf8')); } catch { continue; }
    const res = await fetchImpl(`${root}/api/annotations/${encodeURIComponent(file)}`, { method: 'PUT', headers, body: JSON.stringify(doc) });
    if (res.ok) { filesPushed++; highlightsPushed += (doc.highlights || []).length; }
  }
  return { filesPushed, highlightsPushed };
}

function main(argv) {
  const args = argv.slice(2);
  const direction = (args[0] === 'push' || args[0] === 'pull') ? args.shift() : 'pull';
  let base = null, token = process.env.VIEWER_TOKEN || null, target = null;
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--base') base = args[++i];
    else if (args[i] === '--token') token = args[++i];
    else if (args[i] === '--target') target = args[++i];
  }
  if (!base || !target) { console.error('usage: node pull-annotations.js [pull|push] --base <url> --target <survey-dir> [--token <tok>]'); process.exit(2); }
  const sidecarDir = path.join(path.resolve(target), '.viewer-highlights');
  if (direction === 'push') {
    return pushAnnotations({ base, token, sidecarDir }).then((s) => {
      console.log(`pushed: ${s.filesPushed} files, ${s.highlightsPushed} highlights`);
    });
  }
  return pullAnnotations({ base, token, sidecarDir }).then((s) => {
    console.log(`pulled: ${s.filesChanged} files changed, +${s.highlightsAdded} highlights, ${s.tombstonesApplied} tombstones`);
  });
}

if (require.main === module) main(process.argv);
module.exports = { pullAnnotations, pushAnnotations, listSidecarFiles, main };
