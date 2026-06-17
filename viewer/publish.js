'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const {
  listMarkdownFiles, listMarkdownFilesMultiRoot, rootForFile,
  buildManifest, computeGitInfo, buildIgnoreMatcher,
} = require('./lib/content-source');

// Recursively copy a directory tree src → dest.
function copyDir(src, dest) {
  if (typeof fs.cpSync === 'function') {
    fs.cpSync(src, dest, { recursive: true });
  } else {
    fs.mkdirSync(dest, { recursive: true });
    for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
      const s = path.join(src, entry.name);
      const d = path.join(dest, entry.name);
      if (entry.isDirectory()) copyDir(s, d);
      else fs.copyFileSync(s, d);
    }
  }
}

function copyFile(src, dest) { fs.mkdirSync(path.dirname(dest), { recursive: true }); fs.copyFileSync(src, dest); }

// Collect local image paths referenced by markdown (![..](path) and <img src=..>),
// skipping remote (http/https) and data: URIs.
function referencedAssets(md) {
  const out = new Set();
  const re = /!\[[^\]]*\]\(([^)\s]+)\)|<img[^>]+src=["']([^"']+)["']/g;
  let m;
  while ((m = re.exec(md))) {
    const p = m[1] || m[2];
    if (p && !/^https?:|^data:/i.test(p)) out.add(p);
  }
  return [...out];
}

function buildBundle({ roots, outDir, version, gitInfo, ignore }) {
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(outDir, { recursive: true });

  const isMulti = !(roots.length === 1 && roots[0].id === '');
  // Namespaced file list. Single-root (id='', the default `--target surveys`
  // deploy) is STRICTLY byte-identical: NO ignore matcher, legacy skip set only
  // (decision 2026-06-14-03). honorRootOrderJson:true keeps the order.json
  // short-circuit. The .viewerignore noise-pruning is a multi-root capability.
  const files = isMulti
    ? listMarkdownFilesMultiRoot(roots, { ignore })
    : listMarkdownFiles(roots[0].absPath, { honorRootOrderJson: true });

  // Bake a doc-referenced asset at the SAME path the browser requests:
  // fixRelativePaths() rewrites a relative `src` to `/<docDir>/<src>`, so the
  // dest is dirname(namespaced id) joined with the (normalized) asset path.
  // Byte-identical to the old `path.relative(targetDir, abs)` for a single
  // root; resolves a cross-root asset under another root correctly.
  function bakeAsset(nsDocId, docRealDir, asset) {
    if (/^https?:|^data:/i.test(asset) || asset.startsWith('/')) return;
    const absSrc = path.resolve(docRealDir, asset);
    if (!fs.existsSync(absSrc) || !fs.statSync(absSrc).isFile()) return;
    const destRel = path.posix.normalize(path.posix.join(path.posix.dirname(nsDocId), asset));
    if (destRel.startsWith('..') || path.isAbsolute(destRel)) return; // can't escape dist/
    copyFile(absSrc, path.join(outDir, destRel));
  }

  for (const nsRel of files) {
    const m = rootForFile(roots, nsRel);
    const src = path.join(m.root.absPath, m.rel);
    const md = fs.readFileSync(src, 'utf8');
    copyFile(src, path.join(outDir, 'content', nsRel));
    for (const asset of referencedAssets(md)) bakeAsset(nsRel, path.dirname(src), asset);
  }

  fs.writeFileSync(path.join(outDir, 'files.json'),
    JSON.stringify({
      schema: 2, files, roots: roots.map((r) => ({ id: r.id, label: r.label })),
      defaultFile: null, version,
    }, null, 2));
  fs.writeFileSync(path.join(outDir, 'git-info.json'), JSON.stringify(gitInfo, null, 2));

  // Per-root sidecars → dist/annotations/<namespaced-rel>.json (no orphaning).
  for (const nsRel of files) {
    const m = rootForFile(roots, nsRel);
    const sc = path.join(m.root.absPath, '.viewer-highlights', `${m.rel}.json`);
    if (fs.existsSync(sc)) copyFile(sc, path.join(outDir, 'annotations', `${nsRel}.json`));
  }

  // Highlights manifest. Single-root keeps the byte-identical global build; the
  // multi-root form re-namespaces each root's entries.
  let manifest;
  if (isMulti) {
    const entries = [];
    for (const r of roots) {
      for (const e of buildManifest(r.absPath, null, { ignore }).entries) {
        e.file = r.id === '' ? e.file : `${r.id}/${e.file}`;
        entries.push(e);
      }
    }
    manifest = { entries };
  } else {
    manifest = buildManifest(roots[0].absPath, null);
  }
  fs.writeFileSync(path.join(outDir, 'annotations-manifest.json'), JSON.stringify(manifest, null, 2));

  return { fileCount: files.length };
}

