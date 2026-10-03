import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { csv, type Release } from '../packages/contracts/trade.ts';
import type { PublicReleaseManifest } from '../packages/contracts/public-release.ts';

const boundary = await import('../packages/contracts/public-release.ts').catch(
  () => ({}),
);
function api(name: string): (...args: any[]) => any {
  const fn = (boundary as Record<string, unknown>)[name];
  assert.equal(
    typeof fn,
    'function',
    `Missing public boundary interface: ${name}`,
  );
  return fn as (...args: any[]) => any;
}
const project = (input: unknown): Release => api('projectPublicRelease')(input);
const encode = (input: unknown): Uint8Array =>
  api('encodePublicRelease')(input);
const manifest = (input: unknown): Promise<PublicReleaseManifest> =>
  api('createSampleManifest')(input);
const validateManifest = (input: unknown): PublicReleaseManifest =>
  api('validatePublicManifest')(input);
const load = (
  input: unknown,
  bytes: (hash: string) => Uint8Array | Promise<Uint8Array>,
): Promise<Release> => api('loadPublicRelease')(input, bytes);

function fixture(): Release {
  return {
    schemaVersion: 1,
    id: 'sample-mini-v1',
    mode: 'sample',
    source: 'synthetic',
    scope: 'One illustrative chapter and two partners; synthetic only.',
    officialReleaseDate: null,
    officialRevisionDate: null,
    ingestedAt: '2026-10-02T12:00:00Z',
    revisionDetectedAt: null,
    basis: 'census-monthly-goods-nsa-usd-v1',
    products: [{ code: '09', name: 'Coffee', edition: 'HS2022' }],
    partners: [
      { id: 'canada', name: 'Canada', code: '1220', kind: 'country' },
      { id: 'world', name: 'Illustrative world', code: '-', kind: 'aggregate' },
    ],
    periods: ['2026-07'],
    observations: [
      {
        product: '09',
        partner: 'canada',
        flow: 'imports',
        period: '2026-07',
        value: '9007199254740993',
        status: 'reported',
      },
      {
        product: '09',
        partner: 'world',
        flow: 'imports',
        period: '2026-07',
        value: '9007199254740995',
        status: 'reported',
      },
      {
        product: '09',
        partner: 'canada',
        flow: 'exports',
        period: '2026-07',
        value: null,
        status: 'suppressed',
      },
      {
        product: '09',
        partner: 'world',
        flow: 'exports',
        period: '2026-07',
        value: '0',
        status: 'reported_zero',
      },
    ],
  };
}
const digest = (bytes: Uint8Array) =>
  createHash('sha256').update(bytes).digest('hex');
const bytesOf = (text: string) => new TextEncoder().encode(text);
async function bodyManifest(bytes: Uint8Array, release = fixture()) {
  return {
    ...(await manifest(release)),
    contentHash: digest(bytes),
    contentBytes: bytes.length,
  };
}

test('the public boundary exposes every planned operation', () => {
  for (const name of [
    'projectPublicRelease',
    'encodePublicRelease',
    'validatePublicManifest',
    'createSampleManifest',
    'loadPublicRelease',
  ])
    api(name);
});

test('projection omits private fields at every assembly level', () => {
  const input = fixture() as any;
  input.workspace = { notes: 'canary-private-secret' };
  input.publicationReady = true;
  input.products[0].rawQuery = 'canary-private-secret';
  input.partners[0].tenant = 'canary-private-secret';
  input.observations[0].candidate = { token: 'canary-private-secret' };
  const result = project(input);
  assert.deepEqual(result, fixture());
  assert.ok(
    !new TextDecoder().decode(encode(input)).includes('canary-private-secret'),
  );
  assert.ok(
    !csv(result, result.observations).includes('canary-private-secret'),
  );
});

test('projection creates independent deeply frozen records and arrays', () => {
  const input = fixture();
  const result = project(input);
  assert.notEqual(result, input);
  assert.notEqual(result.products, input.products);
  assert.notEqual(result.observations[0], input.observations[0]);
  for (const object of [
    result,
    result.products,
    result.products[0],
    result.partners,
    result.partners[0],
    result.periods,
    result.observations,
    result.observations[0],
  ])
    assert.ok(Object.isFrozen(object));
  input.observations[0].value = '1';
  input.products[0].name = 'Changed';
  assert.equal(result.observations[0].value, '9007199254740993');
  assert.equal(result.products[0].name, 'Coffee');
  assert.throws(() => {
    result.observations[0].value = '2';
  }, TypeError);
  assert.throws(() => {
    result.periods.push('2026-08');
  }, TypeError);
});

