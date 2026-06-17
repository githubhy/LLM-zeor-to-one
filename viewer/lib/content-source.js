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
// Built-in default ignore patterns (prepended to every matcher).
// These cover the dirs that were previously hard-coded in the legacy walker
// plus additional noise dirs that should never be served as content.
// ---------------------------------------------------------------------------
const BUILTIN_DEFAULTS = [
  'node_modules/',
  'archive/',
  '.viewer-highlights/',
  'dist/',
  'download/',
  'temp/',
  '.git/',
  'viewer/',
];

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
 * Build a gitignore-compatible include/exclude matcher.
 *
 * The `ignore` npm package is loaded lazily so that code paths that do NOT use
 * the matcher (legacy bare calls, publisher default path) stay free of the dep.
 *
 * @param {object} [opts]
 * @param {string} [opts.projectIgnorePath]  Absolute path to a project-level .viewerignore.
 * @param {string} [opts.perRootIgnorePath]  Absolute path to a per-root .viewerignore.
 * @returns {{ ignores(relPath: string): boolean }}
 */
function buildIgnoreMatcher(opts) {
  // eslint-disable-next-line global-require
  const ignore = require('ignore');
  const ig = ignore();

  // 1. Built-in defaults (always prepended).
  ig.add(BUILTIN_DEFAULTS);

  // 2. Project-level .viewerignore (if it exists).
  const projectPath = opts && opts.projectIgnorePath;
  if (projectPath) {
    try {
      const content = fs.readFileSync(projectPath, 'utf8');
      const lines = content.split(/\r?\n/).filter((l) => l.trim() !== '' && !l.startsWith('#'));
      if (lines.length) ig.add(lines);
    } catch {
      // File absent or unreadable — silently skip.
    }
  }

  // 3. Per-root .viewerignore (if provided and exists).
  const rootPath = opts && opts.perRootIgnorePath;
  if (rootPath) {
    try {
      const content = fs.readFileSync(rootPath, 'utf8');
      const lines = content.split(/\r?\n/).filter((l) => l.trim() !== '' && !l.startsWith('#'));
      if (lines.length) ig.add(lines);
    } catch {
      // File absent or unreadable — silently skip.
    }
  }

  return ig;
}

/**
 * List markdown files under targetDir, respecting order.json files.
 *
 * @param {string} targetDir  Absolute path to the survey/content root.
 * @param {object} [opts]
 * @param {object} [opts.ignore]              Matcher from buildIgnoreMatcher; when absent the
 *                                            three legacy literal skips (node_modules/archive/
 *                                            .viewer-highlights) are used instead — keeping a
 *                                            bare call byte-identical to the pre-opts behaviour.
 * @param {boolean} [opts.honorRootOrderJson] When true the root-level order.json short-circuit
 *                                            is taken (single-root compat path). Default false.
 * @returns {string[]}  Relative paths, forward-slash separated.
 */
