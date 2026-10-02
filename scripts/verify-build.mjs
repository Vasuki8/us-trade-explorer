import { readdirSync, readFileSync, existsSync, statSync } from 'node:fs';
import { join, relative, resolve } from 'node:path';
import { gzipSync } from 'node:zlib';
import {
  loadPublicRelease,
  validatePublicManifest,
  MAX_PUBLIC_MANIFEST_BYTES,
  MAX_PUBLIC_RELEASE_BYTES,
} from '../packages/contracts/public-release.ts';
const root = resolve('dist'),
  base = process.env.BASE_PATH || '/';
function files(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? files(join(dir, e.name)) : [join(dir, e.name)],
  );
}
const all = files(root),
  html = all.filter((p) => p.endsWith('.html'));
function check(ok, msg) {
  if (!ok) throw new Error(msg);
}
function readBoundedJSON(path, limit) {
  check(statSync(path).size <= limit, 'Public metadata exceeds byte limit');
  return JSON.parse(readFileSync(path, 'utf8'));
}
const pinnedManifest = validatePublicManifest(
  readBoundedJSON(
    resolve('releases/sample-2026-07-v1.manifest.json'),
    MAX_PUBLIC_MANIFEST_BYTES,
  ),
);
const generatedManifest = validatePublicManifest(
  readBoundedJSON(
    join(root, 'data', `${pinnedManifest.releaseId}.manifest.json`),
    MAX_PUBLIC_MANIFEST_BYTES,
  ),
);
check(
  JSON.stringify(generatedManifest) === JSON.stringify(pinnedManifest),
  'Generated metadata differs from the reviewed sample manifest',
);
await loadPublicRelease(generatedManifest, (contentHash) => {
  check(contentHash === pinnedManifest.contentHash, 'Unexpected public hash');
  const path = join(root, 'data', `${pinnedManifest.releaseId}.json`);
  check(
    statSync(path).size <= MAX_PUBLIC_RELEASE_BYTES,
    'Public JSON too large',
  );
  return readFileSync(path);
});
let scriptBytes = 0;
for (const path of all) {
  const bytes = readFileSync(path),
    text = bytes.toString('utf8');
  check(
    !/canary-private-secret|BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}/.test(
      text,
    ),
    `Secret-like material in ${relative(root, path)}`,
  );
  if (path.endsWith('.js')) scriptBytes += gzipSync(bytes).length;
  if (path.endsWith('.json'))
    check(
      gzipSync(bytes).length < 250 * 1024,
      'Public JSON exceeds compact dataset budget',
    );
  if (!path.endsWith('.html')) continue;
  check(
    /<title>[^<]+<\/title>/.test(text) && /<meta name="description"/.test(text),
    'Missing SEO content',
  );
  check(
    /name="robots" content="noindex, follow"/.test(text),
    'Sample page may be indexed',
  );
  check(
    text.includes('All figures are synthetic sample data.'),
    'Sample disclosure missing',
  );
  check(
    !/<script(?![^>]*\bsrc=)[^>]*>\s*[^<\s]/.test(text),
    'Inline executable script violates CSP',
  );
  for (const [, raw] of text.matchAll(/(?:href|src)="([^"]+)"/g)) {
    const link = raw.replaceAll('&amp;', '&').split(/[?#]/)[0];
    if (!link.startsWith('/') || link.startsWith('//')) continue;
    check(link.startsWith(base), `Link escapes base: ${link}`);
    const target = resolve(root, decodeURI(link.slice(base.length)));
    check(
      target === root ||
        target.startsWith(root + '\\') ||
        target.startsWith(root + '/'),
      'Path traversal',
    );
    check(
      existsSync(target) &&
        (statSync(target).isFile() || existsSync(join(target, 'index.html'))),
      `Broken link ${link} in ${relative(root, path)}`,
    );
  }
}
check(scriptBytes < 100 * 1024, 'Total compressed JS exceeds 100KiB');
check(html.length < 5000, 'Route budget exceeded');
check(
  !readFileSync(join(root, 'sitemap.xml'), 'utf8').includes('<loc>'),
  'Sample sitemap must be empty',
);
console.log(
  `Verified pinned public JSON/metadata, ${html.length} HTML pages, internal links, sample noindex, secret patterns and asset budgets (${scriptBytes} bytes gzipped JS).`,
);
