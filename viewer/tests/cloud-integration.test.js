'use strict';
// End-to-end cloud round-trip: gate (404 / ?k cookie / cookie-auth) + annotation
// write/read + tombstone + manifest + desktop sync-back via pullAnnotations.
//
// Server strategy (Plan 03 decision D2): spawn `wrangler pages dev` against a
// freshly published dist/ as the PRIMARY server; if wrangler cannot install or
// boot in this sandbox, fall back to a plain-Node http harness that runs the
// SAME cloud-api handlers over a Map-backed KV. Both servers must satisfy the
// identical assertion block below, so the test exercises real handler logic
// either way.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const net = require('net');
const http = require('http');
const { spawn } = require('child_process');

const { buildBundle, buildHtmlAndAssets } = require('../publish');
const cloudApi = require('../lib/cloud-api');
const { pullAnnotations } = require('../pull-annotations');

const TOKEN = 'T0KEN';
const VIEWER_DIR = path.resolve(__dirname, '..');

// ── helpers ────────────────────────────────────────────────────────────────

function mkdtemp(prefix) { return fs.mkdtempSync(path.join(os.tmpdir(), prefix)); }

function pickFreePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.on('error', reject);
    srv.listen(0, '127.0.0.1', () => {
      const { port } = srv.address();
      srv.close(() => resolve(port));
    });
  });
}

// Publish a tiny one-file survey into a temp dist/, return the dist dir.
function publishFixture() {
  const target = mkdtemp('cloud-survey-');
  fs.writeFileSync(path.join(target, 'order.json'), JSON.stringify(['test.md']));
  fs.writeFileSync(path.join(target, 'test.md'), '# Test\n\nsecond line\n\nthird line of text\n');
  const dist = mkdtemp('cloud-dist-');
  buildBundle({ targetDir: target, outDir: dist, version: 'itest', gitInfo: { available: false } });
  buildHtmlAndAssets({ outDir: dist, version: 'itest' });
  return dist;
}

async function waitForPort(url, attempts = 60, delayMs = 500) {
  for (let i = 0; i < attempts; i++) {
    try {
      const res = await fetch(url, { redirect: 'manual' });
      if (res.status === 200 || res.status === 404) return true;
    } catch { /* not up yet */ }
    await new Promise((r) => setTimeout(r, delayMs));
  }
  return false;
}

// ── PRIMARY server: wrangler pages dev . (cwd = dist so functions/ is found) ──

function resolveWranglerBin() {
  try {
    const pkg = require.resolve('wrangler/package.json', { paths: [VIEWER_DIR] });
    const bin = path.join(path.dirname(pkg), require(pkg).bin.wrangler);
    return fs.existsSync(bin) ? bin : null;
  } catch { return null; }
}

async function startWrangler(dist, port) {
  const bin = resolveWranglerBin();
  if (!bin) return null; // wrangler not installed in this sandbox → caller falls back.
  // Invoke `node <wrangler.js> pages dev .` with cwd = dist so the adjacent
  // functions/ directory is discovered (wrangler treats cwd, not the positional
  // assets dir, as the Functions root).
  const proc = spawn(
    process.execPath,
    [
      bin, 'pages', 'dev', '.',
      '--port', String(port),
      '--ip', '127.0.0.1',
      '--binding', `VIEWER_TOKEN=${TOKEN}`,
      '--kv', 'ANNOTATIONS',
      '--compatibility-date', '2025-01-01',
      '--log-level', 'error',
    ],
    { cwd: dist, env: { ...process.env, WRANGLER_SEND_METRICS: 'false' }, stdio: 'ignore' },
  );
  let exited = false;
  proc.on('exit', () => { exited = true; });
  const ready = await waitForPort(`http://127.0.0.1:${port}/?k=${TOKEN}`, 60, 500);
  if (!ready || exited) {
    try { proc.kill('SIGKILL'); } catch { /* ignore */ }
    return null;
  }
  return {
    label: 'wrangler',
    stop: () => new Promise((resolve) => {
      if (exited) return resolve();
      proc.on('exit', () => resolve());
      try { proc.kill('SIGTERM'); } catch { resolve(); }
      // hard-kill backstop
      setTimeout(() => { try { proc.kill('SIGKILL'); } catch { /* ignore */ } resolve(); }, 4000);
    }),
  };
}

// ── FALLBACK server: plain Node http running the same cloud-api handlers ──────