test('public encoding has deterministic field order and exact integer/status values', () => {
  const input = fixture();
  const reordered = Object.fromEntries(Object.entries(input).reverse());
  const bytes = encode(reordered);
  assert.equal(new TextDecoder().decode(bytes), JSON.stringify(input));
  assert.deepEqual(bytes, encode(input));
  assert.equal(project(input).observations[2].status, 'suppressed');
  assert.equal(project(input).observations[3].value, '0');
});

test('missing coverage, duplicated observations and value/status contradictions fail', () => {
  const missing = fixture();
  missing.observations.pop();
  assert.throws(() => project(missing), /coverage/i);
  const duplicate = fixture();
  duplicate.observations.push(duplicate.observations[0]);
  assert.throws(() => project(duplicate), /duplicate/i);
  const falseZero = fixture();
  falseZero.observations[0].status = 'reported_zero';
  assert.throws(() => project(falseZero), /contradiction/i);
  const falseMissing = fixture();
  falseMissing.observations[2].value = '0';
  assert.throws(() => project(falseMissing), /null/i);
});

test('all unavailable states remain explicit nulls instead of zero', () => {
  for (const status of [
    'suppressed',
    'not_available',
    'not_applicable',
    'not_reported',
  ] as const) {
    const input = fixture();
    input.observations[2].status = status;
    const result = project(input);
    assert.equal(result.observations[2].value, null);
    assert.equal(result.observations[2].status, status);
  }
});

test('projection rejects official labels, private evidence and claimed official dates', () => {
  const official = {
    ...fixture(),
    mode: 'official',
    source: 'census',
    publicationReady: true,
  };
  assert.throws(() => project(official), /sample|unsupported/i);
  for (const state of [
    'candidate',
    'private-partner-discovery',
    'private-validation',
  ])
    assert.throws(() =>
      project({ schemaVersion: 1, state, rows: [], publicationReady: true }),
    );
  for (const field of [
    'officialReleaseDate',
    'officialRevisionDate',
    'revisionDetectedAt',
  ])
    assert.throws(
      () =>
        project({
          ...fixture(),
          [field]:
            field === 'revisionDetectedAt'
              ? '2026-10-02T13:00:00Z'
              : '2026-09-03',
        }),
      /sample|date/i,
    );
});

test('private provenance and selected-country reports cannot enter the public loader', async () => {
  const receipt = {
    schemaVersion: 1,
    state: 'private-acquisition-snapshot',
    claim: 'verified-acquisition-snapshot-only',
    validation: {
      archiveConsistencyVerified: true,
      sourceAuthenticityAttested: false,
    },
    source: { query: { privateEvidence: 'fabricated-private-canary' } },
    publicationReady: false,
  };
  let reads = 0;
  const selected = {
    schemaVersion: 1,
    state: 'private-selected-partner-report',
    provenance: receipt,
    rows: [{ code: '1220', value: 'fabricated-private-canary' }],
    publicationReady: false,
  };
  for (const input of [
    receipt,
    selected,
    { ...receipt, publicationReady: true },
    { ...selected, publicationReady: true },
  ]) {
    assert.throws(() => project(input));
    assert.throws(() => validateManifest(input));
    await assert.rejects(() =>
      load(input, () => {
        reads++;
        throw new Error('Private payload must never be read');
      }),
    );
  }
  assert.equal(reads, 0);
});

test('array limits reject before copying nested assembly records', () => {
  for (const [field, limit] of [
    ['products', 99],
    ['partners', 300],
    ['periods', 72],
    ['observations', 5000],
  ] as const) {
    const input = fixture() as any;
    const entries = new Array(limit + 1);
    Object.defineProperty(entries, '0', {
      get() {
        throw new Error('copied before validating bounds');
      },
    });
    input[field] = entries;
    assert.throws(() => project(input), /bounds|limit|too many/i);
  }
});

test('a valid large Cartesian release cannot exceed the public byte budget', () => {
  const input = fixture();
  input.products = Array.from({ length: 50 }, (_, i) => ({
    code: String(i + 1).padStart(2, '0'),
    name: 'Illustration',
    edition: 'HS2022' as const,
  }));
  input.partners = [
    ...Array.from({ length: 49 }, (_, i) => ({
      id: `country-${i}`,
      name: 'Illustration',
      code: String(i).padStart(4, '0'),
      kind: 'country' as const,
    })),
    input.partners[1],
  ];
  input.observations = input.products.flatMap((p) =>
    input.partners.flatMap((partner) =>
      (['imports', 'exports'] as const).map((flow) => ({
        product: p.code,
        partner: partner.id,
        flow,
        period: '2026-07',
        value: '123456789012345678901234',
        status: 'reported' as const,
      })),
    ),
  );
  assert.equal(input.observations.length, 5000);
  assert.throws(() => encode(input), /byte|oversized|budget/i);
});

