// Offline write-queue — enqueue annotation PUT failures (network errors only);
// drain on reconnect. Storage-agnostic: inject a `store` seam for unit tests;
// defaults to IndexedDB when running in a browser.
//
// UMD pattern, same as annotation-merge.js.
(function (root) {
  'use strict';

  // ---------------------------------------------------------------------------
  // Default IndexedDB-backed store (browser only, created lazily)
  // ---------------------------------------------------------------------------
  var IDB_DB_NAME = 'viewer-write-queue';
  var IDB_STORE_NAME = 'items';

  function openDb() {
    return new Promise(function (resolve, reject) {
      var req = indexedDB.open(IDB_DB_NAME, 1);
      req.onupgradeneeded = function (e) {
        var db = e.target.result;
        if (!db.objectStoreNames.contains(IDB_STORE_NAME)) {
          db.createObjectStore(IDB_STORE_NAME, { autoIncrement: true });
        }
      };
      req.onsuccess = function (e) { resolve(e.target.result); };
      req.onerror = function (e) { reject(e.target.error); };
    });
  }

  // Builds an IDB-backed store conforming to { add, getAll, delete }.
  // Returns null when indexedDB is not available (Node / test environments).
  function buildIdbStore() {
    if (typeof indexedDB === 'undefined') return null;
    var dbPromise = openDb();

    function tx(mode, fn) {
      return dbPromise.then(function (db) {
        return new Promise(function (resolve, reject) {
          var t = db.transaction(IDB_STORE_NAME, mode);
          var s = t.objectStore(IDB_STORE_NAME);
          var req = fn(s);
          if (req) {
            req.onsuccess = function (e) { resolve(e.target.result); };
            req.onerror   = function (e) { reject(e.target.error); };
          } else {
            t.oncomplete = function () { resolve(); };
            t.onerror    = function (e) { reject(e.target.error); };
          }
        });
      });
    }

    function add(value) {
      return tx('readwrite', function (s) { return s.add(value); });
    }

    function getAll() {
      return dbPromise.then(function (db) {
        return new Promise(function (resolve, reject) {
          var t = db.transaction(IDB_STORE_NAME, 'readonly');
          var s = t.objectStore(IDB_STORE_NAME);
          var items = [];
          var req = s.openCursor();
          req.onsuccess = function (e) {
            var cursor = e.target.result;
            if (cursor) {
              items.push(Object.assign({ id: cursor.key }, cursor.value));
              cursor.continue();
            } else {
              resolve(items);
            }
          };
          req.onerror = function (e) { reject(e.target.error); };
        });
      });
    }

    function del(id) {
      return tx('readwrite', function (s) { return s.delete(id); });
    }

    return { add: add, getAll: getAll, delete: del };
  }

  // ---------------------------------------------------------------------------
  // createWriteQueue
  // ---------------------------------------------------------------------------
  //
  // opts.store — injectable backing store (for tests). If omitted, an
  //   IndexedDB-backed store is used (browser only). In Node where indexedDB
  //   is absent and no store is injected, the queue is a no-op (all methods
  //   resolve immediately with neutral values) so that requiring this module
  //   in Node does not throw.
  //
  // Returns { enqueue, drain, size }.
  //
  function createWriteQueue(opts) {
    var o = opts || {};
    var store = o.store || buildIdbStore();

    // If no backing store is available (Node without injection), return a
    // safe no-op queue so Node imports never throw.
    if (!store) {
      return {
        enqueue: function () { return Promise.resolve(); },
        drain:   function () { return Promise.resolve(); },
        size:    function () { return Promise.resolve(0); },
      };
    }

    // Enqueue a write. Adds { file, doc, ts } to the store.
    function enqueue(item) {
      return store.add({ file: item.file, doc: item.doc, ts: Date.now() });
    }

    // Drain: for each queued item in FIFO order, attempt putFn(item).
    // On success: remove from store.
    // On failure: leave in store; continue to the next item so a single
    //   bad item does not block later ones from being retried.
    function drain(putFn) {
      return store.getAll().then(function (items) {
        return items.reduce(function (chain, item) {
          return chain.then(function () {
            return Promise.resolve()
              .then(function () { return putFn(item); })
              .then(function () { return store.delete(item.id); })
              .catch(function () { /* leave queued; move on */ });
          });
        }, Promise.resolve());
      });
    }

    // Size: current count of queued items.
    function size() {
      return store.getAll().then(function (items) { return items.length; });
    }

    return { enqueue: enqueue, drain: drain, size: size };
  }

  var api = { createWriteQueue: createWriteQueue };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.createWriteQueue = createWriteQueue;
})(typeof window !== 'undefined' ? window : null);
