'use strict';

/**
 * content-source.js — shared, Node-requirable module for survey-walking,
 * manifest building, and git-info computation.
 *
 * All public functions are parameterized on `targetDir` (absolute path).
 * There are NO module-level caches — each call recomputes fresh, which is
 * the correct behaviour for a library used by both the server and the
 * publisher.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const {
  extractInlineHighlights,
  normalizeWhitespace,
} = require('./highlight-shared');

// ---------------------------------------------------------------------------
// Pure helpers (parameterized on targetDir)
// ---------------------------------------------------------------------------

function etagOf(content) {
  return `"${crypto.createHash('sha1').update(content).digest('hex')}"`;
}

function readUtf8WithRevision(filePath) {
  const text = fs.readFileSync(filePath, 'utf8');
  return { text, revision: etagOf(text) };
}

function ensureWithin(root, filePath) {
  return filePath.startsWith(root + path.sep) || filePath === root;
}

function targetPathFor(targetDir, rel) {
  const resolved = path.resolve(targetDir, rel);
  if (!ensureWithin(targetDir, resolved)) return null;
  return resolved;
}

function annotationPathFor(targetDir, file) {
  const annotationsRoot = path.join(targetDir, '.viewer-highlights');
  const relativeJson = `${file}.json`;
  const resolved = path.resolve(annotationsRoot, relativeJson);
  if (!ensureWithin(annotationsRoot, resolved)) return null;
  return resolved;
}

function normalizeAnnotationDoc(file, docRevision, value) {
  const source = value && typeof value === 'object' ? value : {};
  const highlights = Array.isArray(source.highlights) ? source.highlights : [];
  return {
    version: 1,
    file,
    documentRevision: source.documentRevision || docRevision || null,
    highlights: highlights.map((entry) => ({
      id: entry.id,
      file,
      color: entry.color || 'yellow',
      backend: 'sidecar',
      revision: entry.revision || docRevision || null,
      excerpt: normalizeWhitespace(entry.excerpt || ''),
      segments: Array.isArray(entry.segments) ? entry.segments : [],
      updatedAt: Number(entry.updatedAt) || 0,
      ...(entry.deleted ? { deleted: true } : {}),
    })),
  };
}

function defaultAnnotationDoc(file, docRevision) {
  return normalizeAnnotationDoc(file, docRevision, { highlights: [] });
}

function readAnnotationDoc(targetDir, file, docRevision) {
  const filePath = annotationPathFor(targetDir, file);
  if (!filePath) throw new Error('Invalid annotation path');
  if (!fs.existsSync(filePath)) {
    const doc = defaultAnnotationDoc(file, docRevision);
    return {
      doc,
      revision: etagOf(JSON.stringify(doc)),
      exists: false,
      filePath,
    };
  }
  const raw = fs.readFileSync(filePath, 'utf8');
  const parsed = JSON.parse(raw);
  const doc = normalizeAnnotationDoc(file, docRevision, parsed);
  return {
    doc,
    revision: etagOf(raw),
    exists: true,
    filePath,
  };
}

function minLineForAnnotation(entry) {
  let best = Number.POSITIVE_INFINITY;
  for (const segment of entry.segments || []) {
    if (typeof segment.blockLine === 'number') best = Math.min(best, segment.blockLine);
    if (typeof segment.tableLine === 'number') best = Math.min(best, segment.tableLine);
  }
  return Number.isFinite(best) ? best : 0;
}

function sidecarFileFromAnnotationPath(targetDir, absPath) {
  const annotationsRoot = path.join(targetDir, '.viewer-highlights');
  const relative = path.relative(annotationsRoot, absPath).replace(/\\/g, '/');
  if (!relative.endsWith('.json')) return null;
  return relative.slice(0, -'.json'.length);
}

function loadInlineManifest(targetDir, file) {
  // No cache — always recompute.
  const filePath = targetPathFor(targetDir, file);
  if (!filePath || !fs.existsSync(filePath)) return { revision: null, entries: [] };
  const { text, revision } = readUtf8WithRevision(filePath);
  const entries = extractInlineHighlights(text, file).map((entry) => ({
    id: entry.id,
    file,
    backend: 'inline',
    color: entry.color,
    excerpt: entry.excerpt,
    lineStart: entry.lineStart,
    lineEnd: entry.lineEnd,
    sourceStart: entry.sourceStart,
    sourceEnd: entry.sourceEnd,
    innerStart: entry.innerStart,
    innerEnd: entry.innerEnd,
    noteId: entry.noteId,
    noteRefStart: entry.noteRefStart,
    noteRefEnd: entry.noteRefEnd,
    noteDefStart: entry.noteDefStart,
    noteDefEnd: entry.noteDefEnd,
    noteBody: entry.noteBody,
    noteHasMath: entry.noteHasMath,
    revision,
  }));
  return { revision, entries };
}

function loadSidecarManifest(targetDir, file, docRevision) {
  // No cache — always recompute.
  const { doc, revision } = readAnnotationDoc(targetDir, file, docRevision);
  const entries = (doc.highlights || []).filter((entry) => !entry.deleted).map((entry) => ({
    id: entry.id,
    file,
    backend: 'sidecar',
    color: entry.color || 'yellow',
    excerpt: normalizeWhitespace(entry.excerpt || ''),
    lineStart: minLineForAnnotation(entry),
    lineEnd: minLineForAnnotation(entry),
    revision: entry.revision || doc.documentRevision || null,
  }));
  return {
    revision,
    documentRevision: doc.documentRevision || null,
    entries,
  };
}

function gitCmd(targetDir, args) {
  return execFileSync('git', args, {
    cwd: targetDir,
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: false,
    windowsHide: true,
    encoding: 'utf8',
  }).trim();
}

function parseRemoteUrl(url) {
  // Strip embedded credentials; never echo them back.
  const patterns = [
    /^https?:\/\/(?:[^@\/]+@)?github\.com\/([^\/]+)\/([^\/?#]+?)(?:\.git)?\/?$/i,
    /^git@github\.com:([^\/]+)\/([^\/?#]+?)(?:\.git)?$/i,
    /^ssh:\/\/git@github\.com\/([^\/]+)\/([^\/?#]+?)(?:\.git)?$/i,
  ];
  for (const re of patterns) {
    const m = url.match(re);
    if (m) return { owner: m[1], repo: m[2] };
  }
  return null;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * List markdown files under targetDir, respecting order.json files.
 * @param {string} targetDir  Absolute path to the survey/content root.
 * @returns {string[]}  Relative paths, forward-slash separated.
 */
