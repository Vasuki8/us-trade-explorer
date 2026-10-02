import { validateRelease, type Release } from './trade.ts';

export const MAX_PUBLIC_RELEASE_BYTES = 512 * 1024;
export const MAX_PUBLIC_MANIFEST_BYTES = 64 * 1024;
const BASIS = 'census-monthly-goods-nsa-usd-v1';
const ARRAY_LIMITS = {
  products: 99,
  partners: 300,
  periods: 72,
  observations: 5000,
} as const;
const encoder = new TextEncoder();

export interface PublicReleaseManifest {
  schemaVersion: 1;
  artifact: 'public-trade-release';
  mode: 'sample';
  source: 'synthetic';
  releaseId: string;
  releaseSchemaVersion: 1;
  contentHash: string;
  contentBytes: number;
  basis: typeof BASIS;
  scope: string;
  coverage: {
    kind: 'selected-synthetic-fixture';
    productCodes: string[];
    partnerIds: string[];
    periods: string[];
    flows: ['imports', 'exports'];
    worldControlScope: 'included-synthetic-chapters';
  };
  classification: {
    system: 'HS';
    edition: 'HS2022';
    level: 'HS2';
    claim: 'synthetic-label-only';
  };
  provenance: {
    claim: 'synthetic-illustration-only';
    officialReleaseDate: null;
    officialRevisionDate: null;
    ingestedAt: string;
    revisionDetectedAt: null;
  };
}

function requireThat(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}
function object(value: unknown): asserts value is Record<string, unknown> {
  requireThat(
    value !== null && typeof value === 'object' && !Array.isArray(value),
    'Expected public object',
  );
}
function keys(value: Record<string, unknown>, expected: string[]) {
  requireThat(
    Object.keys(value).length === expected.length &&
      Object.keys(value).every((key) => expected.includes(key)),
    'Unexpected or missing public manifest field',
  );
}
function text(value: unknown, maximum: number): asserts value is string {
  requireThat(
    typeof value === 'string' &&
      value.length > 0 &&
      value.length <= maximum &&
      !/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(value),
    'Invalid public text',
  );
}
function array(value: unknown, maximum: number): asserts value is unknown[] {
  requireThat(
    Array.isArray(value) && value.length > 0 && value.length <= maximum,
    'Public array bounds exceeded',
  );
}
function freeze<T>(value: T): T {
  if (value !== null && typeof value === 'object') {
    for (const item of Object.values(value)) freeze(item);
    Object.freeze(value);
  }
  return value;
}

/** Explicit public allowlist; private assembly fields are never serialized. */
export function projectPublicRelease(input: unknown): Release {
  object(input);
  const mode = input.mode,
    source = input.source;
  requireThat(
    mode === 'sample' && source === 'synthetic',
    'Only sample/synthetic public releases are supported',
  );
  for (const [field, maximum] of Object.entries(ARRAY_LIMITS))
    array(input[field], maximum);
  const products = input.products as unknown[],
    partners = input.partners as unknown[],
    observations = input.observations as unknown[];
  const projected = {
    schemaVersion: input.schemaVersion,
    id: input.id,
    mode,
    source,
    scope: input.scope,
    officialReleaseDate: input.officialReleaseDate,
    officialRevisionDate: input.officialRevisionDate,
    ingestedAt: input.ingestedAt,
    revisionDetectedAt: input.revisionDetectedAt,
    basis: input.basis,
    products: products.map((product) => {
      object(product);
      return {
        code: product.code,
        name: product.name,
        edition: product.edition,
      };
    }),
    partners: partners.map((partner) => {
      object(partner);
      return {
        id: partner.id,
        name: partner.name,
        code: partner.code,
        kind: partner.kind,
      };
    }),
    periods: [...(input.periods as unknown[])],
    observations: observations.map((row) => {
      object(row);
      return {
        product: row.product,
        partner: row.partner,
        flow: row.flow,
        period: row.period,
        value: row.value,
        status: row.status,
      };
    }),
  };
  const release = validateRelease(projected);
  requireThat(
    release.officialReleaseDate === null &&
      release.officialRevisionDate === null &&
      release.revisionDetectedAt === null,
    'Sample official and revision dates must be null',
  );
  return freeze(release);
}

/** UTF-8 JSON with the explicit DTO field order and no trailing whitespace. */
export function encodePublicRelease(input: unknown): Uint8Array {
  const bytes = encoder.encode(JSON.stringify(projectPublicRelease(input)));
  requireThat(
    bytes.length <= MAX_PUBLIC_RELEASE_BYTES,
    'Public release byte budget exceeded',
  );
  return bytes;
}

