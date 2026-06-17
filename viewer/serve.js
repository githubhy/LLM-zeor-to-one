#!/usr/bin/env node
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { WebSocketServer } = require('ws');
const {
  normalizeWhitespace,
} = require('./lib/highlight-shared');
const contentSource = require('./lib/content-source');

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------
const viewerDir = __dirname;
// The repo root is the parent of the viewer/ directory (serve.js always lives
// at <repo>/viewer/serve.js). It is an implicit read-only asset fallback so
// markdown anywhere can embed images that escape its own dir (the browser
// normalises "../sim/…/*.png" to "/sim/…/*.png"). Markdown file access stays
// sandboxed per-root via markdownPathFor(); repoRoot is only an assetPathFor root.
const repoRoot = path.dirname(viewerDir);

const args = process.argv.slice(2);
let port = 3000;
const allowFlagRoots = []; // Extra read-only roots for asset lookups (--allow).
const rootFlags = [];      // --root <path[:label]> (repeatable).
let configFlag = null;     // --config <viewer.content.json>.
let positional = null;     // a lone dir-or-file.md positional (compat).

for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if ((a === '-p' || a === '--port') && args[i + 1]) { port = parseInt(args[i + 1], 10); i += 1; }
  else if (a === '--allow' && args[i + 1]) { allowFlagRoots.push(args[i + 1]); i += 1; }
  else if (a === '--root' && args[i + 1]) { rootFlags.push(args[i + 1]); i += 1; }
  else if (a === '--config' && args[i + 1]) { configFlag = args[i + 1]; i += 1; }
  else if (!positional) { positional = a; }
}

function usageExit(msg) {
  if (msg) console.error(`Error: ${msg}`);
  console.error('Usage: node serve.js <dir-or-file.md> [-p port] [--allow <path>]...');
  console.error('       node serve.js --root <path>[:label] [--root ...] [-p port]');
  console.error('       node serve.js --config <viewer.content.json> [-p port]');
  console.error('       node serve.js          # discovers viewer.content.json upward from cwd');
  process.exit(1);
}

// Parse a --root spec "path" or "path:Label". A ':' only separates a label when
// the suffix has no path separator (so a Windows "C:\dir" drive colon is safe).
function makeRoot(spec) {
  let p = spec, label = null;
  const ci = spec.lastIndexOf(':');
  if (ci > 1 && !/[\\/]/.test(spec.slice(ci + 1))) { p = spec.slice(0, ci); label = spec.slice(ci + 1); }
  const absPath = path.resolve(p);
  if (!fs.existsSync(absPath) || !fs.statSync(absPath).isDirectory()) usageExit(`root not found or not a directory: ${absPath}`);
  const id = path.basename(absPath);
  return { id, absPath, label: label || id };
}

// Discover viewer.content.json (explicit --config or upward walk from cwd).
function loadContentConfig(explicit) {
  let file = null;
  if (explicit) { file = path.resolve(explicit); if (!fs.existsSync(file)) usageExit(`--config not found: ${file}`); }
  else {
    let d = process.cwd();
    for (;;) {
      const cand = path.join(d, 'viewer.content.json');
      if (fs.existsSync(cand)) { file = cand; break; }
      const parent = path.dirname(d);
      if (parent === d) break;
      d = parent;
    }
  }
  if (!file) return null;
  try { const cfg = JSON.parse(fs.readFileSync(file, 'utf8')); cfg.baseDir = path.dirname(file); return cfg; }
  catch (e) { usageExit(`invalid config ${file}: ${e.message}`); return null; }
}

// Resolve the content roots. Precedence: single-file mode (exclusive) >
// --root flags > lone positional dir (compat, id='') > config file.
let singleFile = null;
let targetDir = null; // representative dir (roots[0].absPath) — favicon, repoRel base.
let roots = [];

