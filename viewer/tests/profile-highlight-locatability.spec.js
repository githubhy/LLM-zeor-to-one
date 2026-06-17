// @ts-check
// ─────────────────────────────────────────────────────────────────────────────
// ONE-OFF PROFILER — not a CI gate.
//
// Measures how many rendered <mark> elements in the real NTN-survey and
// theories corpus can be re-located in source via the existing clearMarkEl
// regex pipeline, and how many succeed via the simpler findInlineEntryForMark
// textContent comparison.
//
// Run with:
//   cd viewer && npx playwright test tests/profile-highlight-locatability.spec.js --reporter=line
//
// Results are written to:
//   ../reports/highlight-locatability-2026-05-09.md
// ─────────────────────────────────────────────────────────────────────────────

/* global document, window, fetch, Node, NodeFilter */

'use strict';

const { test } = require('@playwright/test');
const { startServer, stopServer } = require('./helpers/server');
const path = require('path');
const fs   = require('fs');

// ── Config ───────────────────────────────────────────────────────────────────

const REPO_ROOT = path.resolve(__dirname, '../../');
const PORT = 5700;

const SURVEY_FILES = [
  'surveys/ntn-initial-sync-tracking/appendix-a-b.md',
  'surveys/ntn-initial-sync-tracking/appendix-c-part-1-derivation.md',
  'surveys/ntn-initial-sync-tracking/appendix-c-part-2-loop-closure.md',
  'surveys/ntn-initial-sync-tracking/appendix-c-part-3-practical.md',
  'surveys/ntn-initial-sync-tracking/appendix-c-part-4-adaptive.md',
  'surveys/ntn-initial-sync-tracking/channel-and-framework.md',
  'surveys/ntn-initial-sync-tracking/frequency-and-timing-estimation.md',
  'surveys/ntn-initial-sync-tracking/index.md',
  'surveys/ntn-initial-sync-tracking/initial-sync.md',
  'surveys/ntn-initial-sync-tracking/pre-compensation-and-analysis.md',
  'surveys/ntn-initial-sync-tracking/references.md',
  'surveys/ntn-initial-sync-tracking/tracking-loops.md',
];

const THEORY_FILES = [
  'theories/cross-product-fll-discriminator-derivation.md',
  'theories/inverse-z-transform of the FLL.md',
  'theories/jury-test.md',
  'theories/ma-filter-bandwidths.md',
  'theories/per-tracker-noise-bandwidth.md',
  'theories/pll-pullin-damped-pendulum.md',
  'theories/poles-and-zeros-in-z-domain.md',
  'theories/residue-theorem.md',
  'theories/root-locus-for-digital-loop.md',
  'theories/velocity-rotational-form.md',
];

const ALL_FILES = [...SURVEY_FILES, ...THEORY_FILES];

// ── In-page profiler function ─────────────────────────────────────────────────
// This runs inside the browser via page.evaluate().
// It replicates the regex logic of clearMarkEl (read-only) and the new
// DOM-position-ratio lookup of findInlineEntryAtMark (post-fix).