function stringArray(
  value: unknown,
  maximum: number,
  pattern: RegExp,
): string[] {
  array(value, maximum);
  requireThat(
    value.every((item) => typeof item === 'string' && pattern.test(item)) &&
      new Set(value).size === value.length,
    'Invalid or duplicate public coverage',
  );
  return [...value] as string[];
}
function timestamp(value: unknown): asserts value is string {
  text(value, 30);
  requireThat(
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(value),
    'Invalid public ingestion date',
  );
  const date = new Date(value);
  requireThat(
    Number.isFinite(date.valueOf()) &&
      date.toISOString() === value.replace('Z', '.000Z'),
    'Invalid public ingestion date',
  );
}

/** Checks metadata independently, before requesting any release bytes. */
export function validatePublicManifest(input: unknown): PublicReleaseManifest {
  object(input);
  keys(input, [
    'schemaVersion',
    'artifact',
    'mode',
    'source',
    'releaseId',
    'releaseSchemaVersion',
    'contentHash',
    'contentBytes',
    'basis',
    'scope',
    'coverage',
    'classification',
    'provenance',
  ]);
  requireThat(
    input.schemaVersion === 1 &&
      input.releaseSchemaVersion === 1 &&
      input.artifact === 'public-trade-release',
    'Unsupported public manifest schema',
  );
  requireThat(
    input.mode === 'sample' && input.source === 'synthetic',
    'Only sample/synthetic public manifests are supported',
  );
  requireThat(input.basis === BASIS, 'Unsupported public statistical basis');
  text(input.releaseId, 80);
  requireThat(
    /^[a-z0-9][a-z0-9-]{2,79}$/.test(input.releaseId),
    'Invalid public release identity',
  );
  text(input.contentHash, 64);
  requireThat(
    /^[a-f0-9]{64}$/.test(input.contentHash),
    'Invalid public content hash',
  );
  requireThat(
    typeof input.contentBytes === 'number' &&
      Number.isSafeInteger(input.contentBytes) &&
      input.contentBytes > 0 &&
      input.contentBytes <= MAX_PUBLIC_RELEASE_BYTES,
    'Invalid public content byte count',
  );
  text(input.scope, 500);
  object(input.coverage);
  keys(input.coverage, [
    'kind',
    'productCodes',
    'partnerIds',
    'periods',
    'flows',
    'worldControlScope',
  ]);
  requireThat(
    input.coverage.kind === 'selected-synthetic-fixture' &&
      input.coverage.worldControlScope === 'included-synthetic-chapters',
    'Unsupported public coverage claim',
  );
  const productCodes = stringArray(
    input.coverage.productCodes,
    ARRAY_LIMITS.products,
    /^\d{2}$/,
  );
  const partnerIds = stringArray(
    input.coverage.partnerIds,
    ARRAY_LIMITS.partners,
    /^[a-z][a-z0-9-]{0,49}$/,
  );
  requireThat(
    partnerIds.includes('world'),
    'Public coverage requires illustrative world',
  );
  const periods = stringArray(
    input.coverage.periods,
    ARRAY_LIMITS.periods,
    /^20\d{2}-(0[1-9]|1[0-2])$/,
  );
  requireThat(
    periods.every(
      (period, index) => index === 0 || period > periods[index - 1],
    ),
    'Public periods must be ordered',
  );
  requireThat(
    Array.isArray(input.coverage.flows) &&
      input.coverage.flows.length === 2 &&
      input.coverage.flows[0] === 'imports' &&
      input.coverage.flows[1] === 'exports',
    'Unsupported public flows',
  );
  object(input.classification);
  keys(input.classification, ['system', 'edition', 'level', 'claim']);
  requireThat(
    input.classification.system === 'HS' &&
      input.classification.edition === 'HS2022' &&
      input.classification.level === 'HS2' &&
      input.classification.claim === 'synthetic-label-only',
    'Unsupported public classification claim',
  );
  object(input.provenance);
  keys(input.provenance, [
    'claim',
    'officialReleaseDate',
    'officialRevisionDate',
    'ingestedAt',
    'revisionDetectedAt',
  ]);
  requireThat(
    input.provenance.claim === 'synthetic-illustration-only' &&
      input.provenance.officialReleaseDate === null &&
      input.provenance.officialRevisionDate === null &&
      input.provenance.revisionDetectedAt === null,
    'Unsupported sample provenance or official dates',
  );
  timestamp(input.provenance.ingestedAt);
  const manifest: PublicReleaseManifest = {
    schemaVersion: 1,
    artifact: 'public-trade-release',
    mode: 'sample',
    source: 'synthetic',
    releaseId: input.releaseId,
    releaseSchemaVersion: 1,
    contentHash: input.contentHash,
    contentBytes: input.contentBytes,
    basis: BASIS,
    scope: input.scope,
    coverage: {
      kind: 'selected-synthetic-fixture',
      productCodes,
      partnerIds,
      periods,
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
      ingestedAt: input.provenance.ingestedAt,
      revisionDetectedAt: null,
    },
  };
  requireThat(
    encoder.encode(JSON.stringify(manifest)).length <=
      MAX_PUBLIC_MANIFEST_BYTES,
    'Public manifest byte budget exceeded',
  );
  return freeze(manifest);
}

