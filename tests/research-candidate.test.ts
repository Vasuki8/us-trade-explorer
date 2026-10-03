import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import test from 'node:test';
import {
  encodeResearchCandidate,
  validateResearchCandidate,
  validateResearchManifest,
  loadResearchCandidate,
} from '../packages/contracts/research-candidate.ts';
import {
  loadPublicRelease,
  projectPublicRelease,
  validatePublicManifest,
} from '../packages/contracts/public-release.ts';

const fixture = JSON.parse(
  readFileSync(
    new URL('./fixtures/research-candidate.example.json', import.meta.url),
    'utf8',
  ),
);
assert.equal(
  fixture.fixtureType,
  'fabricated-for-contract-tests-not-official-data',
);
const bundle = fixture.bundle;
const clone = () => structuredClone(bundle.data);
const hash = (bytes: Uint8Array) =>
  createHash('sha256').update(bytes).digest('hex');
const manifestFor = (bytes: Uint8Array) => ({
  ...bundle.manifest,
  contentBytes: bytes.length,
  contentHash: hash(bytes),
});

test('fabricated Python output validates and canonical bytes reproduce its checksum', async () => {
  const bytes = encodeResearchCandidate(bundle.data);
  assert.equal(hash(bytes), bundle.manifest.contentHash);
  assert.equal(bytes.length, bundle.manifest.contentBytes);
  assert.match(new TextDecoder().decode(bytes), /mat\\u00e9/);
  assert.deepEqual(
    await loadResearchCandidate(bundle.manifest, () => bytes),
    bundle.data,
  );
});

test('strict scope, definitions, source URLs, dates, coverage and policy reject rehashed claims', () => {
  const mutations = [
    (d: any) => (d.schemaVersion = true),
    (d: any) => (d.publicationState = 'published'),
    (d: any) => (d.scope.period = '2026-08'),
    (d: any) => (d.scope.product.code = '0901'),
    (d: any) => d.flows.reverse(),
    (d: any) => (d.flows[0].statisticalBasis.measure = 'ALL_VAL_MO'),
    (d: any) => (d.flows[1].statisticalBasis.valuation = 'customs-value'),
    (d: any) => (d.flows[0].source.datasetURL += '?key=secret'),
    (d: any) =>
      (d.flows[0].classification.referenceURLs[0] = 'https://evil.invalid/'),
    (d: any) =>
      (d.flows[0].classification.apiClassificationVintage = '2026-07-01'),
    (d: any) => (d.flows[0].times.officialReleaseDate = '2026-09-03'),
    (d: any) => (d.flows[0].times.retrievedAt = '2026-02-30T00:00:00Z'),
    (d: any) => (d.coverage.globalCoverageComplete = true),
    (d: any) => (d.geography.effectiveFromVerified = '2026-07-01'),
    (d: any) => (d.geography.referenceURLs = []),
    (d: any) => (d.analysisPolicy.historicalGrowth = 'supported'),
    (d: any) => (d.flows[0].countries[0].name = '<script>bad</script>'),
  ];
  for (const mutate of mutations) {
    const data = clone();
    mutate(data);
    assert.throws(() => validateResearchCandidate(data));
  }
});

test('unknown private fields are rejected at every nested boundary', () => {
  const paths = [
    [],
    ['scope'],
    ['scope', 'product'],
    ['coverage'],
    ['geography'],
    ['analysisPolicy'],
    ['flows', 0],
    ['flows', 0, 'source'],
    ['flows', 0, 'statisticalBasis'],
    ['flows', 0, 'times'],
    ['flows', 0, 'classification'],
    ['flows', 0, 'world'],
    ['flows', 0, 'countries', 0],
    ['flows', 0, 'totals'],
    ['flows', 0, 'coverage'],
  ];
  for (const path of paths) {
    const data = clone();
    let target = data;
    for (const key of path) target = target[key];
    target.sourceQuery = 'PRIVATE-CANARY';
    assert.throws(() => validateResearchCandidate(data));
  }
});