const posAbs = positional ? path.resolve(positional) : null;
if (posAbs && positional.endsWith('.md') && fs.existsSync(posAbs) && fs.statSync(posAbs).isFile()) {
  if (rootFlags.length || configFlag) usageExit('single-file mode cannot be combined with --root/--config');
  singleFile = path.basename(posAbs);
  targetDir = path.dirname(posAbs);
  roots = [{ id: '', absPath: targetDir, label: '' }];
} else if (rootFlags.length) {
  if (configFlag) console.error('Note: --root given; ignoring --config.');
  roots = rootFlags.map(makeRoot);
} else if (positional) {
  if (!posAbs || !fs.existsSync(posAbs)) usageExit(`Target not found: ${posAbs}`);
  if (!fs.statSync(posAbs).isDirectory()) usageExit(`Not a directory: ${posAbs}`);
  targetDir = posAbs;
  roots = [{ id: '', absPath: posAbs, label: '' }];
} else {
  const cfg = loadContentConfig(configFlag);
  if (!cfg || !Array.isArray(cfg.roots) || !cfg.roots.length) {
    usageExit('no content roots — pass a dir, --root <path>, or provide a viewer.content.json');
  }
  roots = cfg.roots.map((r) => {
    const absPath = path.resolve(cfg.baseDir, r.path);
    if (!fs.existsSync(absPath)) usageExit(`config root not found: ${absPath}`);
    const id = r.id || path.basename(absPath);
    return { id, absPath, label: r.label || id };
  });
}

// Reject duplicate ids (collisions would make namespaced paths ambiguous).
const seenIds = new Set();
for (const r of roots) {
  if (r.id !== '' && seenIds.has(r.id)) usageExit(`duplicate root id "${r.id}" — give distinct --root path:label ids`);
  seenIds.add(r.id);
}
if (!targetDir) targetDir = roots[0].absPath;

const isMultiRoot = !(roots.length === 1 && roots[0].id === '');
// .viewerignore matcher — built-in defaults plus a repo-root .viewerignore if
// present. Built once and shared by the file walk AND the watcher so the served
// set and the watched set cannot diverge (Plan Phase 1). Sidecar annotation
// dirs are resolved per-root inline (rootForFile / rootForAbsPath), so no
// global annotationsRoot is needed in multi-root mode.
const ignoreMatcher = contentSource.buildIgnoreMatcher({
  projectIgnorePath: path.join(repoRoot, '.viewerignore'),
});

// Favicon: a round colored badge with the first letter of the target's
// last folder-name component. Hue derived from the folder name so each
// viewer instance gets a visually distinct tab favicon.
// Multi-root has no single basename — identify the window as "Workspace".
const targetFolderName = isMultiRoot ? 'Workspace' : (path.basename(targetDir) || '?');
const faviconLetter = (targetFolderName[0] || '?').toUpperCase();
function hashHueFor(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0;
  return h % 360;
}
const faviconHue = hashHueFor(targetFolderName);
function generateFaviconSVG() {
  const bg = `hsl(${faviconHue}, 65%, 45%)`;
  // 64x64 viewBox; rounded-rectangle background filling the whole viewbox
  // with corner radius rx=12. Letter sized to fill almost the full
  // square (font-size 54, weight 900) and centered via dominant-baseline.
  // System font stack so rendering doesn't depend on a network font load.
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">' +
    `<rect x="0" y="0" width="64" height="64" rx="12" ry="12" fill="${bg}"/>` +
    '<text x="32" y="32" ' +
    'font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Helvetica, Arial, sans-serif" ' +
    'font-size="54" font-weight="900" fill="white" ' +
    `text-anchor="middle" dominant-baseline="central">${faviconLetter}</text>` +
    '</svg>'
  );
}

// Extra asset roots — resolved absolute, deduped, existence-checked.
// Every content root is an allowed asset root; extras come from --allow <path>.
const assetRoots = [];
for (const r of roots) if (!assetRoots.includes(r.absPath)) assetRoots.push(r.absPath);
for (const raw of allowFlagRoots) {
  const resolved = path.resolve(raw);
  if (!fs.existsSync(resolved)) {
    console.error(`--allow path not found: ${resolved}`);
    process.exit(1);
  }
  if (!assetRoots.includes(resolved)) assetRoots.push(resolved);
}
// Repo root as a read-only asset fallback so markdown anywhere in the repo can
// embed images that live outside its own directory (e.g. wikis/ embedding
// ../sim/.../*.png, which the browser normalises to /sim/.../*.png). Deduped in
// case targetDir already is the repo root. assetPathFor() gates each root with
// its own ensureWithin, so markdown access (markdownPathFor → targetPathFor)
// stays sandboxed to targetDir and is unaffected.
if (!assetRoots.includes(repoRoot)) assetRoots.push(repoRoot);


