/** Unpublished review contract. Deliberately not imported by the website loader. */
export const MAX_RESEARCH_BYTES = 64 * 1024;
const MAX_MANIFEST_BYTES = 8 * 1024;
const FLOWS = ['imports', 'exports'] as const;
const COUNTRIES = [
  ['1220', 'Canada', null],
  ['2010', 'Mexico', 'Includes Isla de Cozumel and Islas Revillagigedo.'],
  ['5330', 'India', 'Includes the Andaman, Nicobar, and Laccadive Islands.'],
  [
    '5700',
    'China',
    'Hong Kong, Macao and Taiwan have separate Schedule C designations.',
  ],
] as const;
const POLICY = {
  countryValues: 'selected-countries-same-flow-and-period-only',
  countryWorldShares: 'requires-observed-positive-world-control',
  historicalGrowth: 'not-supported',
  fineCodeJoins: 'not-supported',
  quantityMetrics: 'not-supported',
  globalRankingsAndConcentration: 'not-supported',
} as const;
type Flow = (typeof FLOWS)[number];
type Status = 'reported' | 'reported_zero' | 'unobserved';
type Observation = { status: Status; value: string | null };
type Country = Observation & {
  code: string;
  name: string;
  geographicNote: string | null;
  shareOfWorldPercent: string | null;
  shareUnavailableReason: string | null;
};
type ResearchFlow = {
  flow: Flow;
  statisticalBasis: Record<string, string>;
  source: { agency: string; datasetURL: string };
  times: {
    retrievedAt: string;
    officialReleaseDate: null;
    officialRevisionDate: null;
    revisionDetectedAt: null;
    publishedAt: null;
  };
  classification: {
    system: string;
    referenceURLs: string[];
    apiClassificationVintage: 'not-identified';
    provisionEffectiveFromVerified: null;
    historicalComparability: 'not-established';
  };
  world: Observation;
  countries: Country[];
  totals: {
    observedSelectedUSD: string;
    selectedTotalUSD: string | null;
    selectedShareOfWorldPercent: string | null;
  };
  coverage: { allSelectedObserved: boolean; missingSelectedCodes: string[] };
};
export type ResearchCandidate = {
  geography: {
    system: 'Schedule C';
    claim: 'selected-schedule-c-designations-only';
    effectiveFromVerified: null;
    referenceURLs: string[];
  };
  schemaVersion: 2;
  artifact: 'public-research-candidate-data';
  source: 'census';
  publicationState: 'unpublished-review';
  scope: {
    reporter: 'US';
    period: '2026-07';
    periodKind: 'month';
    product: { code: '09'; name: string; level: 'HS2' };
  };
  coverage: {
    kind: 'selected-four-country-subset';
    globalCoverageComplete: false;
  };
  analysisPolicy: typeof POLICY;
  flows: ResearchFlow[];
};
export type ResearchManifest = {
  schemaVersion: 2;
  artifact: 'public-research-candidate';
  source: 'census';
  publicationState: 'unpublished-review';
  period: '2026-07';
  productCode: '09';
  flows: Flow[];
  countryCodes: string[];
  contentHash: string;
  contentBytes: number;
};