test('amount types, status and all arithmetic relationships are checked independently', () => {
  for (const mutate of [
    (d: any) => (d.flows[0].countries[0].value = 10),
    (d: any) => (d.flows[0].countries[0].value = '01'),
    (d: any) => (d.flows[0].countries[0].value = '-1'),
    (d: any) => (d.flows[0].countries[0].value = '1'.repeat(25)),
    (d: any) => (d.flows[0].countries[2].status = 'reported'),
    (d: any) => (d.flows[0].countries[0].shareOfWorldPercent = '11.00'),
    (d: any) =>
      (d.flows[0].countries[0].shareUnavailableReason = 'world-not-observed'),
    (d: any) => (d.flows[0].totals.observedSelectedUSD = '61'),
    (d: any) => (d.flows[0].totals.selectedTotalUSD = null),
    (d: any) => (d.flows[0].totals.selectedShareOfWorldPercent = '61.00'),
    (d: any) => (d.flows[0].coverage.allSelectedObserved = false),
    (d: any) => (d.flows[0].coverage.missingSelectedCodes = ['5330']),
    (d: any) => (d.flows[0].world.value = '59'),
  ]) {
    const data = clone();
    mutate(data);
    assert.throws(() => validateResearchCandidate(data));
  }
});

test('missing rows remain unavailable while an observed zero remains zero', () => {
  const data = clone(),
    flow = data.flows[0];
  Object.assign(flow.countries[2], {
    status: 'unobserved',
    value: null,
    shareOfWorldPercent: null,
    shareUnavailableReason: 'partner-not-observed',
  });
  Object.assign(flow.totals, {
    selectedTotalUSD: null,
    selectedShareOfWorldPercent: null,
  });
  Object.assign(flow.coverage, {
    allSelectedObserved: false,
    missingSelectedCodes: ['5330'],
  });
  assert.deepEqual(validateResearchCandidate(data), data);
  assert.equal(data.flows[1].countries[2].shareOfWorldPercent, '0.00');
});

test('missing world and reported zero world have different unavailable reasons', () => {
  for (const zero of [false, true]) {
    const data = clone(),
      flow = data.flows[0];
    flow.world = {
      status: zero ? 'reported_zero' : 'unobserved',
      value: zero ? '0' : null,
    };
    for (const row of flow.countries) {
      if (zero) Object.assign(row, { status: 'reported_zero', value: '0' });
      Object.assign(row, {
        shareOfWorldPercent: null,
        shareUnavailableReason: zero
          ? 'zero-world-denominator'
          : 'world-not-observed',
      });
    }
    if (zero)
      Object.assign(flow.totals, {
        observedSelectedUSD: '0',
        selectedTotalUSD: '0',
      });
    flow.totals.selectedShareOfWorldPercent = null;
    assert.deepEqual(validateResearchCandidate(data), data);
  }
});

test('integer half-up rounding remains exact above the safe Number range', () => {
  const data = clone(),
    f = data.flows[0];
  f.world.value = '200000000000000000000000';
  const values = ['1001000000000000000000', '0', '0', '0'];
  f.countries.forEach((row: any, i: number) =>
    Object.assign(row, {
      value: values[i],
      status: i ? 'reported_zero' : 'reported',
      shareOfWorldPercent: i ? '0.00' : '0.50',
    }),
  );
  Object.assign(f.totals, {
    observedSelectedUSD: values[0],
    selectedTotalUSD: values[0],
    selectedShareOfWorldPercent: '0.50',
  });
  validateResearchCandidate(data);
  f.countries[0].value = '1010000000000000000000';
  f.countries[0].shareOfWorldPercent = '0.51';
  Object.assign(f.totals, {
    observedSelectedUSD: f.countries[0].value,
    selectedTotalUSD: f.countries[0].value,
    selectedShareOfWorldPercent: '0.51',
  });
  validateResearchCandidate(data);
});

