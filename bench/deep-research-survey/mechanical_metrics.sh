#!/usr/bin/env bash
# mechanical_metrics.sh — Tier-1 (no-LLM) quality metrics for a produced survey.
#
# Reuses the repo's existing validators to score the deliverable's CONSISTENCY
# and CITATION TRACEABILITY — the two axes proposals P1-2 and P1-1 target, and
# the cheapest, most objective before/after signal there is.
#
# Usage:
#   bash mechanical_metrics.sh surveys/prach-receiver-survey.md         # single file
#   bash mechanical_metrics.sh surveys/5g-nr-ldpc                       # multi-file survey dir
#   bash mechanical_metrics.sh --json surveys/prach-receiver-survey.md  # machine-readable
#
# Exit 0 if all metrics pass, 1 otherwise. Designed to be run from repo root.
set -uo pipefail

JSON=false
[[ "${1:-}" == "--json" ]] && { JSON=true; shift; }
TARGET="${1:?usage: mechanical_metrics.sh [--json] <survey-file-or-dir>}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

# Resolve a directory (for validate-refs, which takes dirs) and a file list.
if [[ -d "$TARGET" ]]; then DIR="$TARGET"; FILES=$(find "$TARGET" -name '*.md'); else DIR="$(dirname "$TARGET")"; FILES="$TARGET"; fi

pass_consistency=true; pass_refs=true; pass_citations=true
consistency_detail=""; refs_detail=""; citations_detail=""

# 1. CONSISTENCY — duplicate/orphan equation IDs + tag sequence (P1-2: cross-section drift)
for f in $FILES; do
  out=$(python3 viewer/tools/renumber-equations.py "$f" --check 2>&1); rc=$?
  if [[ $rc -ne 0 ]]; then pass_consistency=false; consistency_detail+="[$f] $(echo "$out" | tail -1); "; fi
done
[[ -z "$consistency_detail" ]] && consistency_detail="no duplicate/orphan equation IDs; tags sequential"

# 2. REFERENCE INTEGRITY — cross-file xrefs/anchors/images (only meaningful for multi-file survey dirs;
#    single-file ref checks are already covered per-file by renumber-equations --check above).
if [[ -d "$TARGET" ]]; then
  refs_out=$(python3 viewer/tools/validate-refs.py "$DIR" 2>&1); refs_rc=$?
  [[ $refs_rc -ne 0 ]] && { pass_refs=false; refs_detail="$(echo "$refs_out" | grep -iE 'error|orphan|duplicate' | head -3 | tr '\n' ';')"; } || refs_detail="cross-references valid"
else
  refs_detail="single file; per-file ref checks covered by renumber --check"
fi

# 3. CITATION TRACEABILITY — every reference entry carries a source tag (P1-1: attribution drift)
cit_out=$(python3 viewer/tools/check-citation-sources.py $FILES 2>&1); cit_rc=$?
[[ $cit_rc -ne 0 ]] && { pass_citations=false; citations_detail="$(echo "$cit_out" | grep -iE 'untagged|missing|error' | head -3 | tr '\n' ';')"; } || citations_detail="all reference entries source-tagged; tagged files present on disk"

overall=true
$pass_consistency && $pass_refs && $pass_citations || overall=false

if $JSON; then
  python3 - "$TARGET" "$pass_consistency" "$pass_refs" "$pass_citations" \
    "$consistency_detail" "$refs_detail" "$citations_detail" "$overall" <<'PY'
import json, sys
t, c, r, ci, cd, rd, cid, ov = sys.argv[1:9]
b = lambda x: x == "true"
print(json.dumps({"target": t, "metrics": {
  "consistency_pass": b(c), "consistency_detail": cd.strip(),
  "ref_integrity_pass": b(r), "ref_integrity_detail": rd.strip(),
  "citation_traceability_pass": b(ci), "citation_traceability_detail": cid.strip()},
  "overall_pass": b(ov)}, indent=2))
PY
else
  echo "=== mechanical quality metrics: $TARGET"
  $pass_consistency && echo "  [PASS] consistency (eq IDs): $consistency_detail" || echo "  [FAIL] consistency (eq IDs): $consistency_detail"
  $pass_refs        && echo "  [PASS] reference integrity: $refs_detail"          || echo "  [FAIL] reference integrity: $refs_detail"
  $pass_citations   && echo "  [PASS] citation traceability: $citations_detail"   || echo "  [FAIL] citation traceability: $citations_detail"
  echo ""; $overall && echo "STATUS: PASSED" || echo "STATUS: FAILED"
fi
$overall