test('sample manifest pins independent SHA-256, exact byte count and public meaning', async () => {
  const input = fixture();
  const result = await manifest(input);
  const bytes = bytesOf(JSON.stringify(input));
  assert.deepEqual(result, {
    schemaVersion: 1,
    artifact: 'public-trade-release',
    mode: 'sample',
    source: 'synthetic',
    releaseId: 'sample-mini-v1',
    releaseSchemaVersion: 1,
    contentHash: digest(bytes),
    contentBytes: bytes.length,
    basis: 'census-monthly-goods-nsa-usd-v1',
    scope: input.scope,
    coverage: {
      kind: 'selected-synthetic-fixture',
      productCodes: ['09'],
      partnerIds: ['canada', 'world'],
      periods: ['2026-07'],
      flows: ['imports', 'exports'],
      worldControlScope: 'included-synthetic-chapters',
    },
    classification: {
      system: 'HS',
      edition: 'HS2022',
      level: 'HS2',
      claim: 'synthetic-label-only',
    },
    provenance: {
      claim: 'synthetic-illustration-only',
      officialReleaseDate: null,
      officialRevisionDate: null,
      ingestedAt: '2026-10-02T12:00:00Z',
      revisionDetectedAt: null,
    },
  });
  assert.ok(Object.isFrozen(result));
  assert.ok(Object.isFrozen(result.coverage.productCodes));
});

test('manifest validation clones and freezes its input independently', async () => {
  const input = JSON.parse(JSON.stringify(await manifest(fixture())));
  const result = validateManifest(input);
  input.coverage.partnerIds[0] = 'changed';
  input.provenance.ingestedAt = '2026-10-03T12:00:00Z';
  assert.equal(result.coverage.partnerIds[0], 'canada');
  assert.equal(result.provenance.ingestedAt, '2026-10-02T12:00:00Z');
  assert.ok(Object.isFrozen(result.provenance));
  assert.throws(() => {
    result.coverage.partnerIds.push('extra');
  }, TypeError);
});

test('manifest rejects unknown nested fields, invalid dates, basis and classification', async () => {
  const original = await manifest(fixture());
  const mutate = (change: (copy: any) => void) => {
    const copy = JSON.parse(JSON.stringify(original));
    change(copy);
    assert.throws(() => validateManifest(copy));
  };
  for (const change of [
    (m: any) => {
      m.workspace = { notes: 'private' };
    },
    (m: any) => {
      m.coverage.inventoryApproved = true;
    },
    (m: any) => {
      m.classification.sourceHash = 'a'.repeat(64);
    },
    (m: any) => {
      m.provenance.apiVintageVerified = true;
    },
    (m: any) => {
      m.provenance.officialReleaseDate = '2026-09-03';
    },
    (m: any) => {
      m.provenance.officialRevisionDate = '2026-09-03';
    },
    (m: any) => {
      m.provenance.revisionDetectedAt = '2026-10-02T13:00:00Z';
    },
    (m: any) => {
      m.provenance.ingestedAt = '2026-02-30T12:00:00Z';
    },
    (m: any) => {
      m.basis = 'bop-goods-and-services';
    },
    (m: any) => {
      m.classification.edition = 'HS2027';
    },
    (m: any) => {
      m.classification.claim = 'verified';
    },
    (m: any) => {
      m.contentBytes = 512 * 1024 + 1;
    },
    (m: any) => {
      m.contentHash = 'A'.repeat(64);
    },
    (m: any) => {
      m.coverage.flows.reverse();
    },
    (m: any) => {
      m.coverage.periods = ['2026-13'];
    },
    (m: any) => {
      m.coverage.productCodes = ['09', '09'];
    },
    (m: any) => {
      m.coverage.partnerIds = ['canada'];
    },
  ])
    mutate(change);
});

test('unsupported and malformed manifests fail before byte callbacks', async () => {
  const original = await manifest(fixture());
  let reads = 0;
  for (const input of [
    { ...original, mode: 'official', source: 'census', publicationReady: true },
    { ...original, schemaVersion: 2 },
    { ...original, artifact: 'private-candidate' },
    {
      ...original,
      coverage: { ...original.coverage, partnerIds: new Array(301).fill('x') },
    },
    { ...original, scope: 'x'.repeat(65537) },
  ]) {
    await assert.rejects(() =>
      load(input, () => {
        reads++;
        return encode(fixture());
      }),
    );
  }
  assert.equal(reads, 0);
});

test('loader returns the same public release from the pinned hash', async () => {
  const input = fixture();
  const m = await manifest(input);
  const bytes = encode(input);
  const result = await load(m, (hash) => {
    assert.equal(hash, digest(bytes));
    return bytes;
  });
  assert.deepEqual(result, fixture());
  assert.ok(Object.isFrozen(result.observations[0]));
});