function requireThat(
  condition: unknown,
  message = 'Invalid research candidate',
): asserts condition {
  if (!condition) throw new Error(message);
}
function object(
  value: unknown,
  fields: string[],
): asserts value is Record<string, unknown> {
  requireThat(
    value !== null && typeof value === 'object' && !Array.isArray(value),
  );
  const keys = Object.keys(value);
  requireThat(
    keys.length === fields.length &&
      fields.every((key) => Object.hasOwn(value, key)),
  );
}
function same(actual: unknown, expected: unknown): void {
  requireThat(JSON.stringify(actual) === JSON.stringify(expected));
}
function fixed(actual: unknown, expected: Record<string, unknown>): void {
  object(actual, Object.keys(expected));
  for (const key of Object.keys(expected)) same(actual[key], expected[key]);
}
// Bound unknown objects before serializing; reject non-JSON types rather than
// silently dropping undefined/private keys. Snapshot before any asynchronous work.
function snapshot(input: unknown, maxBytes: number): unknown {
  let nodes = 0;
  function inspect(value: unknown, depth: number): void {
    requireThat(++nodes <= 2000 && depth <= 12);
    if (value === null || typeof value === 'boolean') return;
    if (typeof value === 'string') {
      requireThat(value.length <= 2048);
      return;
    }
    if (typeof value === 'number') {
      requireThat(Number.isFinite(value));
      return;
    }
    requireThat(typeof value === 'object');
    if (Array.isArray(value)) {
      requireThat(
        value.length <= 100 && Object.keys(value).length === value.length,
      );
      for (const item of value) inspect(item, depth + 1);
    } else {
      requireThat(
        Object.getPrototypeOf(value) === Object.prototype ||
          Object.getPrototypeOf(value) === null,
      );
      const entries = Object.entries(value);
      requireThat(
        entries.length <= 32 &&
          Reflect.ownKeys(value).length === entries.length,
      );
      for (const [key, item] of entries) {
        requireThat(key.length <= 80);
        inspect(item, depth + 1);
      }
    }
  }
  inspect(input, 0);
  const json = JSON.stringify(input);
  requireThat(new TextEncoder().encode(json).length <= maxBytes);
  return JSON.parse(json);
}
function freeze<T>(value: T): T {
  if (value !== null && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}
function references(flow: Flow): string[] {
  if (flow === 'imports')
    return [11, 12, 13, 14].map(
      (rev) =>
        `https://hts.usitc.gov/reststop/file?release=2026HTSRev${rev}&filename=Chapter%209`,
    );
  return ['index.html', 'c09.pdf'].map(
    (name) => `https://www.census.gov/foreign-trade/schedules/b/2026/${name}`,
  );
}
function basis(flow: Flow): Record<string, string> {
  return {
    reporter: 'US',
    periodKind: 'month',
    tradeBasis:
      flow === 'imports'
        ? 'general-imports'
        : 'total-exports-domestic-plus-reexports',
    valuation: flow === 'imports' ? 'customs-value' : 'FAS-value',
    measure: flow === 'imports' ? 'GEN_VAL_MO' : 'ALL_VAL_MO',
    unit: 'USD',
    priceBasis: 'nominal',
    seasonalAdjustment: 'not-seasonally-adjusted',
    commodityClassification: flow === 'imports' ? 'HTS' : 'Schedule B',
    commodityLevel: 'HS2',
  };
}
function amount(value: unknown): bigint {
  requireThat(
    typeof value === 'string' && /^(0|[1-9][0-9]{0,23})$/.test(value),
  );
  return BigInt(value);
}
function observation(value: Record<string, unknown>): bigint | null {
  if (value.status === 'unobserved') {
    requireThat(value.value === null);
    return null;
  }
  const number = amount(value.value);
  requireThat(value.status === (number === 0n ? 'reported_zero' : 'reported'));
  return number;
}
function share(
  value: bigint | null,
  world: bigint | null,
): [string | null, string | null] {
  if (value === null) return [null, 'partner-not-observed'];
  if (world === null) return [null, 'world-not-observed'];
  if (world === 0n) return [null, 'zero-world-denominator'];
  const hundredths = (value * 20000n + world) / (2n * world);
  return [
    `${hundredths / 100n}.${String(hundredths % 100n).padStart(2, '0')}`,
    null,
  ];
}
function validateFlow(input: unknown, flow: Flow): void {
  object(input, [
    'flow',
    'statisticalBasis',
    'source',
    'times',
    'classification',
    'world',
    'countries',
    'totals',
    'coverage',
  ]);
  same(input.flow, flow);
  fixed(input.statisticalBasis, basis(flow));
  fixed(input.source, {
    agency: 'US Census Bureau',
    datasetURL: `https://api.census.gov/data/timeseries/intltrade/${flow}/hs`,
  });
  object(input.times, [
    'retrievedAt',
    'officialReleaseDate',
    'officialRevisionDate',
    'revisionDetectedAt',
    'publishedAt',
  ]);
  const time = input.times.retrievedAt;
  requireThat(
    typeof time === 'string' &&
      /^20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(time),
  );
  requireThat(
    Number.isFinite(Date.parse(time)) &&
      new Date(time).toISOString() === time.replace('Z', '.000Z'),
  );
  for (const key of [
    'officialReleaseDate',
    'officialRevisionDate',
    'revisionDetectedAt',
    'publishedAt',
  ])
    same(input.times[key], null);
  fixed(input.classification, {
    system: flow === 'imports' ? 'HTSUS' : 'Schedule B',
    referenceURLs: references(flow),
    apiClassificationVintage: 'not-identified',
    provisionEffectiveFromVerified: null,
    historicalComparability: 'not-established',
  });
  object(input.world, ['status', 'value']);
  const world = observation(input.world);
  requireThat(
    Array.isArray(input.countries) &&
      input.countries.length === COUNTRIES.length,
  );
  const missing: string[] = [];
  let sum = 0n;
  input.countries.forEach((row, index) => {
    object(row, [
      'code',
      'name',
      'geographicNote',
      'status',
      'value',
      'shareOfWorldPercent',
      'shareUnavailableReason',
    ]);
    const [code, name, note] = COUNTRIES[index];
    same(row.code, code);
    same(row.name, name);
    same(row.geographicNote, note);
    const value = observation(row);
    if (value === null) missing.push(code);
    else sum += value;
    const [percent, reason] = share(value, world);
    same(row.shareOfWorldPercent, percent);
    same(row.shareUnavailableReason, reason);
  });
  requireThat(
    world === null || sum <= world,
    'Selected subtotal exceeds world',
  );
  fixed(input.coverage, {
    allSelectedObserved: missing.length === 0,
    missingSelectedCodes: missing,
  });
  fixed(input.totals, {
    observedSelectedUSD: String(sum),
    selectedTotalUSD: missing.length ? null : String(sum),
    selectedShareOfWorldPercent: share(missing.length ? null : sum, world)[0],
  });
}
export function validateResearchCandidate(input: unknown): ResearchCandidate {
  const value = snapshot(input, MAX_RESEARCH_BYTES);
  object(value, [
    'schemaVersion',
    'artifact',
    'source',
    'publicationState',
    'scope',
    'coverage',
    'geography',
    'analysisPolicy',
    'flows',
  ]);
  same(value.schemaVersion, 2);
  same(value.artifact, 'public-research-candidate-data');
  same(value.source, 'census');
  same(value.publicationState, 'unpublished-review');
  object(value.scope, ['reporter', 'period', 'periodKind', 'product']);
  same(value.scope.reporter, 'US');
  same(value.scope.period, '2026-07');
  same(value.scope.periodKind, 'month');
  fixed(value.scope.product, {
    code: '09',
    name: 'Coffee, tea, maté and spices',
    level: 'HS2',
  });
  fixed(value.coverage, {
    kind: 'selected-four-country-subset',
    globalCoverageComplete: false,
  });
  fixed(value.analysisPolicy, POLICY);
  fixed(value.geography, {
    system: 'Schedule C',
    claim: 'selected-schedule-c-designations-only',
    effectiveFromVerified: null,
    referenceURLs: [11, 12, 13, 14].map(
      (rev) =>
        `https://hts.usitc.gov/reststop/file?release=2026HTSRev${rev}&filename=Statistical%20Annexes`,
    ),
  });
  requireThat(
    Array.isArray(value.flows) && value.flows.length === FLOWS.length,
  );
  value.flows.forEach((entry, index) => validateFlow(entry, FLOWS[index]));
  return freeze(value as ResearchCandidate);
}
export function validateResearchManifest(input: unknown): ResearchManifest {
  const value = snapshot(input, MAX_MANIFEST_BYTES);
  object(value, [
    'schemaVersion',
    'artifact',
    'source',
    'publicationState',
    'period',
    'productCode',
    'flows',
    'countryCodes',
    'contentHash',
    'contentBytes',
  ]);
  same(value.schemaVersion, 2);
  same(value.artifact, 'public-research-candidate');
  same(value.source, 'census');
  same(value.publicationState, 'unpublished-review');
  same(value.period, '2026-07');
  same(value.productCode, '09');
  same(value.flows, FLOWS);
  same(
    value.countryCodes,
    COUNTRIES.map((row) => row[0]),
  );
  requireThat(
    typeof value.contentHash === 'string' &&
      /^[a-f0-9]{64}$/.test(value.contentHash),
  );
  requireThat(
    typeof value.contentBytes === 'number' &&
      Number.isSafeInteger(value.contentBytes) &&
      value.contentBytes > 0 &&
      value.contentBytes <= MAX_RESEARCH_BYTES,
  );
  return freeze(value as ResearchManifest);
}
// Python json.dumps(sort_keys=True, separators=(',', ':'), ensure_ascii=True).
// Contract numbers are small schema integers; dollar values always remain strings.
function canonical(value: unknown): string {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value !== null && typeof value === 'object')
    return (
      '{' +
      Object.keys(value)
        .sort()
        .map(
          (key) =>
            canonical(key) +
            ':' +
            canonical((value as Record<string, unknown>)[key]),
        )
        .join(',') +
      '}'
    );
  return JSON.stringify(value).replace(
    /[\u007f-\uffff]/g,
    (character) =>
      '\\u' + character.charCodeAt(0).toString(16).padStart(4, '0'),
  );
}
export function encodeResearchCandidate(input: unknown): Uint8Array {
  return new TextEncoder().encode(canonical(validateResearchCandidate(input)));
}
export async function loadResearchCandidate(
  input: unknown,
  loadBytes: (hash: string) => Uint8Array | Promise<Uint8Array>,
): Promise<ResearchCandidate> {
  const manifest = validateResearchManifest(input);
  requireThat(typeof loadBytes === 'function');
  const pending = loadBytes(manifest.contentHash);
  const received = pending instanceof Uint8Array ? pending : await pending;
  requireThat(
    received instanceof Uint8Array &&
      received.length > 0 &&
      received.length <= MAX_RESEARCH_BYTES,
  );
  const bytes = new Uint8Array(received);
  requireThat(
    bytes.length === manifest.contentBytes,
    'Research byte count mismatch',
  );
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  const hash = Array.from(new Uint8Array(digest), (b) =>
    b.toString(16).padStart(2, '0'),
  ).join('');
  requireThat(hash === manifest.contentHash, 'Research checksum mismatch');
  const value = validateResearchCandidate(
    JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes)),
  );
  const expected = encodeResearchCandidate(value);
  requireThat(
    bytes.length === expected.length &&
      bytes.every((byte, index) => byte === expected[index]),
    'Noncanonical research bytes',
  );
  return value;
}
