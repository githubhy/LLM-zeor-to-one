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
const args = process.argv.slice(2);
let targetDir = null;
let port = 3000;
const allowFlagRoots = []; // Extra read-only roots for asset lookups (--allow).

for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if ((a === '-p' || a === '--port') && args[i + 1]) {
    port = parseInt(args[i + 1], 10);
    i += 1;
  } else if (a === '--allow' && args[i + 1]) {
    allowFlagRoots.push(args[i + 1]);
    i += 1;
  } else if (!targetDir) {
    targetDir = a;
  }
}

if (!targetDir) {
  console.error('Usage: node serve.js <target-dir-or-file> [-p port] [--allow <path>]...');
  console.error('  e.g. node viewer/serve.js surveys/5g-nr-ldpc');
  console.error('       node viewer/serve.js surveys/my-survey.md');
  console.error('       node viewer/serve.js reports/ --allow sim/ --allow temp/');
  console.error('');
  console.error('  --allow <path> extends the READ-ONLY asset sandbox with the given');
  console.error('  directory, so markdown in <target-dir> can embed images from outside');
  console.error('  it (e.g. a review doc in reports/ referencing figures under sim/).');
  console.error('  Markdown file access remains strictly sandboxed to <target-dir>.');
  process.exit(1);
}

targetDir = path.resolve(targetDir);
if (!fs.existsSync(targetDir)) {
  console.error(`Target not found: ${targetDir}`);
  process.exit(1);
}

let singleFile = null;
if (fs.statSync(targetDir).isFile() && targetDir.endsWith('.md')) {
  singleFile = path.basename(targetDir);
  targetDir = path.dirname(targetDir);
}

const viewerDir = __dirname;
// The repo root is the parent of the viewer/ directory (serve.js always lives
// at <repo>/viewer/serve.js).  It is added as an implicit read-only fallback
// for image / asset lookups so that markdown files in any subdirectory (e.g.
// wikis/) can embed images with relative paths that escape their own directory
// (e.g. "../sim/…/*.png") — the browser normalises those to repo-rooted paths
// like "/sim/…/*.png" before the HTTP request reaches the server.
// Markdown file access remains strictly sandboxed to targetDir via
// markdownPathFor(); the repo root is only used by assetPathFor().
const repoRoot = path.dirname(viewerDir);
const annotationsRoot = path.join(targetDir, '.viewer-highlights');

// Favicon: a round colored badge with the first letter of the target's
// last folder-name component. Hue derived from the folder name so each
// viewer instance gets a visually distinct tab favicon.
const targetFolderName = path.basename(targetDir) || '?';
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
// targetDir is always an allowed root; extras come from --allow <path>.
const assetRoots = [targetDir];
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

function targetPathFor(relativePath) {
  const resolved = path.resolve(targetDir, relativePath);
  if (!ensureWithin(targetDir, resolved)) return null;
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
function markdownPathFor(relativePath) {
  const resolved = targetPathFor(relativePath);
  if (!resolved) return null;
  if (ensureWithin(annotationsRoot, resolved)) return null;
  return resolved;
}

function annotationPathFor(file) {
  const relativeJson = `${file}.json`;
  const resolved = path.resolve(annotationsRoot, relativeJson);
  if (!ensureWithin(annotationsRoot, resolved)) return null;
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
  return contentSource.listMarkdownFiles(targetDir);
}

function sidecarFileFromAnnotationPath(absPath) {
  const relative = path.relative(annotationsRoot, absPath).replace(/\\/g, '/');
  if (!relative.endsWith('.json')) return null;
  return relative.slice(0, -'.json'.length);
}

function buildManifest(fileFilter) {
  return contentSource.buildManifest(targetDir, fileFilter);
}

function invalidateManifestForFile(file) {
  // Manifest is recomputed per-request via content-source (Plan 02 Task 1);
  // retained as a no-op hook so the watcher/route call sites stay unchanged.
}

// ---------------------------------------------------------------------------
// Git info (for citation GitHub URLs)
// ---------------------------------------------------------------------------

function computeGitInfo() {
  return contentSource.computeGitInfo(targetDir);
}

// ---------------------------------------------------------------------------
// HTTP server
// ---------------------------------------------------------------------------
const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://localhost:${port}`);
  let pathname = decodeURIComponent(url.pathname);

  if (pathname === '/api/files') {
    const files = listMarkdownFiles();
    const payload = { files, defaultFile: singleFile || null };
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
  const watcher = chokidar.watch(targetDir, {
    ignored: [/node_modules/, /archive/],
    ignoreInitial: true,
    awaitWriteFinish: { stabilityThreshold: 150, pollInterval: 50 },
  });

  const ASSET_EXTS = new Set(['.svg', '.json', '.png', '.jpg', '.jpeg']);

  function relMd(absPath) {
    if (!absPath.endsWith('.md')) return null;
    return path.relative(targetDir, absPath).replace(/\\/g, '/');
  }

  function assetToMd(absPath) {
    const ext = path.extname(absPath).toLowerCase();
    if (!ASSET_EXTS.has(ext)) return null;
    const dir = path.dirname(absPath);
    if (path.basename(dir) !== 'figures') return null;
    const parentDir = path.dirname(dir);
    const rel = path.relative(targetDir, parentDir).replace(/\\/g, '/');
    try {
      return fs.readdirSync(parentDir)
        .filter((file) => file.endsWith('.md'))
        .map((file) => (rel ? `${rel}/${file}` : file));
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

  watcher.on('change', (absPath) => {
    const normalized = path.resolve(absPath);
    if (ensureWithin(annotationsRoot, normalized)) {
      const file = sidecarFileFromAnnotationPath(normalized);
      if (file) notifyAnnotationChange(file, 'change');
      return;
    }
    const file = relMd(normalized);
    if (file) {
      console.log(`  changed: ${file}`);
      notifyMarkdownChange(file, 'change');
      return;
    }
    const mdFiles = assetToMd(normalized);
    if (mdFiles) {
      const asset = path.relative(targetDir, normalized).replace(/\\/g, '/');
      console.log(`  asset changed: ${asset} -> reload ${mdFiles.join(', ')}`);
      for (const fileName of mdFiles) notifyMarkdownChange(fileName, 'change');
    }
  });

  watcher.on('add', (absPath) => {
    const normalized = path.resolve(absPath);
    if (ensureWithin(annotationsRoot, normalized)) {
      const file = sidecarFileFromAnnotationPath(normalized);
      if (file) notifyAnnotationChange(file, 'change');
      return;
    }
    const file = relMd(normalized);
    if (!file) return;
    console.log(`  added: ${file}`);
    invalidateManifestForFile(file);
    broadcast({ type: 'add', target: 'markdown', file });
  });

  watcher.on('unlink', (absPath) => {
    const normalized = path.resolve(absPath);
    if (ensureWithin(annotationsRoot, normalized)) {
      const file = sidecarFileFromAnnotationPath(normalized);
      if (file) notifyAnnotationChange(file, 'change');
      return;
    }
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
  console.log(`  Serving: ${targetDir}`);
  for (const extra of assetRoots.slice(1)) {
    console.log(`  +assets: ${extra}`);
  }
  console.log(`  URL:     http://localhost:${port}\n`);
});