async function sha256(bytes: Uint8Array): Promise<string> {
  const digest = await crypto.subtle.digest(
    'SHA-256',
    new Uint8Array(bytes).buffer,
  );
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
}
function metadata(release: Release) {
  return {
    schemaVersion: 1,
    artifact: 'public-trade-release',
    mode: 'sample',
    source: 'synthetic',
    releaseId: release.id,
    releaseSchemaVersion: release.schemaVersion,
    basis: release.basis,
    scope: release.scope,
    coverage: {
      kind: 'selected-synthetic-fixture',
      productCodes: release.products.map((product) => product.code),
      partnerIds: release.partners.map((partner) => partner.id),
      periods: [...release.periods],
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
      officialReleaseDate: release.officialReleaseDate,
      officialRevisionDate: release.officialRevisionDate,
      ingestedAt: release.ingestedAt,
      revisionDetectedAt: release.revisionDetectedAt,
    },
  };
}

/** Hashes prove download consistency; they do not approve official statistics. */
export async function createSampleManifest(
  input: unknown,
): Promise<PublicReleaseManifest> {
  const release = projectPublicRelease(input),
    bytes = encodePublicRelease(release);
  const fields = metadata(release);
  return validatePublicManifest({
    schemaVersion: fields.schemaVersion,
    artifact: fields.artifact,
    mode: fields.mode,
    source: fields.source,
    releaseId: fields.releaseId,
    releaseSchemaVersion: fields.releaseSchemaVersion,
    contentHash: await sha256(bytes),
    contentBytes: bytes.length,
    basis: fields.basis,
    scope: fields.scope,
    coverage: fields.coverage,
    classification: fields.classification,
    provenance: fields.provenance,
  });
}

export async function loadPublicRelease(
  input: unknown,
  loadBytes: (contentHash: string) => Uint8Array | Promise<Uint8Array>,
): Promise<Release> {
  const manifest = validatePublicManifest(input);
  requireThat(typeof loadBytes === 'function', 'Missing public byte loader');
  const pending = loadBytes(manifest.contentHash);
  // Snapshot a synchronous result before yielding, including Node Buffer views.
  const received = pending instanceof Uint8Array ? pending : await pending;
  requireThat(
    received instanceof Uint8Array &&
      received.length > 0 &&
      received.length <= MAX_PUBLIC_RELEASE_BYTES,
    'Missing or oversized public release bytes',
  );
  const bytes = new Uint8Array(received);
  requireThat(
    bytes.length === manifest.contentBytes,
    'Public release byte count mismatch',
  );
  requireThat(
    (await sha256(bytes)) === manifest.contentHash,
    'Public release checksum mismatch',
  );
  let decoded: unknown;
  try {
    decoded = JSON.parse(
      new TextDecoder('utf-8', { fatal: true }).decode(bytes),
    );
  } catch {
    throw new Error('Invalid public release JSON or UTF-8 encoding');
  }
  const release = projectPublicRelease(decoded),
    canonical = encodePublicRelease(release);
  requireThat(
    bytes.length === canonical.length &&
      bytes.every((byte, index) => byte === canonical[index]),
    'Public release is not canonical JSON',
  );
  const expected = metadata(release);
  requireThat(
    manifest.releaseId === expected.releaseId &&
      manifest.releaseSchemaVersion === expected.releaseSchemaVersion &&
      manifest.basis === expected.basis &&
      manifest.scope === expected.scope &&
      JSON.stringify(manifest.coverage) === JSON.stringify(expected.coverage) &&
      JSON.stringify(manifest.classification) ===
        JSON.stringify(expected.classification) &&
      JSON.stringify(manifest.provenance) ===
        JSON.stringify(expected.provenance),
    'Public release metadata does not match manifest',
  );
  return release;
}
