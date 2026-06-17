#!/usr/bin/env node
'use strict';

/**
 * gen-root-manifest.js — generate (or --check) a checked-in snapshot of the
 * multi-root viewer's served file set (Plan 2026-06-14 Phase 3.4).
 *
 * serve recomputes the file list live and publish bakes it fresh, so the
 * pipeline never depends on this file — it is an OPTIONAL drift detector: a
 * checked-in `viewer.manifest.json` + a `--check` gate (suitable for pre-push/CI,
 * but not wired into any hook yet) flags when the served content set changes
 * (files added/removed/renamed, a root added, or a .viewerignore edit) so a
 * reviewer notices.
 *
 * Usage:
 *   node viewer/tools/gen-root-manifest.js              # write viewer.manifest.json
 *   node viewer/tools/gen-root-manifest.js --check      # exit 1 on drift (no write)
 *   node viewer/tools/gen-root-manifest.js --config <f> --out <f>
 */

const fs = require('fs');
const path = require('path');
const { listMarkdownFilesMultiRoot, buildIgnoreMatcher } = require('../lib/content-source');

const SCHEMA = 1;

function parseArgs(argv) {
  const out = { config: null, out: null, check: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--config' && argv[i + 1]) { out.config = argv[++i]; }
    else if (argv[i] === '--out' && argv[i + 1]) { out.out = argv[++i]; }
    else if (argv[i] === '--check') { out.check = true; }
  }
  return out;
}

// Discover viewer.content.json (explicit path, or upward walk from cwd).
function findConfig(explicit) {
  if (explicit) {
    const f = path.resolve(explicit);
    if (!fs.existsSync(f)) { console.error(`config not found: ${f}`); process.exit(2); }
    return f;
  }
  let d = process.cwd();
  for (;;) {
    const cand = path.join(d, 'viewer.content.json');
    if (fs.existsSync(cand)) return cand;
    const parent = path.dirname(d);
    if (parent === d) return null;
    d = parent;
  }
}

function resolveRoots(cfg, baseDir) {
  if (!cfg || !Array.isArray(cfg.roots) || !cfg.roots.length) {
    console.error('config has no roots[]'); process.exit(2);
  }
  const seen = new Set();
  return cfg.roots.map((r) => {
    const absPath = path.resolve(baseDir, r.path);
    if (!fs.existsSync(absPath)) { console.error(`config root not found: ${absPath}`); process.exit(2); }
    const id = r.id || path.basename(absPath);
    if (seen.has(id)) { console.error(`duplicate root id "${id}"`); process.exit(2); }
    seen.add(id);
    return { id, absPath, label: r.label || id };
  });
}

// Pure core: compute the manifest from a resolved config path. Exported for tests.
function generateManifest(configPath) {
  const baseDir = path.dirname(configPath);
  const cfg = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  const roots = resolveRoots(cfg, baseDir);
  // Match serve.js / publish.js EXACTLY (they hardcode `<repoRoot>/.viewerignore`
  // and do NOT honor cfg.ignoreFile) so this drift detector can never disagree
  // with the actually-served set. For the canonical config baseDir === repoRoot.
  const ignore = buildIgnoreMatcher({ projectIgnorePath: path.join(baseDir, '.viewerignore') });
  const files = listMarkdownFilesMultiRoot(roots, { ignore });
  return {
    manifest: { schema: SCHEMA, roots: roots.map((r) => ({ id: r.id, label: r.label })), files },
    outPath: path.join(baseDir, 'viewer.manifest.json'),
  };
}

function serialize(manifest) { return JSON.stringify(manifest, null, 2) + '\n'; }

function build() {
  const configPath = findConfig(parseArgs(process.argv.slice(2)).config);
  if (!configPath) { console.error('no viewer.content.json found (pass --config)'); process.exit(2); }
  return generateManifest(configPath);
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const { manifest, outPath: defaultOut } = build();
  const outPath = args.out ? path.resolve(args.out) : defaultOut;
  const serialized = serialize(manifest);

  if (args.check) {
    if (!fs.existsSync(outPath)) {
      console.error(`[gen-root-manifest] --check: ${path.basename(outPath)} missing; run without --check to create it.`);
      process.exit(1);
    }
    const current = fs.readFileSync(outPath, 'utf8');
    if (current !== serialized) {
      console.error(`[gen-root-manifest] --check: DRIFT — the served file set changed. Re-run \`node viewer/tools/gen-root-manifest.js\` and commit ${path.basename(outPath)}.`);
      process.exit(1);
    }
    console.log(`[gen-root-manifest] --check: clean (${manifest.files.length} files, ${manifest.roots.length} roots).`);
    return;
  }

  fs.writeFileSync(outPath, serialized, 'utf8');
  console.log(`[gen-root-manifest] wrote ${path.basename(outPath)} (${manifest.files.length} files, ${manifest.roots.length} roots).`);
}

if (require.main === module) main();

module.exports = { build, generateManifest, serialize, parseArgs, resolveRoots };