async function profilePage(file) {
  // ── 1. Fetch raw markdown source ─────────────────────────────────────────
  let source = '';
  try {
    const res = await fetch('/api/md/' + encodeURIComponent(file));
    if (!res.ok) return { error: 'fetch-failed:' + res.status, file };
    source = await res.text();
  } catch (e) {
    return { error: 'fetch-exception:' + String(e), file };
  }

  // ── 2. Ground-truth highlight count from shared extractor ─────────────────
  const gtCount = window.ViewerHighlightShared
    ? window.ViewerHighlightShared.extractInlineHighlights(source, file).length
    : -1; // not loaded

  // ── 3. Collect rendered marks ─────────────────────────────────────────────
  const marks = Array.from(document.querySelectorAll('mark[class*="hl-"]'));
  const renderedCount = marks.length;

  // ── 4. Helpers (mirrors of viewer.js non-async helpers) ───────────────────

  const HL_COLOR_ALT = 'yellow|green|red|blue|orange|purple|teal|pink';

  const contentEl = document.getElementById('content');

  function blockOf(node) {
    let el = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
    while (el && el !== contentEl) {
      if (el.dataset && el.dataset.sourceLine != null) return el;
      el = el.parentElement;
    }
    return null;
  }

  function nextBlockSibling(el) {
    let cur = el;
    while (cur) {
      cur = cur.nextElementSibling;
      if (!cur) {
        let parent = el.parentElement;
        while (parent && parent !== contentEl) {
          if (parent.nextElementSibling) { cur = parent.nextElementSibling; break; }
          parent = parent.parentElement;
        }
        if (!cur) return null;
      }
      if (cur.dataset && cur.dataset.sourceLine != null) return cur;
      const inner = cur.querySelector('[data-source-line]');
      if (inner) return inner;
    }
    return null;
  }

  function textBeforeNode(targetNode, root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    let text = '';
    while (walker.nextNode()) {
      if (targetNode.contains && targetNode.contains(walker.currentNode)) break;
      text += walker.currentNode.textContent;
    }
    return text;
  }

  function lineStartOffset(src, lineNum) {
    const lines = src.split('\n');
    let offset = 0;
    for (let i = 0; i < lineNum && i < lines.length; i++) {
      offset += lines[i].length + 1;
    }
    return offset;
  }

  // ── 5. Classify each rendered mark ────────────────────────────────────────

  const results = {
    file,
    groundTruth: gtCount,
    renderedCount,
    pattern1: 0,
    pattern2: 0,
    mathAware: 0,
    failed: 0,
    naiveMatch: 0,     // findInlineEntryAtMark-style: source-position lookup (post-fix)
    failures: [],
  };

  // Build manifest lookup from the manifest API (mirrors manifestByFile but via fetch).
  // We fetch the manifest endpoint that the server exposes.
  let manifestEntries = [];
  try {
    const mres = await fetch('/api/highlights-manifest?file=' + encodeURIComponent(file));
    if (mres.ok) {
      const mdata = await mres.json();
      manifestEntries = (mdata.entries || []).filter(e => e.backend === 'inline');
    }
  } catch (_) {
    // Manifest not critical; naiveMatch will just report 0.
  }

  // Mirrors findInlineEntryAtMark: source-position-ratio lookup via manifest.
  // Uses the manifest's sourceStart/sourceEnd (available in the API response)
  // to locate the entry by DOM-position-ratio, not by textContent comparison.
  function findInlineEntryAtMark(markEl) {
    const blockEl = markEl.closest('[data-source-line]');
    if (!blockEl) return null;
    const blockSrcLine = parseInt(blockEl.dataset.sourceLine, 10);
    if (!Number.isFinite(blockSrcLine)) return null;
    const nextEl   = nextBlockSibling(blockEl);
    const nextLine = nextEl ? parseInt(nextEl.dataset.sourceLine, 10) : srcLines.length;
    const bso = lineStartOffset(source, blockSrcLine);
    const beo = nextEl ? lineStartOffset(source, nextLine) : source.length;

    const entries = manifestEntries.filter(e =>
      typeof e.sourceStart === 'number' && e.sourceStart >= bso && e.sourceStart < beo
    );
    if (entries.length === 0) return null;
    if (entries.length === 1) return entries[0];

    const blockText = blockEl.textContent || '';
    if (!blockText.length) return entries[0];
    const domPre   = textBeforeNode(markEl, blockEl);
    const domRatio = domPre.length / blockText.length;
    const blockSrcLen = beo - bso;
    return entries.reduce((best, e) => {
      const eRatio    = (e.sourceStart - bso) / blockSrcLen;
      const bestRatio = (best.sourceStart - bso) / blockSrcLen;
      return Math.abs(eRatio - domRatio) < Math.abs(bestRatio - domRatio) ? e : best;
    });
  }

  const srcLines = source.split('\n');

  for (const markEl of marks) {
    // ── compute markText (mirrors clearMarkEl) ──────────────────────────────
    let markText = markEl.textContent.trim();
    if (!markText) {
      results.failed++;
      results.failures.push({ reason: 'empty-text', line: null, excerpt: '' });
      continue;
    }

    const blockEl = blockOf(markEl);
    if (!blockEl) {
      results.failed++;
      results.failures.push({ reason: 'no-block-el', line: null, excerpt: markText.slice(0, 60) });
      continue;
    }

    const blockSrcLine = parseInt(blockEl.dataset.sourceLine, 10);
    const nextEl       = nextBlockSibling(blockEl);
    const nextSrcLine  = nextEl ? parseInt(nextEl.dataset.sourceLine, 10) : srcLines.length;
    const blockSrc     = srcLines.slice(blockSrcLine, nextSrcLine).join('\n');

    const domPreText = textBeforeNode(markEl, blockEl);
    const domRatio   = blockEl.textContent.length
      ? domPreText.length / blockEl.textContent.length
      : 0;

    // Math-aware reconstruction (mirrors clearMarkEl)
    let didMathReconstruct = false;
    if (markEl.querySelector('.katex')) {
      const allMath = [...blockSrc.matchAll(/\$[^$\n]+?\$/g)];
      let srcText = '';
      let ok = true;
      for (const child of markEl.childNodes) {
        if (child.nodeType === Node.TEXT_NODE) {
          srcText += child.textContent;
        } else {
          const topKatex = (child.classList && child.classList.contains('katex'))
            ? child
            : (child.querySelector ? child.querySelector('.katex:not(.katex .katex)') : null);
          if (topKatex && allMath.length > 0) {
            const pre = textBeforeNode(topKatex, blockEl);
            const r   = blockEl.textContent.length
              ? pre.length / blockEl.textContent.length
              : 0;
            const fm = allMath.reduce((b, c) =>
              Math.abs(c.index / blockSrc.length - r) < Math.abs(b.index / blockSrc.length - r)
                ? c : b
            );
            srcText += fm[0];
          } else if (child.textContent) {
            srcText += child.textContent;
          } else {
            ok = false;
          }
        }
      }
      if (ok) {
        markText = srcText.trim();
        didMathReconstruct = true;
      }
    }

    // Build regex patterns
    const escaped = markText
      .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      .replace(/\s+/g, '\\s+');

    const pat1 = new RegExp(`==(${HL_COLOR_ALT}):\\s*${escaped}==`, 'g');
    const pat2 = new RegExp(`==${escaped}==`, 'g');

    const hits1 = [...blockSrc.matchAll(pat1)];
    if (hits1.length > 0) {
      results.pattern1++;
    } else {
      const hits2 = [...blockSrc.matchAll(pat2)];
      if (hits2.length > 0) {
        results.pattern2++;
      } else if (didMathReconstruct) {
        // We already reconstructed math — if even math-aware fails it's a real failure.
        // However, per the spec comment: classify as mathAware when the mark
        // *has* katex AND the reconstruction was attempted (regardless of final
        // regex outcome), because the pipeline would have tried the math path.
        // But more accurately: it's mathAware ONLY if a pattern hit.
        results.failed++;
        const excerpt = (markEl.textContent || '').slice(0, 80).replace(/\n/g, ' ');
        if (results.failures.length < 20) {
          results.failures.push({
            reason: 'math-reconstruct-no-match',
            line: blockSrcLine,
            excerpt,
            reconstructed: markText.slice(0, 80),
          });
        }
      } else {
        results.failed++;
        const excerpt = (markEl.textContent || '').slice(0, 80).replace(/\n/g, ' ');
        if (results.failures.length < 20) {
          results.failures.push({
            reason: 'no-pattern-match',
            line: blockSrcLine,
            excerpt,
          });
        }
      }
    }

    // New lookup (findInlineEntryAtMark style — post-fix, source-position-ratio)
    if (findInlineEntryAtMark(markEl) !== null) {
      results.naiveMatch++;
    }
  }

  // Re-classify: if pattern1 failed but math reconstruction succeeded (hits on
  // reconstructed markText), those were already counted in pattern1/pattern2
  // above (math reconstruct runs before pattern building). So mathAware count
  // = marks that have .katex AND matched via either pattern.
  // We need a separate pass for accurate mathAware tallying.
  // Reset and redo with a more explicit counter approach.
  // (The loop above is accurate for failed/p1/p2; mathAware is 0 by design
  //  since it's subsumed into p1/p2. The report will note this.)

  return results;
}

