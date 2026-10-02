import { readFileSync, writeFileSync } from 'node:fs';
const lock = JSON.parse(readFileSync('package-lock.json', 'utf8'));
const lines = [
  '# Locked dependency licence inventory',
  '',
  'Generated from package-lock.json. These are package-declared SPDX identifiers, not a legal conclusion or a substitute for complete licence text. Optional packages for other platforms are included. No package lacks a declared licence in this lockfile.',
  '',
  'The static preview ships this project’s HTML, CSS, SVG, small application scripts and synthetic data. Node/Python runtimes, native image libraries, browser test binaries and node_modules are not copied to dist. If distribution changes to include containers, server software, modified dependencies or third-party assets, review the actual licences and preserve the required notices/source offers before shipping. Copyleft entries below must not be treated as permissively licensed merely because they are transitive.',
  '',
  'Run `node scripts/licence-inventory.mjs` after dependency changes. Keep this inventory with the lockfile; obtain complete licence texts from the corresponding pinned packages in node_modules and their official repositories.',
  '',
  '| Package | Version | Declared licence | Installation role |',
  '|---|---|---|---|',
];
for (const [path, value] of Object.entries(lock.packages).sort(([a], [b]) =>
  a.localeCompare(b),
)) {
  if (!path) continue;
  if (!value.license) throw new Error(`Review undeclared licence: ${path}`);
  lines.push(
    `| ${path.replace(/^node_modules\//, '')} | ${value.version} | ${value.license} | ${value.dev ? 'Development/test' : 'Build/runtime dependency'}${value.optional ? '; optional' : ''} |`,
  );
}
writeFileSync('docs/dependency-licences.md', lines.join('\n') + '\n');
