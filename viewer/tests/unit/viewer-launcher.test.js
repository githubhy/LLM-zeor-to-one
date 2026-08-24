const test = require('node:test');
const assert = require('node:assert');
const { execFileSync, execFile } = require('node:child_process');
const { mkdtempSync, writeFileSync, rmSync, existsSync } = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const net = require('node:net');
const http = require('node:http');

const SCRIPT = path.join(__dirname, '..', '..', 'tools', 'viewer-launcher.sh');

// A launcher run is hermetic: its PID/log state and its served corpus both live
// in a temp dir, so tests never touch the developer's real viewer state.
function mkSandbox() {
  const dir = mkdtempSync(path.join(tmpdir(), 'viewer-launch-'));
  const corpus = path.join(dir, 'corpus');
  require('node:fs').mkdirSync(corpus);
  writeFileSync(path.join(corpus, 'hello.md'), '# Hello\n');
  return { dir, corpus, state: path.join(dir, 'state') };
}

// listen() is async: the port is only known once 'listening' fires. Binding to
// 0 and closing hands back a port the OS has just proven is free.
function freePort() {
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.on('error', reject);
    srv.listen(0, '127.0.0.1', () => {
      const p = srv.address().port;
      srv.close(() => resolve(p));
    });
  });
}

// Run the launcher synchronously. Never throws on non-zero exit — the exit code
// IS the assertion target for most of these cases.
function run(args, sb, env = {}) {
  const res = require('node:child_process').spawnSync('/bin/bash', [SCRIPT, ...args], {
    encoding: 'utf8',
    env: {
      ...process.env,
      VIEWER_STATE_DIR: sb.state,
      VIEWER_NO_BROWSER: '1',
      ...env,
    },
  });
  return { code: res.status, out: res.stdout || '', err: res.stderr || '' };
}

function get(port, p = '/api/files') {
  return new Promise((resolve, reject) => {
    const req = http.get({ host: '127.0.0.1', port, path: p, timeout: 3000 }, (res) => {
      let body = '';
      res.on('data', (c) => (body += c));
      res.on('end', () => resolve({ status: res.statusCode, body }));
    });
    req.on('error', reject);
    req.on('timeout', () => req.destroy(new Error('timeout')));
  });
}

