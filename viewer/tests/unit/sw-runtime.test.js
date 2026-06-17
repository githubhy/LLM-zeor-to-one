'use strict';
// Unit tests for viewer/lib/sw-runtime.js — pure helpers; run in Node (no DOM/SW globals).
const test = require('node:test');
const assert = require('node:assert/strict');

// sw-runtime.js exports via CommonJS when module.exports is present (Node).
const { classifyRequest, cacheNameFor, decorateRequest, strategyFor } = require('../../lib/sw-runtime');

// ─── cacheNameFor ─────────────────────────────────────────────────────────────
test('cacheNameFor: with version', () => {
  assert.equal(cacheNameFor('abc123'), 'viewer-pwa-abc123');
});
test('cacheNameFor: no version falls back to dev', () => {
  assert.equal(cacheNameFor(), 'viewer-pwa-dev');
});

// ─── classifyRequest ──────────────────────────────────────────────────────────
const H = 'http://h';

test('classifyRequest: index.html → shell', () => {
  assert.equal(classifyRequest(`${H}/index.html`, H), 'shell');
});
test('classifyRequest: root path → shell', () => {
  assert.equal(classifyRequest(`${H}/`, H), 'shell');
});
test('classifyRequest: viewer.js → shell', () => {
  assert.equal(classifyRequest(`${H}/viewer.js`, H), 'shell');
});
test('classifyRequest: style.css → shell', () => {
  assert.equal(classifyRequest(`${H}/style.css`, H), 'shell');
});
test('classifyRequest: manifest.webmanifest → shell', () => {
  assert.equal(classifyRequest(`${H}/manifest.webmanifest`, H), 'shell');
});
test('classifyRequest: vendor/katex.min.js → vendor', () => {
  assert.equal(classifyRequest(`${H}/vendor/katex.min.js`, H), 'vendor');
});
test('classifyRequest: icons/icon-192.png → vendor', () => {
  assert.equal(classifyRequest(`${H}/icons/icon-192.png`, H), 'vendor');
});
test('classifyRequest: lib/backend.js → vendor', () => {
  assert.equal(classifyRequest(`${H}/lib/backend.js`, H), 'vendor');
});
test('classifyRequest: content/x.md → content', () => {
  assert.equal(classifyRequest(`${H}/content/x.md`, H), 'content');
});
test('classifyRequest: files.json → content', () => {
  assert.equal(classifyRequest(`${H}/files.json`, H), 'content');
});
test('classifyRequest: git-info.json → content', () => {
  assert.equal(classifyRequest(`${H}/git-info.json`, H), 'content');
});
test('classifyRequest: api/annotations/x → api', () => {
  assert.equal(classifyRequest(`${H}/api/annotations/x`, H), 'api');
});
test('classifyRequest: api/annotations-manifest → api', () => {
  assert.equal(classifyRequest(`${H}/api/annotations-manifest`, H), 'api');
});
test('classifyRequest: cross-origin → passthrough', () => {
  assert.equal(classifyRequest('http://other/x', H), 'passthrough');
});

// ─── strategyFor ──────────────────────────────────────────────────────────────
test('strategyFor: shell → cache-first', () => {
  assert.equal(strategyFor('shell'), 'cache-first');
});
test('strategyFor: vendor → cache-first', () => {
  assert.equal(strategyFor('vendor'), 'cache-first');
});
test('strategyFor: content → network-first', () => {
  assert.equal(strategyFor('content'), 'network-first');
});
test('strategyFor: api → network-first', () => {
  assert.equal(strategyFor('api'), 'network-first');
});
test('strategyFor: passthrough → passthrough', () => {
  assert.equal(strategyFor('passthrough'), 'passthrough');
});

// ─── decorateRequest ──────────────────────────────────────────────────────────
// Minimal fake Headers that behaves like the Web API (set/get/entries).
class FakeHeaders {
  constructor(init) {
    this._map = {};
    if (init && typeof init === 'object') {
      for (const [k, v] of Object.entries(init)) this._map[k.toLowerCase()] = v;
    }
  }
  set(name, value) { this._map[name.toLowerCase()] = value; }
  get(name) { return this._map[name.toLowerCase()] ?? null; }
  entries() { return Object.entries(this._map)[Symbol.iterator](); }
}

// Minimal fake Request that captures url + init.
class FakeRequest {
  constructor(url, init) {
    this.url = typeof url === 'string' ? url : url.url;
    this.method = (init && init.method) || 'GET';
    this.headers = (init && init.headers) || new FakeHeaders();
  }
}

test('decorateRequest: non-null token attaches Authorization header', () => {
  const req = new FakeRequest('http://h/files.json', { method: 'GET', headers: new FakeHeaders() });
  const decorated = decorateRequest(req, 'tok123', FakeRequest);
  assert.ok(decorated instanceof FakeRequest, 'result should be a FakeRequest');
  assert.equal(decorated.headers.get('authorization'), 'Bearer tok123');
});

test('decorateRequest: null token returns original request unchanged', () => {
  const req = new FakeRequest('http://h/files.json', { method: 'GET', headers: new FakeHeaders() });
  const result = decorateRequest(req, null, FakeRequest);
  assert.strictEqual(result, req, 'should return same object when token is null');
});

test('decorateRequest: preserves pre-existing headers alongside Authorization', () => {
  const src = new FakeHeaders({ 'X-Test': '1' });
  const req = new FakeRequest('http://h/files.json', { method: 'GET', headers: src });
  const decorated = decorateRequest(req, 'tok456', FakeRequest);
  assert.ok(decorated instanceof FakeRequest, 'result should be a FakeRequest');
  assert.equal(decorated.headers.get('x-test'), '1', 'X-Test header should be preserved');
  assert.equal(decorated.headers.get('authorization'), 'Bearer tok456', 'Authorization header should be set');
});

test('classifyRequest: annotations-manifest.json → content', () => {
  assert.equal(classifyRequest(`${H}/annotations-manifest.json`, H), 'content');
});

// ─── tokenRecord / readToken ───────────────────────────────────────────────────
const { tokenRecord, readToken } = require('../../lib/sw-runtime');

test('tokenRecord: returns object with id=auth and given token', () => {
  const rec = tokenRecord('abc123');
  assert.deepEqual(rec, { id: 'auth', token: 'abc123' });
});

test('tokenRecord: null token is preserved as-is', () => {
  const rec = tokenRecord(null);
  assert.deepEqual(rec, { id: 'auth', token: null });
});

test('readToken: returns token string from a valid record', () => {
  assert.equal(readToken({ id: 'auth', token: 'mytoken' }), 'mytoken');
});

test('readToken: returns null when record is null', () => {
  assert.strictEqual(readToken(null), null);
});

test('readToken: returns null when record is undefined', () => {
  assert.strictEqual(readToken(undefined), null);
});

test('readToken: returns null when record has no token property', () => {
  assert.strictEqual(readToken({ id: 'auth' }), null);
});