// CDN URL → local vendor path replacement map.
const CDN_REPLACEMENTS = [
  ['https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.css',                         'vendor/katex.min.css'],
  ['https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.js',                          'vendor/katex.min.js'],
  ['https://cdn.jsdelivr.net/npm/markdown-it@14.1.0/dist/markdown-it.min.js',               'vendor/markdown-it.min.js'],
  ['https://cdn.jsdelivr.net/npm/markdown-it-texmath@1.0.0/texmath.min.js',                 'vendor/texmath.min.js'],
  ['https://cdn.jsdelivr.net/npm/markdown-it-texmath@1.0.0/css/texmath.min.css',            'vendor/texmath.min.css'],
  ['https://cdn.jsdelivr.net/npm/markdown-it-mark@4.0.0/dist/markdown-it-mark.min.js',      'vendor/markdown-it-mark.min.js'],
  ['https://cdn.jsdelivr.net/npm/markdown-it-footnote@4.0.0/dist/markdown-it-footnote.min.js', 'vendor/markdown-it-footnote.min.js'],
  ['https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js',                       'vendor/mermaid.min.js'],
];

function buildHtmlAndAssets({ outDir, version }) {
  const viewerDir = __dirname;

  // Copy client JS, CSS, and lib/ into outDir.
  copyFile(path.join(viewerDir, 'viewer.js'), path.join(outDir, 'viewer.js'));
  copyFile(path.join(viewerDir, 'style.css'),  path.join(outDir, 'style.css'));
  copyDir(path.join(viewerDir, 'lib'), path.join(outDir, 'lib'));

  // Copy vendor/ (including vendor/fonts/) into outDir/vendor.
  copyDir(path.join(viewerDir, 'vendor'), path.join(outDir, 'vendor'));

  // PWA manifest.
  copyFile(path.join(viewerDir, 'manifest.webmanifest'), path.join(outDir, 'manifest.webmanifest'));

  // PWA app icons — regenerate deterministically so dist/ works on a fresh checkout.
  require('./tools/make-icons').writeAll(path.join(outDir, 'icons'));

  // Cloudflare Pages Functions + wrangler config (Plan 03) — makes dist/ deployable.
  // functions/ must sit beside dist/lib/ so the adapters' `../lib/cloud-api.js`
  // imports resolve (dist/functions/* -> dist/lib/*).
  const cfDir = path.join(viewerDir, 'cloudflare');
  if (fs.existsSync(path.join(cfDir, 'functions'))) copyDir(path.join(cfDir, 'functions'), path.join(outDir, 'functions'));
  if (fs.existsSync(path.join(cfDir, 'wrangler.toml'))) copyFile(path.join(cfDir, 'wrangler.toml'), path.join(outDir, 'wrangler.toml'));

  // Service worker — copy sw.js to bundle root (scope = .) and sw-runtime.js
  // under lib/ (already covered by the copyDir above, but copy explicitly so
  // the file is present even if the copyDir ran before sw-runtime.js existed).
  copyFile(path.join(viewerDir, 'sw.js'), path.join(outDir, 'sw.js'));
  copyFile(path.join(viewerDir, 'lib', 'sw-runtime.js'), path.join(outDir, 'lib', 'sw-runtime.js'));

  // Build the precache list: static assets that constitute the app shell +
  // vendor bundle.  Paths are root-relative (no leading slash) so they match
  // the SW's fetch event req.url pathnames after stripping the origin.
  const precache = [];
  // Fixed app-shell files.
  for (const f of ['index.html', 'viewer.js', 'style.css', 'manifest.webmanifest', 'files.json']) {
    precache.push(f);
  }
  // vendor/** (recursive — includes fonts/*.woff2).
  (function collectDir(dir, prefix) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const rel = prefix ? prefix + '/' + entry.name : entry.name;
      if (entry.isDirectory()) collectDir(path.join(dir, entry.name), rel);
      else precache.push(rel);
    }
  }(path.join(outDir, 'vendor'), 'vendor'));
  // lib/*.js (flat — sw-runtime.js, backend.js, etc.).
  for (const entry of fs.readdirSync(path.join(outDir, 'lib'), { withFileTypes: true })) {
    if (!entry.isDirectory() && entry.name.endsWith('.js')) precache.push('lib/' + entry.name);
  }
  // icons/* (flat).
  for (const entry of fs.readdirSync(path.join(outDir, 'icons'), { withFileTypes: true })) {
    if (!entry.isDirectory()) precache.push('icons/' + entry.name);
  }

  // Prepend version + precache declarations to dist/sw.js.
  const swDest = path.join(outDir, 'sw.js');
  const swBody = fs.readFileSync(swDest, 'utf8');
  const swHeader = `self.__VERSION=${JSON.stringify(version)};self.__PRECACHE=${JSON.stringify(precache)};\n`;
  fs.writeFileSync(swDest, swHeader + swBody, 'utf8');

  // Produce patched index.html.
  let html = fs.readFileSync(path.join(viewerDir, 'index.html'), 'utf8');
  for (const [cdn, local] of CDN_REPLACEMENTS) {
    html = html.split(cdn).join(local);
  }

  // Sanity check: no CDN references must remain.
  if (html.includes('cdn.jsdelivr.net')) {
    throw new Error('buildHtmlAndAssets: cdn.jsdelivr.net still present in output index.html after replacements');
  }

  // Inject VIEWER_CONFIG immediately before </head>.
  const config = `\n  <script>window.VIEWER_CONFIG = ${JSON.stringify({ backend: 'cloud', base: '.', version })};</script>\n`;
  html = html.replace('</head>', config + '</head>');

  fs.writeFileSync(path.join(outDir, 'index.html'), html, 'utf8');
}