test('checksum and byte count failures reject data; invalid manifest rejects before loading', async () => {
  const bytes = encodeResearchCandidate(bundle.data);
  for (const manifest of [
    { ...bundle.manifest, contentHash: '0'.repeat(64) },
    { ...bundle.manifest, contentBytes: bytes.length + 1 },
  ])
    await assert.rejects(loadResearchCandidate(manifest, () => bytes));
  for (const manifest of [
    { ...bundle.manifest, publicationState: 'published' },
    { ...bundle.manifest, contentBytes: 1000000 },
    { ...bundle.manifest, secret: 'canary' },
  ]) {
    assert.throws(() => validateResearchManifest(manifest));
    await assert.rejects(
      loadResearchCandidate(manifest, () => {
        assert.fail('Must not load');
      }),
    );
  }
});

test('matching checksums cannot admit duplicates, BOM, alternate encoding, malformed UTF8 or extras', async () => {
  const canonical = new TextDecoder().decode(
    encodeResearchCandidate(bundle.data),
  );
  const bodies = [
    canonical + ' ',
    '\ufeff' + canonical,
    canonical.replace('mat\\u00e9', 'maté'),
    canonical.replace(
      '"schemaVersion":2',
      '"schemaVersion":2,"schemaVersion":2',
    ),
    canonical.replace('{', '{"sourceQuery":"private",'),
    '{',
    '[1,2]',
  ];
  for (const body of bodies) {
    const bytes = new TextEncoder().encode(body);
    await assert.rejects(
      loadResearchCandidate(manifestFor(bytes), () => bytes),
    );
  }
  const invalid = new Uint8Array([0xff]);
  await assert.rejects(
    loadResearchCandidate(manifestFor(invalid), () => invalid),
  );
});

test('candidate results and manifest are independent deeply frozen snapshots', async () => {
  const input = clone(),
    result = validateResearchCandidate(input);
  input.flows[0].countries[0].value = '99';
  assert.equal(result.flows[0].countries[0].value, '10');
  assert.ok(Object.isFrozen(result.flows[0].countries[0]));
  const manifest = structuredClone(bundle.manifest),
    bytes = encodeResearchCandidate(bundle.data);
  const pending = loadResearchCandidate(manifest, () => bytes);
  manifest.contentHash = '0'.repeat(64);
  bytes.fill(0);
  assert.deepEqual(await pending, bundle.data);
});

test('review candidates cannot enter the existing website loader or become production by flags', async () => {
  for (const input of [
    bundle.data,
    bundle.manifest,
    bundle,
    { ...bundle.data, publicationReady: true },
  ]) {
    assert.throws(() => projectPublicRelease(input));
    assert.throws(() => validatePublicManifest(input));
    await assert.rejects(
      loadPublicRelease(input, () => {
        assert.fail('Sample loader must not fetch');
      }),
    );
  }
});

test('non-JSON input and oversized payloads fail within bounded validation', async () => {
  for (const input of [
    undefined,
    null,
    [],
    { payload: 'x'.repeat(100000) },
    { contentHash: undefined },
    { contentHash: 1n },
  ]) {
    assert.throws(() => validateResearchCandidate(input));
    assert.throws(() => validateResearchManifest(input));
  }
  const cyclic: any = {};
  cyclic.child = cyclic;
  assert.throws(() => validateResearchCandidate(cyclic));
  for (const bytes of [new Uint8Array(65537), new Uint8Array(), 'invalid']) {
    await assert.rejects(
      loadResearchCandidate(bundle.manifest, () => bytes as Uint8Array),
    );
  }
});

test('async byte loaders use a snapshot of the manifest while waiting', async () => {
  const manifest = structuredClone(bundle.manifest);
  let resolve!: (bytes: Uint8Array) => void;
  const pending = loadResearchCandidate(
    manifest,
    () =>
      new Promise<Uint8Array>((r) => {
        resolve = r;
      }),
  );
  manifest.countryCodes.reverse();
  manifest.contentBytes = 1;
  resolve(encodeResearchCandidate(bundle.data));
  assert.deepEqual(await pending, bundle.data);
});
