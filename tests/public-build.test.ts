import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import {
  readFileSync,
  writeFileSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  realpathSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { encodePublicRelease } from '../packages/contracts/public-release.ts';

const manifestFile = new URL(
  '../releases/sample-2026-07-v1.manifest.json',
  import.meta.url,
);
const manifest = JSON.parse(readFileSync(manifestFile, 'utf8'));
const canonicalMetadata = JSON.stringify(manifest);
const sample = JSON.parse(
  readFileSync(
    new URL('./fixtures/sample-release.json', import.meta.url),
    'utf8',
  ),
);
const verifier = fileURLToPath(
  new URL('../scripts/verify-build.mjs', import.meta.url),
);

function verify(metadata: string | Uint8Array) {
  const parent = realpathSync(tmpdir());
  const directory = mkdtempSync(join(parent, 'trade-public-build-'));
  // The only recursive cleanup target is this newly created temporary directory.
  assert.equal(dirname(directory), parent);
  try {
    mkdirSync(join(directory, 'releases'));
    mkdirSync(join(directory, 'dist', 'data'), { recursive: true });
    writeFileSync(
      join(directory, 'releases', 'sample-2026-07-v1.manifest.json'),
      readFileSync(manifestFile),
    );
    writeFileSync(
      join(directory, 'dist', 'data', `${manifest.releaseId}.json`),
      encodePublicRelease(sample),
    );
    writeFileSync(
      join(directory, 'dist', 'data', `${manifest.releaseId}.manifest.json`),
      metadata,
    );
    writeFileSync(join(directory, 'dist', 'sitemap.xml'), '<urlset/>');
    const result = spawnSync(process.execPath, [verifier], {
      cwd: directory,
      encoding: 'utf8',
      timeout: 20000,
      env: { ...process.env, BASE_PATH: '/' },
    });
    assert.equal(result.error, undefined);
    return result;
  } finally {
    rmSync(directory, { recursive: true });
  }
}

test('build verification accepts the canonical public sample sidecar', () => {
  const result = verify(canonicalMetadata);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Verified pinned public JSON\/metadata/);
});

test('duplicate sidecar fields cannot hide private payloads discarded by JSON parsing', () => {
  for (const key of ['coverage', 'classification', 'provenance']) {
    const bytes = canonicalMetadata.replace(
      `"${key}":`,
      `"${key}":{"privateNotes":"review-fixture-secret"},"${key}":`,
    );
    assert.deepEqual(JSON.parse(bytes), manifest);
    const result = verify(bytes);
    assert.notEqual(
      result.status,
      0,
      `Accepted hidden private payload in ${key}`,
    );
    assert.match(result.stderr, /canonical pinned JSON/);
  }
});

test('metadata whitespace and malformed UTF-8 cannot bypass exact artifact bytes', () => {
  const malformed = Buffer.from(canonicalMetadata);
  malformed[malformed.indexOf('Illustrative')] = 0xff;
  for (const metadata of [canonicalMetadata + '\n', malformed]) {
    const result = verify(metadata);
    assert.notEqual(result.status, 0, 'Accepted noncanonical metadata bytes');
    assert.match(result.stderr, /canonical pinned JSON|encoding|UTF-8/i);
  }
});
