'use strict';
// Pure request handlers for the Cloudflare gate + annotation API. Self-contained:
// NO Node built-ins (runs in the Worker runtime), only the annotation-merge module.
const { mergeDocs } = require('./annotation-merge');

const SESSION_COOKIE = 'vt';

// FNV-1a 32-bit content hash → quoted hex (ETag-style). Sync, dependency-free,
// identical in Node and the Worker. (content-source.etagOf uses Node crypto,
// which is NOT available in Workers, so we cannot reuse it here.)
function revisionOf(str) {
  let h = 0x811c9dc5;
  const s = String(str);
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0;
  }
  return `"${h.toString(16).padStart(8, '0')}"`;
}

// Length-checked, accumulator-based bearer compare (no early-exit on content).
function safeEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string') return false;
  if (a.length !== b.length) return false;
  let acc = 0;
  for (let i = 0; i < a.length; i++) acc |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return acc === 0;
}

function bearerToken(authHeader) {
  if (typeof authHeader !== 'string') return null;
  const m = /^Bearer\s+(.+)$/.exec(authHeader.trim());
  return m ? m[1] : null;
}

function cookieToken(cookieHeader) {
  if (typeof cookieHeader !== 'string') return null;
  for (const part of cookieHeader.split(';')) {
    const eq = part.indexOf('=');
    if (eq === -1) continue;
    if (part.slice(0, eq).trim() === SESSION_COOKIE) return part.slice(eq + 1).trim();
  }
  return null;
}

function isAuthorized(authHeader, expected) {
  if (!expected) return false;
  const tok = bearerToken(authHeader);
  return tok != null && safeEqual(tok, expected);
}

function serializeSessionCookie(token) {
  // ~400-day persistent session cookie. Secure is honored on https and on
  // http://localhost (a secure context), so the local e2e works too.
  return `${SESSION_COOKIE}=${token}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=34560000`;
}

// Mutate `response` (or a copy you pass in) to carry the session Set-Cookie
// AND Cache-Control: no-store.  Pure: operates only on the passed Response,
// no globals.  Works in the Worker runtime and in Node 18+ (both expose a
// global Response with a mutable .headers).
function applyGateCookie(response, token) {
  response.headers.append('Set-Cookie', serializeSessionCookie(token));
  // Never let an edge/intermediate cache a per-user Set-Cookie response.
  response.headers.set('Cache-Control', 'no-store');
  return response;
}

// Gate: null (proceed) | { setCookie: <token> } (proceed AND set the session
// cookie) | Response(404) (block). Authorized via Authorization header OR the
// session cookie OR a ?k= bootstrap. The 404 body is generic — no hint the
// site exists.
async function handleGate(request, env) {
  const expected = env && env.token;
  const get = request.headers && request.headers.get ? (k) => request.headers.get(k) : () => null;
  if (isAuthorized(get('Authorization'), expected)) return null;
  if (expected && safeEqual(cookieToken(get('Cookie')) || '', expected)) return null;
  try {
    const k = new URL(request.url).searchParams.get('k');
    if (expected && k && safeEqual(k, expected)) return { setCookie: expected };
  } catch { /* malformed URL → fall through to 404 */ }
  return new Response('Not found', { status: 404, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}

function normalizeWhitespace(v) { return String(v || '').replace(/[ \t\r\n]+/g, ' ').trim(); }

function minLine(entry) {
  let best = Infinity;
  for (const s of (entry && entry.segments) || []) {
    if (typeof s.blockLine === 'number') best = Math.min(best, s.blockLine);
    if (typeof s.tableLine === 'number') best = Math.min(best, s.tableLine);
  }
  return Number.isFinite(best) ? best : 0;
}

// Cloud sidecar normalize — mirrors serve.js normalizeAnnotationDoc but PRESERVES
// updatedAt (int, default 0) and the deleted tombstone flag.
function normalizeCloudDoc(file, value) {
  const src = value && typeof value === 'object' ? value : {};
  const highlights = Array.isArray(src.highlights) ? src.highlights : [];
  return {
    version: 1,
    file,
    highlights: highlights.map((e) => {
      const out = {
        id: e.id,
        file,
        color: e.color || 'yellow',
        backend: 'sidecar',
        excerpt: normalizeWhitespace(e.excerpt || ''),
        segments: Array.isArray(e.segments) ? e.segments : [],
        updatedAt: Number(e.updatedAt) || 0,
      };
      if (e.deleted) out.deleted = true;
      return out;
    }),
  };
}

const keyFor = (file) => `ann:${file}`;

async function readDoc(kv, file) {
  const raw = await kv.get(keyFor(file));
  if (!raw) return { version: 1, file, highlights: [] };
  try { return normalizeCloudDoc(file, JSON.parse(raw)); }
  catch { return { version: 1, file, highlights: [] }; }
}

function jsonResponse(obj, status, extraHeaders) {
  const body = JSON.stringify(obj);
  return new Response(status === 204 ? null : body, {
    status,
    headers: Object.assign({ 'Content-Type': 'application/json; charset=utf-8' }, extraHeaders || {}),
  });
}

async function handleGetAnnotation(request, env, file) {
  const doc = await readDoc(env.kv, file);
  const rev = revisionOf(JSON.stringify(doc));
  return jsonResponse(doc, 200, { 'ETag': rev, 'X-Annotations-Revision': rev, 'Cache-Control': 'no-store' });
}

async function handlePutAnnotation(request, env, file) {
  let incoming;
  try { incoming = await request.json(); }
  catch { return new Response('Invalid JSON', { status: 400 }); }
  const stored = await readDoc(env.kv, file);
  const merged = normalizeCloudDoc(file, mergeDocs(stored, incoming, file));
  const json = JSON.stringify(merged);
  await env.kv.put(keyFor(file), json);
  const rev = revisionOf(json);
  return new Response(null, { status: 204, headers: { 'ETag': rev, 'X-Annotations-Revision': rev } });
}

async function handleManifest(request, env) {
  const { keys } = await env.kv.list({ prefix: 'ann:' });
  const files = keys.map(({ name }) => name.slice('ann:'.length));
  const entries = [];
  for (const file of files) {
    const doc = await readDoc(env.kv, file);
    for (const h of doc.highlights) {
      if (h.deleted) continue;
      const line = minLine(h);
      entries.push({ id: h.id, file, backend: 'sidecar', color: h.color || 'yellow', excerpt: h.excerpt || '', lineStart: line, lineEnd: line });
    }
  }
  entries.sort((a, b) => (a.file === b.file ? (a.lineStart - b.lineStart) : (a.file < b.file ? -1 : 1)));
  return jsonResponse({ entries, files }, 200, { 'Cache-Control': 'no-store' });
}

module.exports = { SESSION_COOKIE, revisionOf, isAuthorized, serializeSessionCookie, applyGateCookie, handleGate, normalizeCloudDoc, handleGetAnnotation, handlePutAnnotation, handleManifest };