// ── Report generator ──────────────────────────────────────────────────────────

function buildReport(allResults, durationMs) {
  const lines = [];
  const ts = new Date().toISOString().slice(0, 10);

  lines.push('# Highlight Locatability Profile — 2026-05-09');
  lines.push('');
  lines.push('Profiles the existing `clearMarkEl` source-locator (used by the toolbar\'s');
  lines.push('clear/recolor actions) and the `findInlineEntryForMark` naive textContent');
  lines.push('matcher (used by the note button) across the NTN survey + theories corpus.');
  lines.push('');
  lines.push('## Methodology');
  lines.push('');
  lines.push('For each file, the profiler:');
  lines.push('');
  lines.push('1. Boots the real repo\'s viewer server (pointed at the repo root).');
  lines.push('2. Loads each file in a headless Chromium page and waits for `networkidle`.');
  lines.push('3. Fetches the raw markdown source via `/api/md/<file>`.');
  lines.push('4. Calls `ViewerHighlightShared.extractInlineHighlights(source, file)` to get the ground-truth highlight count from the source parser.');
  lines.push('5. Queries all `mark[class*="hl-"]` elements in the rendered DOM (rendered count).');
  lines.push('6. For each rendered mark, replicates the **read-only** `clearMarkEl` pipeline:');
  lines.push('   - Finds the containing `[data-source-line]` block element.');
  lines.push('   - If the mark contains `.katex`, reconstructs the source-level math text (mirrors `clearMarkEl`\'s math-aware walk).');
  lines.push('   - Builds `pattern1` (`==(color):\\s*<escaped>==`) and `pattern2` (`==<escaped>==`) regexes.');
  lines.push('   - Classifies each mark: `pattern1_match`, `pattern2_match`, or `failed`.');
  lines.push('   - **Math-aware** marks are those that had `.katex` AND matched via either pattern (reconstructed text fed into the same patterns).');
  lines.push('7. In parallel, fetches `/api/highlights-manifest?file=<file>` and replicates `findInlineEntryAtMark`\'s DOM-position-ratio source-position lookup (post-fix — not the old naive `excerpt === textContent.trim()` comparison).');
  lines.push('');
  lines.push('**Important:** "pattern1" and "pattern2" counts are not mutually exclusive');
  lines.push('with "math-aware". Marks containing KaTeX run the math reconstruction **before**');
  lines.push('the regex — so a math-heavy highlight that succeeds via pattern1 after');
  lines.push('reconstruction is counted as pattern1 (not as a separate math-aware bucket).');
  lines.push('The `failed` column is the key diagnostic: these are marks where no regex');
  lines.push('matched in the containing block, meaning the toolbar would show');
  lines.push('"Could not locate style in source".');
  lines.push('');

  // Per-file table
  lines.push('## Per-file results');
  lines.push('');
  lines.push('| File | Source HL | Rendered marks | Pattern1 | Pattern2 | Failed | Naive match |');
  lines.push('|---|---:|---:|---:|---:|---:|---:|');

  let totGT = 0, totRendered = 0, totP1 = 0, totP2 = 0, totFailed = 0, totNaive = 0;
  const allFailures = [];

  for (const r of allResults) {
    if (r.error) {
      lines.push(`| \`${r.file}\` | — | — | — | — | — | _(${r.error})_ |`);
      continue;
    }
    const shortFile = r.file.replace('surveys/ntn-initial-sync-tracking/', 'survey/').replace('theories/', 'theories/');
    lines.push(`| \`${shortFile}\` | ${r.groundTruth} | ${r.renderedCount} | ${r.pattern1} | ${r.pattern2} | ${r.failed} | ${r.naiveMatch} |`);
    totGT       += r.groundTruth >= 0 ? r.groundTruth : 0;
    totRendered += r.renderedCount;
    totP1       += r.pattern1;
    totP2       += r.pattern2;
    totFailed   += r.failed;
    totNaive    += r.naiveMatch;
    if (r.failures && r.failures.length) {
      allFailures.push({ file: r.file, failures: r.failures });
    }
  }

  lines.push(`| **TOTAL** | **${totGT}** | **${totRendered}** | **${totP1}** | **${totP2}** | **${totFailed}** | **${totNaive}** |`);
  lines.push('');

  // Totals + rates
  lines.push('## Totals and rates');
  lines.push('');
  const successCount = totP1 + totP2;
  const clearMarkRate = totRendered > 0
    ? ((successCount / totRendered) * 100).toFixed(1)
    : 'n/a';
  const naiveRate = totRendered > 0
    ? ((totNaive / totRendered) * 100).toFixed(1)
    : 'n/a';
  const failedRate = totRendered > 0
    ? ((totFailed / totRendered) * 100).toFixed(1)
    : 'n/a';

  lines.push(`| Metric | Count | Rate |`);
  lines.push(`|---|---:|---:|`);
  lines.push(`| Total files profiled | ${allResults.filter(r => !r.error).length} | |`);
  lines.push(`| Source highlights (ground truth) | ${totGT} | |`);
  lines.push(`| Rendered \`<mark>\` elements | ${totRendered} | |`);
  lines.push(`| **clearMarkEl success** (pattern1 + pattern2) | **${successCount}** | **${clearMarkRate}%** |`);
  lines.push(`|   — pattern1 (colored form) | ${totP1} | ${totRendered > 0 ? ((totP1/totRendered)*100).toFixed(1) : 'n/a'}% |`);
  lines.push(`|   — pattern2 (colorless form) | ${totP2} | ${totRendered > 0 ? ((totP2/totRendered)*100).toFixed(1) : 'n/a'}% |`);
  lines.push(`| **clearMarkEl failures** | **${totFailed}** | **${failedRate}%** |`);
  lines.push(`| **findInlineEntryAtMark success** (source-position lookup) | **${totNaive}** | **${naiveRate}%** |`);
  lines.push(`| findInlineEntryAtMark failures | ${totRendered - totNaive} | ${totRendered > 0 ? (((totRendered - totNaive)/totRendered)*100).toFixed(1) : 'n/a'}% |`);
  lines.push('');

  const gap = successCount - totNaive;
  if (gap !== 0) {
    lines.push(`> **Gap between pipelines:** clearMarkEl regex fallback succeeds on ${successCount} marks;`);
    lines.push(`> findInlineEntryAtMark succeeds on ${totNaive}. The difference of ${Math.abs(gap)}`);
    lines.push(`> marks ${gap > 0 ? 'succeed via clearMarkEl regex but are not found by the manifest lookup (manifest stale?)' : 'are found by findInlineEntryAtMark but fail the regex pipeline — these are precisely the marks the fix addresses'}.`);
    lines.push('');
  }

  lines.push(`Profiling duration: ${(durationMs / 1000).toFixed(1)} s`);
  lines.push('');

  // Failure samples
  if (allFailures.length > 0) {
    lines.push('## Failure samples');
    lines.push('');
    lines.push('First failures from each file where the `clearMarkEl` regex pipeline found no match.');
    lines.push('');
    let shown = 0;
    for (const { file, failures } of allFailures) {
      if (shown >= 30) break;
      lines.push(`### \`${file}\``);
      lines.push('');
      for (const f of failures) {
        if (shown >= 30) break;
        lines.push(`- **reason:** \`${f.reason}\` | **source line:** ${f.line ?? 'n/a'}`);
        lines.push(`  - excerpt: \`${(f.excerpt || '').replace(/`/g, "'").slice(0, 120)}\``);
        if (f.reconstructed) {
          lines.push(`  - reconstructed: \`${f.reconstructed.replace(/`/g, "'").slice(0, 120)}\``);
        }
        lines.push('');
        shown++;
      }
    }
  }

  // Observations
  lines.push('## Observations');
  lines.push('');
  if (totFailed === 0) {
    lines.push('All rendered marks are locatable via the `clearMarkEl` regex pipeline.');
    lines.push('No failures detected in this corpus.');
  } else {
    lines.push(`${totFailed} of ${totRendered} rendered marks (${failedRate}%) could NOT be located via the`);
    lines.push('`clearMarkEl` regex pipeline. These would produce the "Could not locate style');
    lines.push('in source" toast in the toolbar clear/recolor flow.');
    lines.push('');
    lines.push('Common failure reasons seen in the failure samples above:');
    const reasons = {};
    for (const { failures } of allFailures) {
      for (const f of failures) {
        reasons[f.reason] = (reasons[f.reason] || 0) + 1;
      }
    }
    for (const [r, n] of Object.entries(reasons)) {
      lines.push(`- \`${r}\`: ${n} occurrences`);
    }
  }

  const naiveGap = successCount - totNaive;
  if (naiveGap > 0) {
    lines.push('');
    lines.push(`**Manifest-lookup gap:** ${naiveGap} marks succeed via the clearMarkEl regex pipeline but fail`);
    lines.push('the source-position lookup. This could indicate the manifest API returned stale data for those marks.');
  } else if (naiveGap < 0) {
    lines.push('');
    lines.push(`**Post-fix:** findInlineEntryAtMark locates ${-naiveGap} more marks than the regex fallback pipeline.`);
    lines.push('These are the marks that the fix rescues: KaTeX / formatted marks where the regex path');
    lines.push('fails but the manifest source-position lookup succeeds. In production, `clearMarkEl`');
    lines.push('hits the fast path for all of these and skips the regex pipeline entirely.');
  } else {
    lines.push('');
    lines.push('**findInlineEntryAtMark and the regex pipeline agree on all marks.**');
  }

  lines.push('');
  lines.push('---');
  lines.push(`*Generated by \`viewer/tests/profile-highlight-locatability.spec.js\` on ${ts}.*`);
  lines.push('');

  return lines.join('\n');
}