// Build a Root from a "path" or "path:Label" spec. withId=false yields the
// single-root compat id='' (no namespace prefix in dist/content/).
function mkRoot(spec, withId, repoRoot) {
  let p = spec, label = null;
  const ci = spec.lastIndexOf(':');
  if (ci > 1 && !/[\\/]/.test(spec.slice(ci + 1))) { p = spec.slice(0, ci); label = spec.slice(ci + 1); }
  const absPath = path.isAbsolute(p) ? p : path.resolve(repoRoot, p);
  const id = withId ? path.basename(absPath) : '';
  return { id, absPath, label: label || id };
}

function main() {
  const args = process.argv.slice(2);
  const targets = [];      // --target (repeatable)
  const rootFlags = [];    // --root path[:label]
  let configFlag = null;
  let out = 'dist';
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--target' && args[i + 1]) targets.push(args[++i]);
    else if (args[i] === '--root' && args[i + 1]) rootFlags.push(args[++i]);
    else if (args[i] === '--config' && args[i + 1]) configFlag = args[++i];
    else if (args[i] === '--out' && args[i + 1]) out = args[++i];
  }

  const repoRoot = path.resolve(__dirname, '..');
  const outDir = path.isAbsolute(out) ? out : path.resolve(repoRoot, out);

  // Resolve roots. Default (no flags) and a single --target keep id='' so the
  // dist/content/ layout is byte-identical to today (the surveys-only deploy).
  let roots;
  if (rootFlags.length) {
    roots = rootFlags.map((s) => mkRoot(s, true, repoRoot));
  } else if (configFlag) {
    const cfgPath = path.resolve(configFlag);
    const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
    const base = path.dirname(cfgPath);
    roots = cfg.roots.map((r) => ({
      id: r.id || path.basename(r.path),
      absPath: path.resolve(base, r.path),
      label: r.label || r.id || path.basename(r.path),
    }));
  } else if (targets.length > 1) {
    roots = targets.map((s) => mkRoot(s, true, repoRoot));
  } else {
    roots = [mkRoot(targets[0] || 'surveys', false, repoRoot)];
  }

  // Reject same-basename root collisions (else duplicate files.json entries +
  // rootForFile shadows one root) — mirrors serve.js's guard.
  const seenIds = new Set();
  for (const r of roots) {
    if (r.id === '') continue;
    if (seenIds.has(r.id)) { console.error(`Error: duplicate root id "${r.id}" — give distinct path:label ids`); process.exit(1); }
    seenIds.add(r.id);
  }

  let version = 'dev';
  try {
    version = execFileSync('git', ['rev-parse', '--short', 'HEAD'], { cwd: repoRoot, encoding: 'utf8' }).trim();
  } catch (_) { /* tolerate */ }

  // git-info: per-root map; single-root spreads the flat fields for back-compat.
  let gitInfo;
  if (roots.length === 1 && roots[0].id === '') {
    const info = computeGitInfo(roots[0].absPath);
    gitInfo = { schema: 2, roots: { '': info }, ...info };
  } else {
    gitInfo = { schema: 2, roots: {} };
    for (const r of roots) gitInfo.roots[r.id] = computeGitInfo(r.absPath);
  }

  const ignore = buildIgnoreMatcher({ projectIgnorePath: path.join(repoRoot, '.viewerignore') });
  const { fileCount } = buildBundle({ roots, outDir, version, gitInfo, ignore });
  buildHtmlAndAssets({ outDir, version });

  console.log(`published ${fileCount} files → ${outDir} (version ${version})`);
}

if (require.main === module) main();

module.exports = { buildBundle, buildHtmlAndAssets, main, referencedAssets };