test('status on a clean state dir reports stopped and exits non-zero', () => {
  const sb = mkSandbox();
  try {
    const r = run(['status'], sb);
    assert.match(r.out + r.err, /stopped/i);
    assert.notStrictEqual(r.code, 0, 'stopped must be a non-zero exit so shell callers can branch on it');
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('a missing node interpreter fails loudly instead of silently doing nothing', async () => {
  const sb = mkSandbox();
  // Pin a free port: on the default 3000 this would find the developer's own
  // running viewer, report "already running", and pass for the wrong reason.
  const port = await freePort();
  try {
    const r = run(['start', '-p', String(port), '--', sb.corpus], sb, { VIEWER_NODE: '/nonexistent/node' });
    assert.notStrictEqual(r.code, 0);
    assert.match(r.out + r.err, /node/i);
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('a stale pid file is not mistaken for a running server', () => {
  const sb = mkSandbox();
  try {
    require('node:fs').mkdirSync(sb.state, { recursive: true });
    // PID 999999 is above the default macOS pid_max and cannot be alive.
    writeFileSync(path.join(sb.state, 'viewer.pid'), '999999\n');
    const r = run(['status'], sb);
    assert.match(r.out + r.err, /stopped/i);
    assert.notStrictEqual(r.code, 0);
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('start brings the viewer up, status sees it, stop takes it down', async () => {
  const sb = mkSandbox();
  const port = await freePort();
  try {
    const s = run(['start', '-p', String(port), '--', sb.corpus], sb);
    assert.strictEqual(s.code, 0, `start failed: ${s.out}${s.err}`);

    const st = run(['status'], sb);
    assert.strictEqual(st.code, 0, `status failed: ${st.out}${st.err}`);
    assert.match(st.out, new RegExp(String(port)));

    const res = await get(port);
    assert.strictEqual(res.status, 200);
    const payload = JSON.parse(res.body);
    assert.ok(Array.isArray(payload.files), 'served corpus should expose a files array');

    const k = run(['stop'], sb);
    assert.strictEqual(k.code, 0, `stop failed: ${k.out}${k.err}`);

    await assert.rejects(() => get(port), 'port must be closed after stop');
    assert.notStrictEqual(run(['status'], sb).code, 0);
  } finally {
    run(['stop'], sb);
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('start is idempotent — a second start reuses the running server', async () => {
  const sb = mkSandbox();
  const port = await freePort();
  try {
    assert.strictEqual(run(['start', '-p', String(port), '--', sb.corpus], sb).code, 0);
    const pid1 = require('node:fs').readFileSync(path.join(sb.state, 'viewer.pid'), 'utf8').trim();

    const again = run(['start', '-p', String(port), '--', sb.corpus], sb);
    assert.strictEqual(again.code, 0);
    assert.match(again.out + again.err, /already running/i);

    const pid2 = require('node:fs').readFileSync(path.join(sb.state, 'viewer.pid'), 'utf8').trim();
    assert.strictEqual(pid2, pid1, 'must not spawn a second server on the same port');
  } finally {
    run(['stop'], sb);
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('a foreign server on the port is refused, not adopted', async () => {
  const sb = mkSandbox();
  const port = await freePort();
  const foreign = http.createServer((req, res) => { res.writeHead(200); res.end('not the viewer'); });
  await new Promise((r) => foreign.listen(port, '127.0.0.1', r));
  try {
    const s = run(['start', '-p', String(port), '--', sb.corpus], sb);
    assert.notStrictEqual(s.code, 0, 'must not report success when the port belongs to something else');
    assert.match(s.out + s.err, new RegExp(String(port)));
  } finally {
    run(['stop'], sb);
    await new Promise((r) => foreign.close(r));
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

// --- repo selection ---------------------------------------------------------
// The app is not bound to a repo: it resolves one at launch. Everything below
// runs with --no-ui, which turns every dialog into a failure exit instead, so
// the resolution logic is testable without a human clicking Finder dialogs.

const PICKER = path.join(__dirname, '..', '..', 'tools', 'pick-repo.sh');
const BUILDER = path.join(__dirname, '..', '..', 'tools', 'make-mac-app.sh');
const REAL_REPO = path.join(__dirname, '..', '..', '..');

function pick(args, sb, env = {}) {
  const r = require('node:child_process').spawnSync('/bin/bash', [PICKER, ...args], {
    encoding: 'utf8',
    env: { ...process.env, VIEWER_STATE_DIR: sb.state, ...env },
  });
  return { code: r.status, out: (r.stdout || '').trim(), err: r.stderr || '' };
}

// A directory that looks like a repo to the validator, without being one.
function fakeRepo(dir, name) {
  const fs = require('node:fs');
  const root = path.join(dir, name);
  fs.mkdirSync(path.join(root, 'viewer', 'tools'), { recursive: true });
  fs.writeFileSync(path.join(root, 'viewer', 'serve.js'), '// stub\n');
  const l = path.join(root, 'viewer', 'tools', 'viewer-launcher.sh');
  fs.writeFileSync(l, '#!/bin/bash\necho stub\n');
  fs.chmodSync(l, 0o755);
  return root;
}

test('validate accepts a viewer repo and rejects a bare directory', () => {
  const sb = mkSandbox();
  try {
    const good = fakeRepo(sb.dir, 'good');
    assert.strictEqual(pick(['validate', good], sb).code, 0);
    assert.notStrictEqual(pick(['validate', sb.corpus], sb).code, 0,
      'a directory with no viewer/ must not pass as a repo');
    assert.notStrictEqual(pick(['validate', path.join(good, 'viewer')], sb).code, 0,
      'viewer/ itself is not the repo root — its parent is');
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('resolve returns the remembered repo with no dialog', () => {
  const sb = mkSandbox();
  try {
    const a = fakeRepo(sb.dir, 'alpha');
    assert.strictEqual(pick(['remember', a], sb).code, 0);
    const r = pick(['resolve', '--no-ui'], sb);
    assert.strictEqual(r.code, 0, r.err);
    assert.strictEqual(r.out, a);
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('remember moves a repo to the head and does not duplicate it', () => {
  const sb = mkSandbox();
  try {
    const a = fakeRepo(sb.dir, 'alpha');
    const b = fakeRepo(sb.dir, 'beta');
    pick(['remember', a], sb);
    pick(['remember', b], sb);
    assert.deepStrictEqual(pick(['list'], sb).out.split('\n'), [b, a]);

    pick(['remember', a], sb);
    assert.deepStrictEqual(pick(['list'], sb).out.split('\n'), [a, b],
      'a re-picked repo moves to the head rather than being appended again');
    assert.strictEqual(pick(['resolve', '--no-ui'], sb).out, a);
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('a moved repo ages out of the recents instead of being offered', () => {
  const sb = mkSandbox();
  try {
    const a = fakeRepo(sb.dir, 'alpha');
    const b = fakeRepo(sb.dir, 'beta');
    pick(['remember', b], sb);
    pick(['remember', a], sb);           // a is head
    rmSync(a, { recursive: true, force: true });   // ...and then a moves away

    assert.deepStrictEqual(pick(['list'], sb).out.split('\n'), [b],
      'a repo that no longer validates must not appear in the menu');
    // The head is gone, so resolve must ASK rather than silently fall through to
    // beta — opening a different corpus unannounced is the bug being avoided.
    const r = pick(['resolve', '--no-ui'], sb);
    assert.notStrictEqual(r.code, 0);
    assert.match(r.err, /would prompt/i);
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('VIEWER_REPO overrides the recents without reordering them', () => {
  const sb = mkSandbox();
  try {
    const a = fakeRepo(sb.dir, 'alpha');
    const b = fakeRepo(sb.dir, 'beta');
    pick(['remember', a], sb);
    const r = pick(['resolve', '--no-ui'], sb, { VIEWER_REPO: b });
    assert.strictEqual(r.out, b);
    assert.deepStrictEqual(pick(['list'], sb).out.split('\n'), [a],
      'a one-off override must not reorder the menu');

    const bad = pick(['resolve', '--no-ui'], sb, { VIEWER_REPO: sb.corpus });
    assert.notStrictEqual(bad.code, 0, 'an invalid VIEWER_REPO must fail, not fall back');
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('forget clears one repo or all of them', () => {
  const sb = mkSandbox();
  try {
    const a = fakeRepo(sb.dir, 'alpha');
    const b = fakeRepo(sb.dir, 'beta');
    pick(['remember', a], sb);
    pick(['remember', b], sb);
    pick(['forget', b], sb);
    assert.deepStrictEqual(pick(['list'], sb).out.split('\n'), [a]);
    pick(['forget'], sb);
    assert.strictEqual(pick(['list'], sb).out, '');
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

// --- the generated .app bundle ----------------------------------------------
//
// DARWIN ONLY. make-mac-app.sh builds a macOS .app and is written against BSD sed --
// `/usr/bin/sed -i '' "s|...|"`. GNU sed reads that `''` as the SCRIPT and then treats the real
// expression as a FILENAME, so on Linux the build exits 2 with
// `sed: can't read s| @@PORTARGS@@||: No such file or directory`.
//
// That is correct for a macOS builder and wrong only for these two tests, which asserted
// `status === 0` unconditionally. Skipping with a named reason rather than making a
// macOS-targeted script portable for a workflow nobody has (you build a .app on a Mac).
//
// Found 2026-08-23: the viewer's 330 node unit tests are run by no gate, so this arrived from
// PR #176 red on every non-Mac and nothing said so. See
// bugs/2026-08-23-the-viewers-330-node-tests-are-run-by-nothing.
const DARWIN = process.platform === 'darwin';
const macOnly = { skip: DARWIN ? false : 'SKIPPED, NOT PASSED - make-mac-app.sh needs BSD sed (macOS); run on Darwin' };

function buildApp(outDir) {
  return require('node:child_process').spawnSync(
    '/bin/bash', [BUILDER, '--out', outDir, '--name', 'Test Viewer'], { encoding: 'utf8' });
}

test('the built app bakes in no repo path and ships the bootstrap', macOnly, () => {
  const sb = mkSandbox();
  try {
    const b = buildApp(sb.dir);
    assert.strictEqual(b.status, 0, `build failed: ${b.stdout}${b.stderr}`);
    const app = path.join(sb.dir, 'Test Viewer.app');
    const shim = require('node:fs').readFileSync(
      path.join(app, 'Contents', 'MacOS', 'TestViewer'), 'utf8');

    assert.ok(require('node:fs').existsSync(path.join(app, 'Contents', 'Resources', 'pick-repo.sh')),
      'the bootstrap must ship inside the bundle — it runs before a repo is known');
    assert.doesNotMatch(shim, /GitRepos/, 'no repo path may be baked into the shim');
    assert.match(shim, /--pick/, 'shim must expose a way to force the chooser');
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('the built app launches the repo it resolves', macOnly, () => {
  const sb = mkSandbox();
  try {
    assert.strictEqual(buildApp(sb.dir).status, 0);
    const shim = path.join(sb.dir, 'Test Viewer.app', 'Contents', 'MacOS', 'TestViewer');

    // VIEWER_REPO points the resolved repo at a stub whose launcher just echoes,
    // so this exercises the real hand-off without starting a server.
    const stub = fakeRepo(sb.dir, 'stubrepo');
    const r = require('node:child_process').spawnSync('/bin/bash', [shim], {
      encoding: 'utf8',
      env: { ...process.env, VIEWER_GUI: '0', VIEWER_STATE_DIR: sb.state, VIEWER_REPO: stub },
    });
    assert.strictEqual(r.status, 0, `${r.stdout}${r.stderr}`);
    assert.match(r.stdout, /stub/, "must exec the resolved repo's own launcher");
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('the real repo resolves and is a valid choice', () => {
  const sb = mkSandbox();
  try {
    const real = require('node:fs').realpathSync(REAL_REPO);
    assert.strictEqual(pick(['validate', real], sb).code, 0,
      'this repo must satisfy the validator the app uses');
  } finally {
    rmSync(sb.dir, { recursive: true, force: true });
  }
});

test('starting from a different repo takes the port over instead of showing the wrong corpus', async () => {
  const sb = mkSandbox();
  const port = await freePort();
  try {
    assert.strictEqual(run(['start', '-p', String(port), '--', sb.corpus], sb).code, 0);

    // Pretend the live server belongs to some other clone. Without the handover
    // the launcher would say "already running" and the reader would be looking
    // at a corpus from a repo they did not choose.
    require('node:fs').writeFileSync(path.join(sb.state, 'viewer.repo'), '/some/other/clone\n');

    const again = run(['start', '-p', String(port), '--', sb.corpus], sb);
    assert.strictEqual(again.code, 0, `${again.out}${again.err}`);
    assert.match(again.out, /different repo/i, 'the handover must be announced, not silent');
    assert.match(again.out, /\/some\/other\/clone/, 'must name the repo it is taking over from');

    assert.strictEqual((await get(port)).status, 200, 'the viewer must be serving again after the handover');
    assert.strictEqual(run(['status'], sb).code, 0);
  } finally {
    run(['stop'], sb);
    rmSync(sb.dir, { recursive: true, force: true });
  }
});