function listMarkdownFiles(targetDir, opts) {
  // Compat lock: a bare call (opts === undefined) is 100 % byte-identical to the
  // pre-opts code.  When opts is explicitly provided, opt.honorRootOrderJson
  // controls the root short-circuit (default false so multi-root / generator
  // paths never take it); opts.ignore replaces the three legacy literal skips.
  const noOpts = opts === undefined;
  const ignore = opts && opts.ignore ? opts.ignore : null;
  // Root short-circuit is taken when: (a) no opts at all (bare legacy call), OR
  // (b) opts.honorRootOrderJson is explicitly true.
  const honorRootOrderJson = noOpts || (opts && opts.honorRootOrderJson === true);

  // Root short-circuit: only when explicitly requested (single-root compat).
  if (honorRootOrderJson) {
    const orderFile = path.join(targetDir, 'order.json');
    if (fs.existsSync(orderFile)) {
      try {
        const ordered = JSON.parse(fs.readFileSync(orderFile, 'utf8'));
        return ordered.filter((f) => {
          if (!fs.existsSync(path.join(targetDir, f))) return false;
          if (ignore && ignore.ignores(f)) return false;
          return true;
        });
      } catch {
        // fall through to walker
      }
    }
  }

  const results = [];
  function walk(dir, prefix) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    let folderOrder = null;
    {
      // Honor a per-folder order.json at EVERY level, INCLUDING the walk root:
      // a content root served with honorRootOrderJson:false (multi-root) must
      // still order its own top-level files. The root short-circuit, when
      // enabled, returns before the walk, so there is no double-consultation.
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
        // Skip logic: use ignore matcher when provided, else legacy literals.
        if (ignore) {
          const relEntry = prefix ? `${prefix}/${entry.name}` : entry.name;
          const testRel = entry.isDirectory() ? `${relEntry}/` : relEntry;
          if (ignore.ignores(testRel)) continue;
        } else {
          if (entry.name === 'node_modules' || entry.name === 'archive' || entry.name === '.viewer-highlights') continue;
        }
        if (entry.isDirectory()) subdirs.push(entry.name);
        else if (entry.name.endsWith('.md')) mdFiles.push(entry.name);
      }
      mdFiles.sort((a, b) => {
        const ia = folderOrder.has(a) ? folderOrder.get(a) : Number.MAX_SAFE_INTEGER;
        const ib = folderOrder.has(b) ? folderOrder.get(b) : Number.MAX_SAFE_INTEGER;
        return ia !== ib ? ia - ib : a.localeCompare(b);
      });
      // Drop order.json entries that are ignored or missing.
      for (const name of mdFiles) {
        const relFile = prefix ? `${prefix}/${name}` : name;
        if (ignore && ignore.ignores(relFile)) continue;
        if (!fs.existsSync(path.join(dir, name))) continue;
        results.push(relFile);
      }
      for (const name of subdirs) {
        walk(path.join(dir, name), prefix ? `${prefix}/${name}` : name);
      }
    } else {
      // No order.json — DFS-alphabetical (readdirSync returns alphabetical).
      for (const entry of entries) {
        const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
        // Skip logic: use ignore matcher when provided, else legacy literals.
        if (ignore) {
          const testRel = entry.isDirectory() ? `${rel}/` : rel;
          if (ignore.ignores(testRel)) continue;
        } else {
          if (entry.name === 'node_modules' || entry.name === 'archive' || entry.name === '.viewer-highlights') continue;
        }
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
 * List markdown files across multiple roots, returning namespaced ids.
 *
 * For each `{id, absPath}` in order: walks `absPath` with
 * `listMarkdownFiles(absPath, { ignore, honorRootOrderJson: false })`, then
 * maps each relative path to `id==='' ? rel : id+'/'+rel`. Results are
 * concatenated in `roots` order.
 *
 * @param {Array<{id:string, absPath:string, label:string}>} roots
 * @param {object} [opts]
 * @param {object} [opts.ignore]  Shared matcher from buildIgnoreMatcher.
 * @returns {string[]}
 */
function listMarkdownFilesMultiRoot(roots, opts) {
  const ignore = opts && opts.ignore ? opts.ignore : null;
  // A sole compat root (id='') reproduces the legacy single-root short-circuit
  // exactly (invariant 1). Genuine roots use the walk (honorRootOrderJson:false)
  // — a root's own top-level order.json is still honored, now via the per-folder
  // logic, which includes unlisted files instead of dropping them.
  const soleCompat = roots.length === 1 && roots[0].id === '';
  const result = [];
  for (const root of roots) {
    const files = listMarkdownFiles(root.absPath, { ignore, honorRootOrderJson: soleCompat });
    for (const rel of files) {
      result.push(root.id === '' ? rel : `${root.id}/${rel}`);
    }
  }
  return result;
}

/**
 * Resolve a namespaced file id to its owning root + root-relative path.
 * Longest matching id prefix wins. An `id===''` root (single-root compat)
 * matches anything but only as the sole fallback when no namespaced root
 * claims the file.
 * @param {Array<{id:string, absPath:string, label:string}>} roots
 * @param {string} file  namespaced id (`id/rel`, or `rel` when the only root id==='')
 * @returns {{root:object, rel:string}|null}
 */
function rootForFile(roots, file) {
  let best = null;
  let emptyRoot = null;
  for (const root of roots) {
    if (root.id === '') { emptyRoot = root; continue; }
    const prefix = `${root.id}/`;
    if (file === root.id || file.startsWith(prefix)) {
      const rel = file === root.id ? '' : file.slice(prefix.length);
      if (!best || root.id.length > best.root.id.length) best = { root, rel };
    }
  }
  if (best) return best;
  if (emptyRoot) return { root: emptyRoot, rel: file };
  return null;
}

/**
 * Inverse of rootForFile: find the root whose absPath contains absPath.
 * Longest-absPath ancestor wins (roots may nest). Used by the watcher to map
 * a filesystem event back to its namespaced file id.
 * @param {Array<{id:string, absPath:string, label:string}>} roots
 * @param {string} absPath
 * @returns {{root:object, rel:string}|null}
 */
function rootForAbsPath(roots, absPath) {
  let best = null;
  for (const root of roots) {
    if (ensureWithin(root.absPath, absPath)) {
      if (!best || root.absPath.length > best.root.absPath.length) {
        const rel = path.relative(root.absPath, absPath).split(path.sep).join('/');
        best = { root, rel };
      }
    }
  }
  return best;
}

/**
 * Build the highlights manifest for one file (fileFilter = relative path)
 * or all files (fileFilter = null). When listing all files, an optional
 * `opts.ignore` matcher restricts the set to the SAME files the content bake /
 * server serve — without it the manifest can list ignore-excluded files,
 * yielding 404-pointing entries.
 * @param {string} targetDir
 * @param {string|null} fileFilter
 * @param {object} [opts]
 * @returns {{ entries: object[] }}
 */
function buildManifest(targetDir, fileFilter, opts) {
  const ignore = opts && opts.ignore ? opts.ignore : undefined;
  const files = fileFilter ? [fileFilter] : listMarkdownFiles(targetDir, ignore ? { ignore } : undefined);
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
  buildIgnoreMatcher,
  listMarkdownFiles,
  listMarkdownFilesMultiRoot,
  rootForFile,
  rootForAbsPath,
  buildManifest,
  computeGitInfo,
  etagOf,
  normalizeAnnotationDoc,
  loadSidecarManifest,
};
