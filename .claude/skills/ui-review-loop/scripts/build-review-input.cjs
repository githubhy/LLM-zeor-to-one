/* build-review-input.cjs — emit review-input.json (absolute image paths, grouped
 * by STATE GROUP) from a capture run's manifest. The vision workflow runs ONE agent
 * per (doc × state-group) so each agent compares a coherent set of states.
 *   node .../build-review-input.cjs <out-dir> > <out>/review-input.json
 * Absolute paths let the workflow's vision agents Read each PNG directly. */
const fs = require("fs");
const path = require("path");
const OUT = path.resolve(process.argv[2] || ".");
const manifest = JSON.parse(fs.readFileSync(path.join(OUT, "manifest.json"), "utf8"));
const abs = (rel) => (rel ? path.join(OUT, rel) : null);

// Group label for the synthesis prompt — what each cluster is meant to exercise.
const GROUP_BLURB = {
  core: "core chrome × theme states (docs/reader/focus, light/dark)",
  theme: "theme variants (sepia)",
  density: "chrome density presets (compact/spacious) — these tune --ui-density-lh, NOT prose line-height",
  wide: "wide-desktop layouts (three-zone right-pane, split Pane B, margin sidenotes)",
  mobile: "mobile reader (390px, isMobile)",
};

const rows = [];
for (const m of manifest) {
  const byGroup = {};
  for (const [stateId, shot] of Object.entries(m.shots)) {
    const g = shot.group || "core";
    (byGroup[g] ||= []).push({
      stateId,
      img: abs(shot.file),
      status: shot.status,
      dom: shot.dom || null,
      seedFails: shot.seedFails || [],
      error: shot.error || null,
    });
  }
  for (const [group, shots] of Object.entries(byGroup)) {
    rows.push({
      key: `${m.key}::${group}`,
      doc: m.label,
      file: m.file,
      group,
      groupBlurb: GROUP_BLURB[group] || group,
      bytes: m.bytes,
      shots,
    });
  }
}
process.stdout.write(JSON.stringify(rows, null, 2) + "\n");
process.stderr.write(`emitted ${rows.length} review groups across ${manifest.length} docs\n`);