// Map-backed KV implementing the get/put/list interface cloud-api expects.
function makeKv() {
  const store = new Map();
  return {
    async get(k) { return store.has(k) ? store.get(k) : null; },
    async put(k, v) { store.set(k, String(v)); },
    async list({ prefix } = {}) {
      const keys = [...store.keys()]
        .filter((k) => !prefix || k.startsWith(prefix))
        .map((name) => ({ name }));
      return { keys };
    },
  };
}

// Build a web Request from a Node IncomingMessage (+ collected body).
function toWebRequest(req, body, origin) {
  const url = origin + req.url;
  const headers = new Headers();
  for (const [k, v] of Object.entries(req.headers)) {
    if (Array.isArray(v)) for (const vv of v) headers.append(k, vv);
    else if (v != null) headers.set(k, v);
  }
  const init = { method: req.method, headers };
  if (body && body.length && req.method !== 'GET' && req.method !== 'HEAD') init.body = body;
  return new Request(url, init);
}

// Write a web Response onto a Node ServerResponse.
async function sendWebResponse(res, webRes) {
  res.statusCode = webRes.status;
  for (const [k, v] of webRes.headers) res.setHeader(k, v);
  const buf = Buffer.from(await webRes.arrayBuffer());
  res.end(buf);
}

function startFallback(dist, port) {
  const env = { kv: makeKv(), token: TOKEN };
  const server = http.createServer((req, res) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', async () => {
      try {
        const body = Buffer.concat(chunks);
        const origin = `http://127.0.0.1:${port}`;
        const request = toWebRequest(req, body, origin);
        const url = new URL(request.url);

        // API routes first (gate via Authorization bearer inside handlers' env).
        const annMatch = /^\/api\/annotations\/(.+)$/.exec(url.pathname);
        if (annMatch) {
          const file = decodeURIComponent(annMatch[1]);
          if (!cloudApi.isAuthorized(request.headers.get('Authorization'), TOKEN)) {
            res.statusCode = 404; return res.end('Not found');
          }
          const handler = request.method === 'PUT' ? cloudApi.handlePutAnnotation : cloudApi.handleGetAnnotation;
          return sendWebResponse(res, await handler(request, env, file));
        }
        if (url.pathname === '/api/annotations-manifest') {
          if (!cloudApi.isAuthorized(request.headers.get('Authorization'), TOKEN)) {
            res.statusCode = 404; return res.end('Not found');
          }
          return sendWebResponse(res, await cloudApi.handleManifest(request, env));
        }

        // Static paths run through the gate (mirrors _middleware.js).
        const gate = await cloudApi.handleGate(request, env);
        if (gate instanceof Response) return sendWebResponse(res, gate);

        // Serve the static asset (index.html for '/').
        let rel = url.pathname === '/' ? 'index.html' : url.pathname.replace(/^\//, '');
        const filePath = path.join(dist, rel);
        if (!filePath.startsWith(dist) || !fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
          res.statusCode = 404; if (gate && gate.setCookie) res.setHeader('Set-Cookie', cloudApi.serializeSessionCookie(gate.setCookie));
          return res.end('Not found');
        }
        if (gate && gate.setCookie) res.setHeader('Set-Cookie', cloudApi.serializeSessionCookie(gate.setCookie));
        res.statusCode = 200;
        res.end(fs.readFileSync(filePath));
      } catch (e) {
        res.statusCode = 500; res.end('error: ' + (e && e.message));
      }
    });
  });
  return new Promise((resolve) => {
    server.listen(port, '127.0.0.1', () => resolve({
      label: 'fallback',
      stop: () => new Promise((r) => server.close(() => r())),
    }));
  });
}

// ── assertions (identical for both servers) ──────────────────────────────────

