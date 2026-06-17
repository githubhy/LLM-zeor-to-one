'use strict';

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

/**
 * Create a temporary fixture directory with the given markdown files.
 * @param {Record<string, string>} files  filename → content
 * @returns {string} absolute path to the fixture directory
 */
function createFixtureDir(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'viewer-test-'));
  for (const [name, content] of Object.entries(files)) {
    const filePath = path.join(dir, name);
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content, 'utf8');
  }
  return dir;
}

/**
 * Seed a sidecar annotation file for a markdown document.
 * @param {string} fixtureDir
 * @param {string} file markdown file path relative to fixture root
 * @param {object} doc
 */
function seedAnnotations(fixtureDir, file, doc) {
  const sidecarPath = path.join(fixtureDir, '.viewer-highlights', `${file}.json`);
  fs.mkdirSync(path.dirname(sidecarPath), { recursive: true });
  fs.writeFileSync(sidecarPath, JSON.stringify(doc, null, 2), 'utf8');
}

/**
 * Start the viewer server on a unique port.
 * Resolves when the server is listening.
 * @param {string} fixtureDir
 * @param {number} port
 * @returns {Promise<import('child_process').ChildProcess>}
 */
function startServer(fixtureDir, port, options = {}) {
  const servePath = path.resolve(__dirname, '../../serve.js');
  const extraArgs = Array.isArray(options.extraArgs) ? options.extraArgs : [];
  const child = spawn(process.execPath, [servePath, fixtureDir, '-p', String(port), ...extraArgs], {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, ...(options.env || {}) },
    cwd: path.resolve(__dirname, '../..'),
  });

  return new Promise((resolve, reject) => {
    let started = false;
    child.stdout.on('data', (chunk) => {
      if (!started && chunk.toString().includes('Markdown viewer ready')) {
        started = true;
        resolve(child);
      }
    });
    child.stderr.on('data', (chunk) => {
      if (!started) {
        reject(new Error(`Server stderr: ${chunk}`));
      }
    });
    child.on('error', reject);
    child.on('exit', (code) => {
      if (!started) reject(new Error(`Server exited with code ${code}`));
    });
    setTimeout(() => {
      if (!started) reject(new Error('Server start timeout'));
    }, 10_000);
  });
}

/**
 * Stop the server and clean up the fixture directory.
 */
function stopServer(child, fixtureDir) {
  if (child && !child.killed) {
    child.kill('SIGTERM');
  }
  if (fixtureDir) {
    try { fs.rmSync(fixtureDir, { recursive: true, force: true }); } catch {}
  }
}

module.exports = { createFixtureDir, seedAnnotations, startServer, stopServer };