test('loader rejects tampered, truncated, oversized and nonbyte bodies', async () => {
  const input = fixture();
  const m = await manifest(input);
  const bytes = encode(input);
  const tampered = bytes.slice();
  tampered[tampered.length - 2] ^= 1;
  for (const body of [
    tampered,
    bytes.slice(0, -1),
    new Uint8Array(512 * 1024 + 1),
    'not bytes',
  ])
    await assert.rejects(() => load(m, () => body as Uint8Array));
  await assert.rejects(() =>
    load({ ...m, contentBytes: bytes.length - 1 }, () => bytes),
  );
});

test('loader binds DTO identity, scope, ordered coverage and provenance to the manifest', async () => {
  const bytes = encode(fixture());
  const original = await manifest(fixture());
  for (const change of [
    (m: any) => {
      m.releaseId = 'different-release';
    },
    (m: any) => {
      m.scope = 'Different synthetic scope';
    },
    (m: any) => {
      m.coverage.productCodes = ['10'];
    },
    (m: any) => {
      m.coverage.partnerIds.reverse();
    },
    (m: any) => {
      m.coverage.periods = ['2026-06'];
    },
    (m: any) => {
      m.provenance.ingestedAt = '2026-10-03T12:00:00Z';
    },
  ]) {
    const changed = JSON.parse(JSON.stringify(original));
    change(changed);
    await assert.rejects(
      () => load(changed, () => bytes),
      /match|coverage|identity|metadata/i,
    );
  }
});

test('duplicate JSON fields and noncanonical encoding fail even with a matching digest', async () => {
  const text = JSON.stringify(fixture());
  for (const body of [
    text.replace('"schemaVersion":1', '"schemaVersion":1,"schemaVersion":1'),
    text.replace('"code":"09"', '"code":"09","code":"09"'),
    text + '\n',
    '\uFEFF' + text,
    JSON.stringify(fixture(), null, 2),
    JSON.stringify(Object.fromEntries(Object.entries(fixture()).reverse())),
    text.replace('Coffee', 'Coff\\u0065e'),
  ]) {
    const bytes = bytesOf(body);
    const pinned = await bodyManifest(bytes);
    await assert.rejects(
      () => load(pinned, () => bytes),
      /canonical|encoding/i,
    );
  }
});

test('unknown public JSON fields cannot be discarded into a valid downloaded DTO', async () => {
  for (const mutate of [
    (r: any) => {
      r.workspace = 'canary-private-secret';
    },
    (r: any) => {
      r.products[0].token = 'canary-private-secret';
    },
    (r: any) => {
      r.partners[0].tenant = 'canary-private-secret';
    },
    (r: any) => {
      r.observations[0].sourceQuery = 'canary-private-secret';
    },
  ]) {
    const input = fixture();
    mutate(input);
    const bytes = bytesOf(JSON.stringify(input));
    const pinned = await bodyManifest(bytes);
    await assert.rejects(() => load(pinned, () => bytes), /canonical/i);
  }
});

test('malformed UTF-8 fails despite a matching byte digest', async () => {
  const bytes = encode(fixture());
  const index = new TextDecoder().decode(bytes).indexOf('Coffee');
  bytes[index] = 0xff;
  const pinned = await bodyManifest(bytes);
  await assert.rejects(() => load(pinned, () => bytes), /encoding|UTF/i);
});

test('loader snapshots mutable callback bytes before asynchronous hashing', async () => {
  const m = await manifest(fixture());
  const bytes = encode(fixture());
  const loaded = load(m, () => bytes);
  queueMicrotask(() => bytes.fill(0));
  assert.deepEqual(await loaded, fixture());
});

test('loader snapshots mutable manifest metadata before asynchronous loading', async () => {
  const m = JSON.parse(JSON.stringify(await manifest(fixture())));
  const loaded = load(m, async () => {
    m.scope = 'changed';
    m.coverage.partnerIds[0] = 'changed';
    return encode(fixture());
  });
  assert.deepEqual(await loaded, fixture());
});

test('pinned repository sample manifest equals independently hashed canonical sample bytes', async () => {
  const sample = JSON.parse(
    readFileSync(
      new URL('./fixtures/sample-release.json', import.meta.url),
      'utf8',
    ),
  );
  const pinned = JSON.parse(
    readFileSync(
      new URL('../releases/sample-2026-07-v1.manifest.json', import.meta.url),
      'utf8',
    ),
  );
  const bytes = encode(sample);
  assert.equal(pinned.contentHash, digest(bytes));
  assert.equal(pinned.contentBytes, bytes.length);
  assert.deepEqual(pinned, await manifest(sample));
  assert.deepEqual(await load(pinned, () => bytes), sample);
});