async function runRoundTrip(t, base) {
  const auth = { Authorization: `Bearer ${TOKEN}` };

  // 1. No token → 404 "Not found".
  {
    const res = await fetch(`${base}/`, { redirect: 'manual' });
    assert.equal(res.status, 404, 'no-token GET should 404');
    assert.equal((await res.text()).trim(), 'Not found');
  }

  // 2. ?k bootstrap → 200 + Set-Cookie vt=TOKEN; HttpOnly.
  {
    const res = await fetch(`${base}/?k=${TOKEN}`, { redirect: 'manual' });
    assert.equal(res.status, 200, '?k GET should 200');
    const sc = res.headers.get('set-cookie') || '';
    assert.match(sc, /vt=T0KEN/, 'Set-Cookie carries vt=token');
    assert.match(sc, /HttpOnly/i, 'Set-Cookie is HttpOnly');
  }

  // 3. Static path with session cookie → 200.
  {
    const res = await fetch(`${base}/`, { headers: { Cookie: `vt=${TOKEN}` }, redirect: 'manual' });
    assert.equal(res.status, 200, 'cookie authenticates static subresource');
  }

  // 4. PUT h1 → 204, then GET contains h1. h2 is a second live highlight that
  //    keeps test.md present in the manifest after h1 is later tombstoned —
  //    pullAnnotations is manifest-driven (handleManifest omits tombstones), so a
  //    file whose ONLY highlight is a tombstone would drop out of the file list
  //    and never be synced back. h2 keeps the file discoverable; the tombstone
  //    sync-back for h1 (step 6) then rides along on the same doc.
  {
    const put = await fetch(`${base}/api/annotations/test.md`, {
      method: 'PUT',
      headers: { ...auth, 'Content-Type': 'application/json' },
      body: JSON.stringify({ highlights: [
        { id: 'h1', color: 'yellow', segments: [{ blockLine: 2 }], updatedAt: 100 },
        { id: 'h2', color: 'green', segments: [{ blockLine: 4 }], updatedAt: 100 },
      ] }),
    });
    assert.equal(put.status, 204, 'PUT highlight → 204');
    const get = await fetch(`${base}/api/annotations/test.md`, { headers: auth });
    assert.equal(get.status, 200);
    const doc = await get.json();
    assert.ok(doc.highlights.some((h) => h.id === 'h1' && !h.deleted), 'doc contains live h1');
  }

  // 5. PUT tombstone → 204; GET retains tombstone; manifest excludes h1.
  {
    const put = await fetch(`${base}/api/annotations/test.md`, {
      method: 'PUT',
      headers: { ...auth, 'Content-Type': 'application/json' },
      body: JSON.stringify({ highlights: [{ id: 'h1', deleted: true, updatedAt: 200, segments: [{ blockLine: 2 }] }] }),
    });
    assert.equal(put.status, 204, 'PUT tombstone → 204');
    const get = await fetch(`${base}/api/annotations/test.md`, { headers: auth });
    const doc = await get.json();
    const h1 = doc.highlights.find((h) => h.id === 'h1');
    assert.ok(h1 && h1.deleted === true, 'tombstone retained on GET');
    const man = await (await fetch(`${base}/api/annotations-manifest`, { headers: auth })).json();
    assert.ok(!man.entries.some((e) => e.id === 'h1'), 'manifest excludes tombstoned h1');
  }

  // 6. Desktop sync-back: pullAnnotations writes a sidecar with h1 as a tombstone.
  {
    const sidecar = mkdtemp('cloud-sidecar-');
    t.after(() => fs.rmSync(sidecar, { recursive: true, force: true }));
    await pullAnnotations({ base, token: TOKEN, sidecarDir: sidecar });
    const dest = path.join(sidecar, 'test.md.json');
    assert.ok(fs.existsSync(dest), 'pullAnnotations wrote test.md.json');
    const doc = JSON.parse(fs.readFileSync(dest, 'utf8'));
    assert.ok(doc.highlights.some((h) => h.id === 'h1' && h.deleted === true), 'synced sidecar has h1 tombstone');
  }
}

// ── test body ────────────────────────────────────────────────────────────────

test('cloud round-trip: gate + write/read + tombstone + manifest + sync-back', { timeout: 120000 }, async (t) => {
  const dist = publishFixture();
  t.after(() => fs.rmSync(dist, { recursive: true, force: true }));

  const port = await pickFreePort();
  let server = null;
  // CLOUD_ITEST_FORCE_FALLBACK=1 skips wrangler to exercise the plain-Node path.
  if (process.env.CLOUD_ITEST_FORCE_FALLBACK !== '1') {
    try {
      // PRIMARY: wrangler.
      server = await startWrangler(dist, port);
    } catch {
      server = null;
    }
  }
  if (!server) {
    // FALLBACK: plain-Node harness on a fresh port (the wrangler port may be
    // half-bound after a failed boot).
    const fbPort = await pickFreePort();
    server = await startFallback(dist, fbPort);
    server.port = fbPort;
  } else {
    server.port = port;
  }

  const base = `http://127.0.0.1:${server.port}`;
  // eslint-disable-next-line no-console
  console.log(`[cloud-integration] server = ${server.label} @ ${base}`);
  try {
    await runRoundTrip(t, base);
  } finally {
    await server.stop();
  }
});
