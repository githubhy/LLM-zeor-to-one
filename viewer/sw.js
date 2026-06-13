/* global self, caches, fetch, indexedDB */
/* Service worker — app-shell precache + network-first content strategy.
 * self.__VERSION and self.__PRECACHE are prepended by publish.js at build time.
 * Bearer token is stored in IndexedDB (DB: viewer-pwa-auth, store: auth) and
 * injected on forwarded fetches for forward-compat / offline auth. The HttpOnly
 * vt= cookie still gates online requests automatically. */
importScripts('lib/sw-runtime.js');

const { classifyRequest, cacheNameFor, decorateRequest, strategyFor, tokenRecord, readToken } = self.SwRuntime;

const VERSION  = self.__VERSION  || 'dev';
const PRECACHE = self.__PRECACHE || [];
const CACHE    = cacheNameFor(VERSION);
const ORIGIN   = self.location.origin;

// ─── install: open versioned cache and prime the precache list ────────────────
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => c.addAll(PRECACHE))
      .then(() => self.skipWaiting()),
  );
});

// ─── activate: delete stale viewer-pwa-* caches and claim all clients ─────────
self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys
        .filter((k) => k.startsWith('viewer-pwa-') && k !== CACHE)
        .map((k) => caches.delete(k)),
    );
    await self.clients.claim();
  })());
});

// ─── IndexedDB helpers ────────────────────────────────────────────────────────
const IDB_NAME  = 'viewer-pwa-auth';
const IDB_STORE = 'auth';

function openAuthDb() {
  return new Promise(function (resolve, reject) {
    var req = indexedDB.open(IDB_NAME, 1);
    req.onupgradeneeded = function (e) {
      var db = e.target.result;
      if (!db.objectStoreNames.contains(IDB_STORE)) {
        db.createObjectStore(IDB_STORE, { keyPath: 'id' });
      }
    };
    req.onsuccess = function (e) { resolve(e.target.result); };
    req.onerror   = function (e) { reject(e.target.error); };
  });
}

function idbPut(db, record) {
  return new Promise(function (resolve, reject) {
    var tx  = db.transaction(IDB_STORE, 'readwrite');
    var req = tx.objectStore(IDB_STORE).put(record);
    req.onsuccess = function () { resolve(); };
    req.onerror   = function (e) { reject(e.target.error); };
  });
}

function idbGet(db, key) {
  return new Promise(function (resolve, reject) {
    var tx  = db.transaction(IDB_STORE, 'readonly');
    var req = tx.objectStore(IDB_STORE).get(key);
    req.onsuccess = function (e) { resolve(e.target.result); };
    req.onerror   = function (e) { reject(e.target.error); };
  });
}

// ─── token: IDB-backed bearer token read ─────────────────────────────────────
// Memoize a single IDBDatabase connection for the SW's lifetime so that
// repeated getToken() calls on every fetch share one handle (no leak).
var _authDbPromise = null;
function authDb() { return _authDbPromise || (_authDbPromise = openAuthDb()); }

// Read IDB on every call — connection is memoized so the round-trip is cheap,
// and it eliminates the stale-token window when a token is rotated between
// SW respawns (an in-memory cache would serve the pre-rotation value).
async function getToken() {
  try {
    var db  = await authDb();
    var rec = await idbGet(db, 'auth');
    return readToken(rec);
  } catch (_) {
    return null;
  }
}

// ─── message: accept token from page and persist to IDB ──────────────────────
self.addEventListener('message', function (event) {
  if (!event.data || event.data.type !== 'token') return;
  var token = event.data.token;
  authDb().then(function (db) {
    return idbPut(db, tokenRecord(token));
  }).catch(function () { /* IDB write failure is non-fatal */ });
});

// ─── fetch: cache-first for shell/vendor; network-first for content/api ───────
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const kind  = classifyRequest(req.url, ORIGIN);
  const strat = strategyFor(kind);
  if (strat === 'passthrough') return;

  e.respondWith((async () => {
    const token = await getToken();
    const wire  = decorateRequest(req, token);
    const cache = await caches.open(CACHE);

    if (strat === 'cache-first') {
      const hit = await cache.match(req);
      if (hit) return hit;
      const res = await fetch(wire);
      if (res.ok) cache.put(req, res.clone());
      return res;
    }

    // network-first
    try {
      const res = await fetch(wire);
      if (res.ok) cache.put(req, res.clone());
      return res;
    } catch (err) {
      const hit = await cache.match(req);
      if (hit) return hit;
      throw err;
    }
  })());
});
