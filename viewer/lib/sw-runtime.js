// Service-worker runtime helpers — pure functions over URL/Request-like inputs.
// No DOM or SW globals so this unit-tests in Node. UMD: loads via importScripts
// in the SW (sets self.SwRuntime) and via require() in Node tests.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SwRuntime = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // Paths that constitute the app shell (exact matches after stripping leading /).
  const SHELL = new Set(['', 'index.html', 'viewer.js', 'style.css', 'manifest.webmanifest']);

  /**
   * Classify a request URL relative to selfOrigin into one of:
   *   'shell' | 'vendor' | 'content' | 'api' | 'passthrough'
   *
   * @param {string} rawUrl
   * @param {string} [selfOrigin]  e.g. 'http://localhost:5000' — cross-origin → passthrough
   * @returns {'shell'|'vendor'|'content'|'api'|'passthrough'}
   */
  function classifyRequest(rawUrl, selfOrigin) {
    var u;
    try { u = new URL(rawUrl, selfOrigin || 'http://x'); } catch (e) { return 'passthrough'; }
    if (selfOrigin && u.origin !== selfOrigin) return 'passthrough';
    var p = u.pathname.replace(/^\//, '');
    if (p.startsWith('vendor/') || p.startsWith('icons/') || p.startsWith('lib/')) return 'vendor';
    if (p.startsWith('api/')) return 'api';
    if (p.startsWith('content/') || p === 'files.json' || p === 'git-info.json' || p === 'annotations-manifest.json') return 'content';
    if (SHELL.has(p)) return 'shell';
    return 'passthrough';
  }

  /**
   * Build the versioned cache bucket name.
   * @param {string} [version]
   * @returns {string}
   */
  function cacheNameFor(version) {
    return 'viewer-pwa-' + (version || 'dev');
  }

  /**
   * Attach an Authorization header to a request when a token is available.
   * Accepts injected RequestCtor/FakeRequest so it is unit-testable in Node
   * where the global Request/Headers may or may not be present.
   *
   * @param {Request|{url:string,method?:string,headers?:any}} request
   * @param {string|null} token
   * @param {Function} [RequestCtor]  override Request constructor (for tests)
   * @returns {Request|typeof request}
   */
  function decorateRequest(request, token, RequestCtor) {
    var C = RequestCtor || (typeof Request !== 'undefined' ? Request : null);
    if (!token || !C) return request;
    var src = request.headers || {};
    var headers;
    if (typeof Headers !== 'undefined' && (src instanceof Headers || typeof src.entries === 'function')) {
      headers = new Headers();
      if (typeof src.entries === 'function') { for (var _a of src.entries()) headers.set(_a[0], _a[1]); }
      headers.set('Authorization', 'Bearer ' + token);
    } else {
      headers = {};
      if (typeof src.entries === 'function') { for (var _b of src.entries()) headers[_b[0]] = _b[1]; }
      else Object.assign(headers, src);
      headers['Authorization'] = 'Bearer ' + token;
    }
    return new C(request.url || request, {
      method: request.method || 'GET',
      headers: headers,
      mode: 'same-origin',
      credentials: 'include',
    });
  }

  /**
   * Map a request classification to a caching strategy.
   * @param {'shell'|'vendor'|'content'|'api'|'passthrough'} kind
   * @returns {'cache-first'|'network-first'|'passthrough'}
   */
  function strategyFor(kind) {
    if (kind === 'shell' || kind === 'vendor') return 'cache-first';
    if (kind === 'content' || kind === 'api') return 'network-first';
    return 'passthrough';
  }

  /**
   * Build the IDB record for storing a bearer token.
   * @param {string|null} token
   * @returns {{ id: 'auth', token: string|null }}
   */
  function tokenRecord(token) {
    return { id: 'auth', token: token };
  }

  /**
   * Extract the token string from an IDB auth record.
   * Returns null when the record is absent or carries no token property.
   * @param {{ token?: string|null }|null|undefined} record
   * @returns {string|null}
   */
  function readToken(record) {
    if (!record || !('token' in record)) return null;
    return record.token != null ? record.token : null; // normalizes undefined → null
  }

  return { classifyRequest, cacheNameFor, decorateRequest, strategyFor, tokenRecord, readToken };
});
