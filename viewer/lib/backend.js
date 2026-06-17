// Backend adapter — the only module that talks to a server/transport.
// Exposes `window.createLocalServerBackend` (browser) and module.exports (Node/tests).
//
// A backend reproduces the exact request/response contract of viewer/serve.js so
// viewer.js never calls fetch()/WebSocket directly. Cloud and native backends
// implement the same surface (see docs/superpowers/specs/2026-06-07-ios-pwa-viewer-design.md).

(function (root) {
  'use strict';

  // Lazily import write-queue. In Node, require() is available; in the browser the
  // UMD module registers window.createWriteQueue before backend.js runs.
  function getCreateWriteQueue() {
    if (typeof createWriteQueue !== 'undefined') return createWriteQueue;
    try { return require('./write-queue').createWriteQueue; } catch { return null; }
  }

  function revisionFromResponse(res, fallback) {
    return res.headers.get('ETag') || res.headers.get(fallback || 'X-Document-Revision') || null;
  }

  const TOKEN_KEY = 'viewer:token';
  function bootstrapToken(deps) {
    const d = deps || {};
    const loc = d.location, ls = d.localStorage, hist = d.history;
    try {
      const search = loc && typeof loc.search === 'string' ? loc.search : '';
      const m = /[?&]k=([^&]+)/.exec(search);
      if (m) {
        const token = decodeURIComponent(m[1]);
        if (ls) ls.setItem(TOKEN_KEY, token);
        if (hist && hist.replaceState && loc) {
          const stripped = (loc.pathname || '/') + search.replace(/([?&])k=[^&]*(&|$)/, '$1').replace(/[?&]$/, '');
          hist.replaceState({}, '', stripped || (loc.pathname || '/'));
        }
        return token;
      }
      return (ls && ls.getItem(TOKEN_KEY)) || null;
    } catch { return null; }
  }

  function createLocalServerBackend(opts) {
    const o = opts || {};
    const fetchImpl = o.fetch || (typeof fetch !== 'undefined' ? fetch : null);
    const WSImpl = o.WebSocketImpl || (typeof WebSocket !== 'undefined' ? WebSocket : null);
    const getLocation = o.getLocation
      || (() => (typeof location !== 'undefined' ? location : { protocol: 'http:', host: 'localhost' }));

    async function listFiles() {
      const res = await fetchImpl('/api/files');
      const data = await res.json();
      return {
        files: Array.isArray(data.files) ? data.files : [],
        roots: Array.isArray(data.roots) ? data.roots : null,
        defaultFile: data.defaultFile || null,
      };
    }

    async function getMarkdown(file) {
      const res = await fetchImpl(`/api/md/${encodeURIComponent(file)}`);
      if (!res.ok) throw new Error(`Failed to fetch ${file}: ${res.status}`);
      const text = await res.text();
      return { text, revision: revisionFromResponse(res) };
    }

    async function putMarkdown(file, source, expectedRevision) {
      try {
        const headers = { 'Content-Type': 'text/plain; charset=utf-8' };
        if (expectedRevision) headers['If-Match'] = expectedRevision;
        const res = await fetchImpl(`/api/md/${encodeURIComponent(file)}`, {
          method: 'PUT', headers, body: source,
        });
        return {
          ok: res.ok,
          status: res.status,
          revision: revisionFromResponse(res),
          conflict: res.status === 409 || res.status === 428,
        };
      } catch (err) {
        return { ok: false, status: err.message || String(err), conflict: false };
      }
    }

    async function getAnnotations(file) {
      try {
        const res = await fetchImpl(`/api/highlights/${encodeURIComponent(file)}`);
        if (!res.ok) return null;
        const doc = await res.json();
        return { doc, revision: revisionFromResponse(res, 'X-Annotations-Revision') };
      } catch {
        return null;
      }
    }

    async function putAnnotations(file, doc, expectedRevision, documentRevision) {
      try {
        const headers = { 'Content-Type': 'application/json; charset=utf-8' };
        if (expectedRevision) headers['If-Match'] = expectedRevision;
        if (documentRevision) headers['X-Document-Revision'] = documentRevision;
        const res = await fetchImpl(`/api/highlights/${encodeURIComponent(file)}`, {
          method: 'PUT', headers, body: JSON.stringify(doc),
        });
        return {
          ok: res.ok,
          status: res.status,
          revision: revisionFromResponse(res, 'X-Annotations-Revision'),
          conflict: res.status === 409 || res.status === 428,
        };
      } catch (err) {
        return { ok: false, status: err.message || String(err), conflict: false };
      }
    }

    async function getManifest(file) {
      try {
        const url = file
          ? `/api/highlights-manifest?file=${encodeURIComponent(file)}`
          : '/api/highlights-manifest';
        const res = await fetchImpl(url);
        if (!res.ok) return null;
        const data = await res.json();
        return { entries: Array.isArray(data.entries) ? data.entries : [] };
      } catch {
        return null;
      }
    }

    async function getGitInfo() {
      try {
        const res = await fetchImpl('/api/git-info', { cache: 'no-store' });
        return res.ok ? await res.json() : { available: false, reason: 'http ' + res.status };
      } catch (err) {
        return { available: false, reason: String((err && err.message) || err) };
      }
    }

    function connectLiveReload(handlers) {
      const onMessage = (handlers && handlers.onMessage) || function () {};
      const onClose = (handlers && handlers.onClose) || function () {};
      if (!WSImpl) return { close() {} };
      const loc = getLocation();
      const protocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WSImpl(`${protocol}//${loc.host}`);
      ws.addEventListener('message', (e) => {
        let msg;
        try { msg = JSON.parse(e.data); } catch { return; }
        onMessage(msg);
      });
      ws.addEventListener('error', () => {});
      ws.addEventListener('close', () => { onClose(); });
      return { close() { try { ws.close(); } catch {} } };
    }

    return {
      kind: 'local-server',
      listFiles, getMarkdown, putMarkdown,
      getAnnotations, putAnnotations, getManifest,
      getGitInfo, connectLiveReload,
      flushQueue: async () => {},
    };
  }

  function createCloudBackend(opts) {
    const o = opts || {};
    const base = (o.base || '.').replace(/\/$/, '');
    const fetchImpl = o.fetch || (typeof fetch !== 'undefined' ? fetch : null);
    const version = o.version || null;
    const token = o.token || null;
    const RO = { ok: false, status: 'read-only', conflict: false };

    function headers(extra) {
      const h = Object.assign({}, extra);
      if (token) h.Authorization = 'Bearer ' + token;
      return h;
    }

    // Module-level write-queue instance for this cloud backend.
    // Created lazily so that Node/test imports of backend.js (which never call
    // putAnnotations in a way that needs IDB) don't open any IndexedDB.
    // The IDB guard inside createWriteQueue itself also prevents opening IDB in Node.
    // opts.writeQueue may inject a pre-built queue (used in tests and native shell).
    let _queue = o.writeQueue || null;
    function getQueue() {
      if (_queue) return _queue;
      const factory = getCreateWriteQueue();
      if (!factory) return null;
      _queue = factory();
      return _queue;
    }

    async function listFiles() {
      const res = await fetchImpl(`${base}/files.json`, { headers: headers() });
      const data = await res.json();
      return { files: Array.isArray(data.files) ? data.files : [], roots: Array.isArray(data.roots) ? data.roots : null, defaultFile: data.defaultFile || null, version: data.version || null };
    }
    async function getMarkdown(file) {
      const res = await fetchImpl(`${base}/content/${file}`, { headers: headers() });
      if (!res.ok) throw new Error(`Failed to fetch ${file}: ${res.status}`);
      return { text: await res.text(), revision: version };
    }
    async function getAnnotations(file) {
      try {
        const res = await fetchImpl(`${base}/api/annotations/${encodeURIComponent(file)}`, { headers: headers() });
        if (!res.ok) return null;
        return { doc: await res.json(), revision: revisionFromResponse(res, 'X-Annotations-Revision') };
      } catch { return null; }
    }
    async function getManifest(file) {
      try {
        const res = await fetchImpl(`${base}/api/annotations-manifest`, { headers: headers() });
        if (!res.ok) return null;
        const data = await res.json();
        const entries = Array.isArray(data.entries) ? data.entries : [];
        return { entries: file ? entries.filter((e) => e.file === file) : entries };
      } catch { return null; }
    }
    async function getGitInfo() {
      try {
        const res = await fetchImpl(`${base}/git-info.json`, { headers: headers() });
        return res.ok ? await res.json() : { available: false, reason: 'http ' + res.status };
      } catch (err) { return { available: false, reason: String((err && err.message) || err) }; }
    }
    async function putAnnotations(file, doc, expectedRevision, documentRevision) {
      let res;
      try {
        res = await fetchImpl(`${base}/api/annotations/${encodeURIComponent(file)}`, {
          method: 'PUT',
          headers: headers({ 'Content-Type': 'application/json; charset=utf-8' }),
          body: JSON.stringify(doc),
        });
      } catch (err) {
        // fetch() itself threw — this is a NETWORK error (offline, DNS, connection reset).
        // Enqueue for later replay and report optimistic success-pending to the UI.
        const q = getQueue();
        if (q) {
          let enqueued = false;
          try { await q.enqueue({ file, doc }); enqueued = true; } catch (e) {}
          if (enqueued) return { ok: true, queued: true, status: 0, conflict: false, revision: null };
          // IDB enqueue also failed (quota exceeded, private mode, storage unavailable).
          // Signal a real loss so the caller can surface an error toast.
          return { ok: false, dropped: true, status: 'offline+storage-unavailable', conflict: false };
        }
        // No queue available (should not happen in practice) — surface the error.
        return { ok: false, status: (err && err.message) || String(err), conflict: false };
      }
      // fetch() resolved — real server response. Return existing shape regardless of
      // status code so server-side 4xx/409 errors are NOT swallowed into the queue.
      return {
        ok: res.ok,
        status: res.status,
        revision: revisionFromResponse(res, 'X-Annotations-Revision'),
        conflict: res.status === 409,
      };
    }

    // Flush the write-queue: replay all queued annotation PUTs.
    // Called by viewer.js on the 'online' event and once at startup.
    // Each replay issues the full PUT; on network failure the item stays queued.
    async function flushQueue() {
      const q = getQueue();
      if (!q) return;
      await q.drain(async function (item) {
        const res = await fetchImpl(`${base}/api/annotations/${encodeURIComponent(item.file)}`, {
          method: 'PUT',
          headers: headers({ 'Content-Type': 'application/json; charset=utf-8' }),
          body: JSON.stringify(item.doc),
        });
        // Only accept 2xx as success; non-ok response rejects so the item
        // stays queued and will be retried on the next flush.
        if (!res.ok) throw new Error('server ' + res.status);
      });
    }

    return {
      kind: 'cloud',
      listFiles, getMarkdown, getAnnotations, getManifest, getGitInfo,
      putMarkdown: async () => RO,
      putAnnotations,
      flushQueue,
      connectLiveReload: () => ({ close() {} }),
    };
  }

  function selectBackend(global) {
    const cfg = (global && global.VIEWER_CONFIG) || null;
    if (cfg && cfg.backend === 'cloud') {
      const token = bootstrapToken({ location: global && global.location, localStorage: global && global.localStorage, history: global && global.history });
      return createCloudBackend(Object.assign({}, cfg, { token }));
    }
    return createLocalServerBackend(cfg || undefined);
  }

  const api = { createLocalServerBackend, createCloudBackend, revisionFromResponse, selectBackend, bootstrapToken };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.createLocalServerBackend = createLocalServerBackend;
  if (root) root.createCloudBackend = createCloudBackend;
  if (root) root.selectBackend = selectBackend;
  if (root) root.bootstrapToken = bootstrapToken;
})(typeof window !== 'undefined' ? window : null);