// ---------------------------------------------------------------------------
// MIME types
// ---------------------------------------------------------------------------
const MIME = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.md': 'text/markdown; charset=utf-8',
  '.pdf': 'application/pdf',
};

function mime(filePath) {
  return MIME[path.extname(filePath).toLowerCase()] || 'application/octet-stream';
}

function etagOf(content) {
  return `"${crypto.createHash('sha1').update(content).digest('hex')}"`;
}

function readUtf8WithRevision(filePath) {
  const text = fs.readFileSync(filePath, 'utf8');
  return { text, revision: etagOf(text) };
}

function ensureWithin(root, filePath) {
  return filePath.startsWith(root + path.sep) || filePath === root;
}

// Resolve a namespaced file id (id/rel, or rel in single-root mode) to an
// absolute path WITHIN its owning root. Returns null on an unknown namespace
// or a `..` escape out of that root — each root is its own sandbox, so a path
// in root A can never resolve into root B.
function targetPathFor(file) {
  const m = contentSource.rootForFile(roots, file);
  if (!m) return null;
  const resolved = path.resolve(m.root.absPath, m.rel);
  if (!ensureWithin(m.root.absPath, resolved)) return null;
  return resolved;
}

// Read-only asset lookup across targetDir plus any --allow roots. Returns
// the first matching existing file, or null if absent from every allowed
// root. Each root is checked with its own ensureWithin gate, so `..`
// escapes cannot cross root boundaries. Used by the image/asset branch;
// markdown access stays strictly sandboxed via targetPathFor.
function assetPathFor(relativePath) {
  for (const root of assetRoots) {
    const resolved = path.resolve(root, relativePath);
    if (!ensureWithin(root, resolved)) continue;
    try {
      if (fs.existsSync(resolved) && fs.statSync(resolved).isFile()) return resolved;
    } catch {
      // continue
    }
  }
  return null;
}

// Like targetPathFor, but additionally rejects any path under the sidecar
// annotations directory. The /api/md/ route must not double as a backdoor
// for reading or overwriting sidecar JSON files — those have their own
// validated route and format.
function markdownPathFor(file) {
  const m = contentSource.rootForFile(roots, file);
  if (!m) return null;
  const resolved = path.resolve(m.root.absPath, m.rel);
  if (!ensureWithin(m.root.absPath, resolved)) return null;
  // Reject the owning root's sidecar dir — /api/md/ must not read/write sidecars.
  if (ensureWithin(path.join(m.root.absPath, '.viewer-highlights'), resolved)) return null;
  return resolved;
}

function annotationPathFor(file) {
  const m = contentSource.rootForFile(roots, file);
  if (!m) return null;
  const annRoot = path.join(m.root.absPath, '.viewer-highlights');
  const resolved = path.resolve(annRoot, `${m.rel}.json`);
  if (!ensureWithin(annRoot, resolved)) return null;
  return resolved;
}

function writeTextAtomic(filePath, body) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const tmpPath = `${filePath}.tmp`;
  fs.writeFileSync(tmpPath, body, 'utf8');
  fs.renameSync(tmpPath, filePath);
}

