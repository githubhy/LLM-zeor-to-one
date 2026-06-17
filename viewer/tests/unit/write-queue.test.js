'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');

// require write-queue.js — must not crash in Node (no real indexedDB available)
const { createWriteQueue } = require('../../lib/write-queue');

// ---------------------------------------------------------------------------
// Map-backed fake store (seam)
// ---------------------------------------------------------------------------
function makeFakeStore() {
  let nextId = 1;
  const map = new Map(); // id -> value (insertion-order FIFO)
  return {
    async add(value) {
      const id = nextId++;
      map.set(id, Object.assign({}, value));
      return id;
    },
    async getAll() {
      return [...map.entries()].map(([id, v]) => Object.assign({ id }, v));
    },
    async delete(id) {
      map.delete(id);
    },
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test('enqueue persists an item (size() and getAll reflect it)', async () => {
  const store = makeFakeStore();
  const q = createWriteQueue({ store });

  assert.equal(await q.size(), 0);

  await q.enqueue({ file: 'a.md', doc: { highlights: [] } });

  assert.equal(await q.size(), 1);

  const all = await store.getAll();
  assert.equal(all.length, 1);
  assert.equal(all[0].file, 'a.md');
});

test('drain calls putFn for each item in FIFO order', async () => {
  const store = makeFakeStore();
  const q = createWriteQueue({ store });

  await q.enqueue({ file: 'first.md', doc: { highlights: [{ id: '1' }] } });
  await q.enqueue({ file: 'second.md', doc: { highlights: [{ id: '2' }] } });

  const order = [];
  await q.drain(async (item) => {
    order.push(item.file);
  });

  assert.deepEqual(order, ['first.md', 'second.md']);
});

test('drain removes only items whose putFn resolved; failed item stays queued', async () => {
  const store = makeFakeStore();
  const q = createWriteQueue({ store });

  await q.enqueue({ file: 'ok.md', doc: {} });
  await q.enqueue({ file: 'fail.md', doc: {} });
  await q.enqueue({ file: 'ok2.md', doc: {} });

  await q.drain(async (item) => {
    if (item.file === 'fail.md') throw new Error('network error');
  });

  // fail.md should still be queued; ok.md and ok2.md should be removed
  assert.equal(await q.size(), 1);
  const remaining = await store.getAll();
  assert.equal(remaining[0].file, 'fail.md');
});

test('size() returns current queued count', async () => {
  const store = makeFakeStore();
  const q = createWriteQueue({ store });

  assert.equal(await q.size(), 0);

  await q.enqueue({ file: 'a.md', doc: {} });
  assert.equal(await q.size(), 1);

  await q.enqueue({ file: 'b.md', doc: {} });
  assert.equal(await q.size(), 2);

  // drain all successfully
  await q.drain(async () => {});
  assert.equal(await q.size(), 0);
});

test('drain after partial failure: size reflects only remaining failed items', async () => {
  const store = makeFakeStore();
  const q = createWriteQueue({ store });

  await q.enqueue({ file: 'a.md', doc: {} });
  await q.enqueue({ file: 'b.md', doc: {} }); // will fail
  await q.enqueue({ file: 'c.md', doc: {} });

  await q.drain(async (item) => {
    if (item.file === 'b.md') throw new Error('offline');
  });

  assert.equal(await q.size(), 1);
  const left = await store.getAll();
  assert.equal(left[0].file, 'b.md');
});