function listMarkdownFiles(targetDir) {
  const orderFile = path.join(targetDir, 'order.json');
  if (fs.existsSync(orderFile)) {
    try {
      const ordered = JSON.parse(fs.readFileSync(orderFile, 'utf8'));
      return ordered.filter((f) => fs.existsSync(path.join(targetDir, f)));
    } catch {
      // fall through
    }
  }

  const results = [];
  function walk(dir, prefix) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    let folderOrder = null;
    if (prefix) {
      const orderPath = path.join(dir, 'order.json');
      if (fs.existsSync(orderPath)) {
        try {
          const arr = JSON.parse(fs.readFileSync(orderPath, 'utf8'));
          folderOrder = new Map(arr.map((name, i) => [name, i]));
        } catch (e) {
          console.warn(`order.json parse failed at ${orderPath}: ${e.message}`);
        }
      }
    }

    if (folderOrder) {
      const subdirs = [];
      const mdFiles = [];
      for (const entry of entries) {
        if (entry.name === 'node_modules' || entry.name === 'archive' || entry.name === '.viewer-highlights') continue;
        if (entry.isDirectory()) subdirs.push(entry.name);
        else if (entry.name.endsWith('.md')) mdFiles.push(entry.name);
      }
      mdFiles.sort((a, b) => {
        const ia = folderOrder.has(a) ? folderOrder.get(a) : Number.MAX_SAFE_INTEGER;
        const ib = folderOrder.has(b) ? folderOrder.get(b) : Number.MAX_SAFE_INTEGER;
        return ia !== ib ? ia - ib : a.localeCompare(b);
      });
      for (const name of mdFiles) {
        results.push(`${prefix}/${name}`);
      }
      for (const name of subdirs) {
        walk(path.join(dir, name), `${prefix}/${name}`);
      }
    } else {
      // No order.json — DFS-alphabetical (readdirSync returns alphabetical).
      for (const entry of entries) {
        if (entry.name === 'node_modules' || entry.name === 'archive' || entry.name === '.viewer-highlights') continue;
        const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
        if (entry.isDirectory()) {
          walk(path.join(dir, entry.name), rel);
        } else if (entry.name.endsWith('.md')) {
          results.push(rel);
        }
      }
    }
  }
  walk(targetDir, '');
  return results;
}