// ── Test entry point ──────────────────────────────────────────────────────────

test('profile highlight locatability across NTN survey + theories corpus', async ({ page }) => {
  // Use a longer timeout since we're loading many large files.
  test.setTimeout(20 * 60 * 1000); // 20 minutes

  let server = null;
  try {
    server = await startServer(REPO_ROOT, PORT);
    console.log(`\nServer started on port ${PORT}, root: ${REPO_ROOT}`);
  } catch (err) {
    console.error('Failed to start server:', err.message);
    throw err;
  }

  const allResults = [];
  const t0 = Date.now();

  try {
    for (const file of ALL_FILES) {
      console.log(`\nProfiling: ${file}`);
      const url = `http://localhost:${PORT}?file=${encodeURIComponent(file)}`;

      try {
        await page.goto(url, { timeout: 60_000 });
        // Wait for rendering — networkidle may time out on large files,
        // so fall back to a fixed wait if needed.
        try {
          await page.waitForLoadState('networkidle', { timeout: 30_000 });
        } catch (_) {
          // On large math-heavy files networkidle can be slow; give it a bit more.
          await page.waitForTimeout(5_000);
        }
      } catch (err) {
        console.error(`  LOAD FAILED: ${err.message}`);
        allResults.push({ file, error: 'load-failed:' + err.message.slice(0, 80) });
        continue;
      }

      let result;
      try {
        result = await page.evaluate(profilePage, file);
      } catch (err) {
        console.error(`  EVALUATE FAILED: ${err.message}`);
        allResults.push({ file, error: 'evaluate-failed:' + err.message.slice(0, 80) });
        continue;
      }

      console.log(`  groundTruth=${result.groundTruth} rendered=${result.renderedCount} p1=${result.pattern1} p2=${result.pattern2} failed=${result.failed} naive=${result.naiveMatch}`);
      allResults.push(result);
    }
  } finally {
    stopServer(server, null); // Don't delete repo root — pass null for dir
  }

  const durationMs = Date.now() - t0;
  const report = buildReport(allResults, durationMs);

  // Write report
  const reportsDir = path.resolve(REPO_ROOT, 'reports');
  fs.mkdirSync(reportsDir, { recursive: true });
  const reportPath = path.join(reportsDir, 'highlight-locatability-2026-05-09.md');
  fs.writeFileSync(reportPath, report, 'utf8');

  console.log('\n========================================');
  console.log('REPORT WRITTEN TO:');
  console.log(reportPath);
  console.log('========================================\n');
  console.log(report);
});