function readJsonBody(req, res, onBody) {
  const MAX_BODY = 10 * 1024 * 1024;
  let body = '';
  let bytes = 0;
  let aborted = false;

  req.on('error', () => {
    if (aborted) return;
    aborted = true;
    res.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Request stream error');
  });

  req.on('data', (chunk) => {
    if (aborted) return;
    bytes += Buffer.byteLength(chunk);
    if (bytes > MAX_BODY) {
      aborted = true;
      res.writeHead(413, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Payload too large');
      req.destroy();
      return;
    }
    body += chunk;
  });

  req.on('end', () => {
    if (aborted) return;
    onBody(body);
  });
}

function normalizeAnnotationDoc(file, docRevision, value) {
  const source = value && typeof value === 'object' ? value : {};
  const highlights = Array.isArray(source.highlights) ? source.highlights : [];
  return {
    version: 1,
    file,
    documentRevision: source.documentRevision || docRevision || null,
    highlights: highlights.map((entry) => ({
      id: entry.id,
      file,
      color: entry.color || 'yellow',
      backend: 'sidecar',
      revision: entry.revision || docRevision || null,
      excerpt: normalizeWhitespace(entry.excerpt || ''),
      segments: Array.isArray(entry.segments) ? entry.segments : [],
      updatedAt: Number(entry.updatedAt) || 0,
      ...(entry.deleted ? { deleted: true } : {}),
    })),
  };
}

function defaultAnnotationDoc(file, docRevision) {
  return normalizeAnnotationDoc(file, docRevision, { highlights: [] });
}

function readAnnotationDoc(file, docRevision) {
  const filePath = annotationPathFor(file);
  if (!filePath) throw new Error('Invalid annotation path');
  if (!fs.existsSync(filePath)) {
    const doc = defaultAnnotationDoc(file, docRevision);
    return {
      doc,
      revision: etagOf(JSON.stringify(doc)),
      exists: false,
      filePath,
    };
  }
  const raw = fs.readFileSync(filePath, 'utf8');
  const parsed = JSON.parse(raw);
  const doc = normalizeAnnotationDoc(file, docRevision, parsed);
  return {
    doc,
    revision: etagOf(raw),
    exists: true,
    filePath,
  };
}

function listMarkdownFiles() {
  if (!isMultiRoot) {
    // Single-root compat is STRICTLY byte-identical to the legacy `serve.js
    // <dir>`: NO ignore matcher (so the walk uses the exact legacy skip set —
    // node_modules/archive/.viewer-highlights — and serves dist/temp/etc.
    // markdown the user explicitly pointed at). The expanded .viewerignore /
    // noise-pruning is a MULTI-ROOT capability only (decision 2026-06-14-03).
    // honorRootOrderJson:true keeps a leaf survey dir's own order.json short-circuit.
    return contentSource.listMarkdownFiles(roots[0].absPath, { honorRootOrderJson: true });
  }
  return contentSource.listMarkdownFilesMultiRoot(roots, { ignore: ignoreMatcher });
}

// Map a sidecar .json absolute path back to its NAMESPACED file id (which root
// owns it, plus the root-relative path), so watcher broadcasts match the keys
// the frontend uses.
function sidecarFileFromAnnotationPath(absPath) {
  for (const r of roots) {
    const annRoot = path.join(r.absPath, '.viewer-highlights');
    if (!ensureWithin(annRoot, absPath)) continue;
    const relative = path.relative(annRoot, absPath).replace(/\\/g, '/');
    if (!relative.endsWith('.json')) return null;
    const rel = relative.slice(0, -'.json'.length);
    return r.id === '' ? rel : `${r.id}/${rel}`;
  }
  return null;
}

function buildManifest(fileFilter) {
  if (!isMultiRoot) return contentSource.buildManifest(roots[0].absPath, fileFilter);
  if (fileFilter) {
    const m = contentSource.rootForFile(roots, fileFilter);
    if (!m) return { entries: [] };
    const inner = contentSource.buildManifest(m.root.absPath, m.rel);
    for (const e of inner.entries) e.file = fileFilter; // re-namespace
    return inner;
  }
  const entries = [];
  for (const r of roots) {
    const inner = contentSource.buildManifest(r.absPath, null, { ignore: ignoreMatcher });
    for (const e of inner.entries) {
      e.file = r.id === '' ? e.file : `${r.id}/${e.file}`;
      entries.push(e);
    }
  }
  return { entries };
}

function invalidateManifestForFile(file) {
  // Manifest is recomputed per-request via content-source (Plan 02 Task 1);
  // retained as a no-op hook so the watcher/route call sites stay unchanged.
}

// ---------------------------------------------------------------------------
// Git info (for citation GitHub URLs)
// ---------------------------------------------------------------------------

function computeGitInfo() {
  if (!isMultiRoot) {
    // Single-root: return the schema-2 per-root map AND spread the flat fields
    // so a not-yet-updated client still reads top-level repoRelDir (back-compat).
    const info = contentSource.computeGitInfo(roots[0].absPath);
    return { schema: 2, roots: { '': info }, ...info };
  }
  const out = { schema: 2, roots: {} };
  for (const r of roots) out.roots[r.id] = contentSource.computeGitInfo(r.absPath);
  return out;
}

// ---------------------------------------------------------------------------
// HTTP server
// ---------------------------------------------------------------------------
const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${port}`);
  let pathname = decodeURIComponent(url.pathname);

  if (pathname === '/api/files') {
    const files = listMarkdownFiles();
    const payload = {
      schema: 2,
      files,
      roots: roots.map((r) => ({ id: r.id, label: r.label })),
      defaultFile: singleFile || null,
    };
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify(payload));
    return;
  }

  if (pathname === '/api/git-info') {
    let payload;
    try {
      payload = computeGitInfo();
    } catch (err) {
      payload = { available: false, reason: 'git probe failed' };
    }
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify(payload));
    return;
  }

  if (pathname === '/api/highlights-manifest') {
    const file = url.searchParams.get('file') || null;
    const payload = buildManifest(file);
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify(payload));
    return;
  }

  if (pathname.startsWith('/api/highlights/')) {
    const file = pathname.slice('/api/highlights/'.length);
    const markdownPath = markdownPathFor(file);
    if (!markdownPath || !fs.existsSync(markdownPath)) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }

    if (req.method === 'GET') {
      const { revision: docRevision } = readUtf8WithRevision(markdownPath);
      const current = readAnnotationDoc(file, docRevision);
      res.writeHead(200, {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
        'ETag': current.revision,
        'X-Annotations-Revision': current.revision,
        'X-Document-Revision': docRevision,
      });
      res.end(JSON.stringify(current.doc));
      return;
    }

    if (req.method === 'PUT') {
      const ifMatch = req.headers['if-match'];
      const baseDocRevision = req.headers['x-document-revision'];
      if (!ifMatch) {
        // Early 428 uses a stale-but-harmless revision read — the client
        // retries with If-Match anyway so no race hazard here.
        const { revision: docRevision } = readUtf8WithRevision(markdownPath);
        const preview = readAnnotationDoc(file, docRevision);
        res.writeHead(428, {
          'Content-Type': 'text/plain; charset=utf-8',
          'ETag': preview.revision,
          'X-Document-Revision': docRevision,
        });
        res.end('Missing If-Match');
        return;
      }

      readJsonBody(req, res, (body) => {
        // TOCTOU fix: re-read the document and annotation revisions inside
        // the synchronous write window (no awaits between this read and the
        // writeTextAtomic). This closes the gap where a concurrent PUT could
        // interleave between the initial read and the write.
        if (!fs.existsSync(markdownPath)) {
          res.writeHead(404);
          res.end('Not found');
          return;
        }
        const { revision: docRevision } = readUtf8WithRevision(markdownPath);
        const current = readAnnotationDoc(file, docRevision);

        if (ifMatch !== current.revision) {
          res.writeHead(409, {
            'Content-Type': 'text/plain; charset=utf-8',
            'ETag': current.revision,
            'X-Document-Revision': docRevision,
          });
          res.end('Annotation revision conflict');
          return;
        }
        if (baseDocRevision && baseDocRevision !== docRevision) {
          res.writeHead(409, {
            'Content-Type': 'text/plain; charset=utf-8',
            'ETag': current.revision,
            'X-Document-Revision': docRevision,
          });
          res.end('Document revision conflict');
          return;
        }

        let parsed;
        try {
          parsed = body ? JSON.parse(body) : {};
        } catch {
          res.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
          res.end('Invalid JSON');
          return;
        }

        try {
          const normalized = normalizeAnnotationDoc(file, docRevision, parsed);
          const json = JSON.stringify(normalized, null, 2);
          writeTextAtomic(current.filePath, json);
          invalidateManifestForFile(file);
          const newRevision = etagOf(json);
          res.writeHead(204, {
            'ETag': newRevision,
            'X-Annotations-Revision': newRevision,
            'X-Document-Revision': docRevision,
          });
          res.end();
        } catch (err) {
          const status = err && (err.code === 'EACCES' || err.code === 'EPERM') ? 403 : 500;
          res.writeHead(status, { 'Content-Type': 'text/plain; charset=utf-8' });
          res.end(`Write failed: ${err.code || 'UNKNOWN'}`);
          console.error(`PUT failed for ${current.filePath}:`, err);
        }
      });
      return;
    }

    res.writeHead(405);
    res.end('Method not allowed');
    return;
  }

  if (pathname.startsWith('/api/md/')) {
    const file = pathname.slice('/api/md/'.length);
    const filePath = markdownPathFor(file);
    if (!filePath || !fs.existsSync(filePath)) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }

    if (req.method === 'GET') {
      const current = readUtf8WithRevision(filePath);
      res.writeHead(200, {
        'Content-Type': 'text/markdown; charset=utf-8',
        'Cache-Control': 'no-store',
        'ETag': current.revision,
        'X-Document-Revision': current.revision,
      });
      res.end(current.text);
      return;
    }

    if (req.method === 'PUT') {
      const ifMatch = req.headers['if-match'];
      if (!ifMatch) {
        const preview = readUtf8WithRevision(filePath);
        res.writeHead(428, {
          'Content-Type': 'text/plain; charset=utf-8',
          'ETag': preview.revision,
        });
        res.end('Missing If-Match');
        return;
      }

      readJsonBody(req, res, (body) => {
        // TOCTOU fix: re-read the on-disk revision inside the synchronous
        // write window so the revision check and the write happen
        // atomically with respect to the Node event loop.
        if (!fs.existsSync(filePath)) {
          res.writeHead(404);
          res.end('Not found');
          return;
        }
        const current = readUtf8WithRevision(filePath);
        if (ifMatch !== current.revision) {
          res.writeHead(409, {
            'Content-Type': 'text/plain; charset=utf-8',
            'ETag': current.revision,
            'X-Document-Revision': current.revision,
          });
          res.end('Document revision conflict');
          return;
        }

        try {
          writeTextAtomic(filePath, body);
          invalidateManifestForFile(file);
          const nextRevision = etagOf(body);
          res.writeHead(204, {
            'ETag': nextRevision,
            'X-Document-Revision': nextRevision,
          });
          res.end();
        } catch (err) {
          const status = err && (err.code === 'EACCES' || err.code === 'EPERM') ? 403 : 500;
          res.writeHead(status, { 'Content-Type': 'text/plain; charset=utf-8' });
          res.end(`Write failed: ${err.code || 'UNKNOWN'}`);
          console.error(`PUT failed for ${filePath}:`, err);
        }
      });
      return;
    }

    res.writeHead(405);
    res.end('Method not allowed');
    return;
  }

  if (pathname === '/favicon.svg' || pathname === '/favicon.ico') {
    const svg = generateFaviconSVG();
    res.writeHead(200, {
      'Content-Type': 'image/svg+xml',
      'Cache-Control': 'no-store',
    });
    res.end(svg);
    return;
  }

  if (pathname.startsWith('/figures/') || pathname.match(/\.(png|jpg|jpeg|gif|svg)$/i)) {
    const filePath = assetPathFor(pathname.slice(1));
    if (filePath) {
      res.writeHead(200, { 'Content-Type': mime(filePath) });
      res.end(fs.readFileSync(filePath));
      return;
    }
  }

  if (pathname === '/' || pathname === '/index.html') pathname = '/index.html';
  const staticPath = path.join(viewerDir, pathname);
  if (ensureWithin(viewerDir, staticPath) && fs.existsSync(staticPath) && fs.statSync(staticPath).isFile()) {
    res.writeHead(200, { 'Content-Type': mime(staticPath) });
    res.end(fs.readFileSync(staticPath));
    return;
  }

  res.writeHead(404);
  res.end('Not found');
});

// ---------------------------------------------------------------------------
// WebSocket notifications
// ---------------------------------------------------------------------------
const wss = new WebSocketServer({ server });
const clients = new Set();

wss.on('connection', (ws) => {
  clients.add(ws);
  ws.on('close', () => clients.delete(ws));
});

function broadcast(data) {
  const message = JSON.stringify(data);
  for (const ws of clients) {
    if (ws.readyState === 1) ws.send(message);
  }
}

// ---------------------------------------------------------------------------
// File watcher
// ---------------------------------------------------------------------------
let chokidar;
try {
  chokidar = require('chokidar');
} catch {
  console.error('ERROR: chokidar not installed - live reload will not work.');
  console.error('       Run: cd viewer && npm install');
  process.exit(1);
}

if (chokidar) {
  const watcher = chokidar.watch(roots.map((r) => r.absPath), {
    // chokidar v4 removed glob support; `ignored` is a whole-path function.
    // Derive it from the SAME .viewerignore matcher as the walk (resolved per
    // owning root) so served/watched sets cannot drift — EXCEPT the sidecar
    // dirs: the walk skips .viewer-highlights, but the watcher MUST see sidecar
    // edits for annotation live-reload, so those are never ignored here.
    // Single-root uses the legacy ignored set (strict byte-compat with main —
    // the served set isn't matcher-pruned, so the watcher must not be either).
    // Multi-root derives `ignored` from the shared matcher (per owning root),
    // never ignoring sidecar dirs (annotation live-reload must still fire).
    ignored: !isMultiRoot ? [/node_modules/, /archive/] : (p) => {
      const m = contentSource.rootForAbsPath(roots, p);
      if (!m || m.rel === '') return false;
      if (m.rel === '.viewer-highlights' || m.rel.startsWith('.viewer-highlights/')) return false;
      return ignoreMatcher.ignores(m.rel) || ignoreMatcher.ignores(`${m.rel}/`);
    },
    ignoreInitial: true,
    awaitWriteFinish: { stabilityThreshold: 150, pollInterval: 50 },
  });

  const ASSET_EXTS = new Set(['.svg', '.json', '.png', '.jpg', '.jpeg']);

  // Namespaced id of a changed .md (owning root id + root-relative path).
  function relMd(absPath) {
    if (!absPath.endsWith('.md')) return null;
    const m = contentSource.rootForAbsPath(roots, absPath);
    if (!m) return null;
    return m.root.id === '' ? m.rel : `${m.root.id}/${m.rel}`;
  }

  function assetToMd(absPath) {
    const ext = path.extname(absPath).toLowerCase();
    if (!ASSET_EXTS.has(ext)) return null;
    const dir = path.dirname(absPath);
    if (path.basename(dir) !== 'figures') return null;
    const parentDir = path.dirname(dir);
    const m = contentSource.rootForAbsPath(roots, parentDir);
    if (!m) return null;
    const base = m.rel ? `${m.rel}/` : '';
    const prefix = m.root.id === '' ? base : `${m.root.id}/${base}`;
    try {
      return fs.readdirSync(parentDir)
        .filter((file) => file.endsWith('.md'))
        .map((file) => `${prefix}${file}`);
    } catch {
      return null;
    }
  }

  function notifyMarkdownChange(file, type) {
    invalidateManifestForFile(file);
    broadcast({ type, target: 'markdown', file });
  }

  function notifyAnnotationChange(file, type) {
    invalidateManifestForFile(file);
    broadcast({ type, target: 'annotations', file });
  }

  // A sidecar .json under any root's .viewer-highlights resolves to a non-null
  // namespaced id; a normal content file resolves to null here and falls through.
  watcher.on('change', (absPath) => {
    const normalized = path.resolve(absPath);
    const sc = sidecarFileFromAnnotationPath(normalized);
    if (sc) { notifyAnnotationChange(sc, 'change'); return; }
    const file = relMd(normalized);
    if (file) {
      console.log(`  changed: ${file}`);
      notifyMarkdownChange(file, 'change');
      return;
    }
    const mdFiles = assetToMd(normalized);
    if (mdFiles) {
      console.log(`  asset changed -> reload ${mdFiles.join(', ')}`);
      for (const fileName of mdFiles) notifyMarkdownChange(fileName, 'change');
    }
  });

  watcher.on('add', (absPath) => {
    const normalized = path.resolve(absPath);
    const sc = sidecarFileFromAnnotationPath(normalized);
    if (sc) { notifyAnnotationChange(sc, 'change'); return; }
    const file = relMd(normalized);
    if (!file) return;
    console.log(`  added: ${file}`);
    invalidateManifestForFile(file);
    broadcast({ type: 'add', target: 'markdown', file });
  });

  watcher.on('unlink', (absPath) => {
    const normalized = path.resolve(absPath);
    const sc = sidecarFileFromAnnotationPath(normalized);
    if (sc) { notifyAnnotationChange(sc, 'change'); return; }
    const file = relMd(normalized);
    if (!file) return;
    console.log(`  removed: ${file}`);
    invalidateManifestForFile(file);
    broadcast({ type: 'remove', target: 'markdown', file });
  });
}

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
server.listen(port, () => {
  console.log('\n  Markdown viewer ready');
  if (isMultiRoot) {
    console.log(`  Serving ${roots.length} roots:`);
    for (const r of roots) console.log(`    ${r.id}  ->  ${r.absPath}`);
  } else {
    console.log(`  Serving: ${roots[0].absPath}`);
  }
  const contentSet = new Set(roots.map((r) => r.absPath));
  for (const a of assetRoots) if (!contentSet.has(a)) console.log(`  +assets: ${a}`);
  console.log(`  URL:     http://localhost:${port}\n`);
});