/**
 * Build the highlights manifest for one file (fileFilter = relative path)
 * or all files (fileFilter = null).
 * @param {string} targetDir
 * @param {string|null} fileFilter
 * @returns {{ entries: object[] }}
 */
function buildManifest(targetDir, fileFilter) {
  const files = fileFilter ? [fileFilter] : listMarkdownFiles(targetDir);
  const entries = [];
  for (const file of files) {
    const inline = loadInlineManifest(targetDir, file);
    const sidecar = loadSidecarManifest(targetDir, file, inline.revision);
    entries.push(...inline.entries, ...sidecar.entries);
  }
  entries.sort((a, b) => {
    if (a.file !== b.file) return a.file.localeCompare(b.file);
    if ((a.lineStart || 0) !== (b.lineStart || 0)) return (a.lineStart || 0) - (b.lineStart || 0);
    const aSrc = Number(a.sourceStart);
    const bSrc = Number(b.sourceStart);
    if (Number.isFinite(aSrc) && Number.isFinite(bSrc) && aSrc !== bSrc) return aSrc - bSrc;
    return a.id.localeCompare(b.id);
  });
  return { entries };
}

/**
 * Compute git info for the repo containing targetDir.
 * Always recomputes fresh (no cache).
 * @param {string} targetDir
 * @returns {object}
 */
function computeGitInfo(targetDir) {
  let sha, branch, remoteParsed, headPushed = null, repoRelDir = '';
  try {
    sha = gitCmd(targetDir, ['rev-parse', 'HEAD']);
  } catch (_) {
    return { available: false, reason: 'not a git repo' };
  }
  try {
    const top = gitCmd(targetDir, ['rev-parse', '--show-toplevel']);
    const rel = path.relative(path.resolve(top), targetDir);
    repoRelDir = rel.split(path.sep).join('/');
    if (repoRelDir.startsWith('..')) repoRelDir = '';
  } catch (_) {
    repoRelDir = '';
  }
  try {
    const raw = gitCmd(targetDir, ['config', '--get', 'remote.origin.url']);
    remoteParsed = parseRemoteUrl(raw);
  } catch (_) {
    remoteParsed = null;
  }
  if (!remoteParsed) {
    return { available: false, reason: 'no github remote' };
  }
  try {
    const abbrev = gitCmd(targetDir, ['rev-parse', '--abbrev-ref', 'HEAD']);
    branch = abbrev === 'HEAD' ? null : abbrev;
  } catch (_) {
    branch = null;
  }
  try {
    execFileSync('git', ['merge-base', '--is-ancestor', 'HEAD', '@{upstream}'], {
      cwd: targetDir, stdio: 'ignore', shell: false, windowsHide: true,
    });
    headPushed = true;
  } catch (err) {
    headPushed = err && err.status === 1 ? false : null;
  }
  return {
    available: true,
    owner: remoteParsed.owner,
    repo: remoteParsed.repo,
    sha,
    branch,
    headPushed,
    repoRelDir,
  };
}

module.exports = {
  listMarkdownFiles,
  buildManifest,
  computeGitInfo,
  etagOf,
  normalizeAnnotationDoc,
  loadSidecarManifest,
};
