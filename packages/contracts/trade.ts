export type Flow = 'imports' | 'exports';
export type Status =
  | 'reported'
  | 'reported_zero'
  | 'suppressed'
  | 'not_available'
  | 'not_applicable'
  | 'not_reported';
export interface Product {
  code: string;
  name: string;
  edition: 'HS2022';
}
export interface Partner {
  id: string;
  name: string;
  code: string;
  kind: 'country' | 'aggregate';
}
export interface Observation {
  product: string;
  partner: string;
  flow: Flow;
  period: string;
  value: string | null;
  status: Status;
}
export interface Release {
  schemaVersion: 1;
  id: string;
  mode: 'sample' | 'official';
  source: 'synthetic' | 'census';
  scope: string;
  officialReleaseDate: string | null;
  officialRevisionDate: string | null;
  ingestedAt: string;
  revisionDetectedAt: string | null;
  basis: 'census-monthly-goods-nsa-usd-v1';
  products: Product[];
  partners: Partner[];
  periods: string[];
  observations: Observation[];
}
export const BASIS = {
  imports: 'General imports · customs value',
  exports: 'Total exports · FAS value',
} as const;
export const ATTRIBUTION =
  'This product uses the Census Bureau Data API but is not endorsed or certified by the Census Bureau.';
const statuses: Status[] = [
  'reported',
  'reported_zero',
  'suppressed',
  'not_available',
  'not_applicable',
  'not_reported',
];
const periodPattern = /^20\d{2}-(0[1-9]|1[0-2])$/;
const integerPattern = /^(0|[1-9]\d{0,23})$/;
function requireThat(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}
function object(value: unknown): asserts value is Record<string, unknown> {
  requireThat(
    value !== null && typeof value === 'object' && !Array.isArray(value),
    'Expected object',
  );
}
function keys(value: Record<string, unknown>, allowed: string[]) {
  requireThat(
    Object.keys(value).length === allowed.length &&
      Object.keys(value).every((k) => allowed.includes(k)),
    'Unexpected or missing field',
  );
}
function text(value: unknown, max = 250): asserts value is string {
  requireThat(
    typeof value === 'string' &&
      value.length > 0 &&
      value.length <= max &&
      !/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(value),
    'Invalid text',
  );
}
function date(value: unknown, timestamp = false) {
  if (value === null) return;
  text(value, 30);
  requireThat(
    (timestamp
      ? /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/
      : /^\d{4}-\d{2}-\d{2}$/
    ).test(value),
    'Invalid date',
  );
  const d = new Date(value);
  requireThat(
    Number.isFinite(d.valueOf()) &&
      d.toISOString().startsWith(value.replace('Z', '')),
    'Invalid date',
  );
}
export function validateRelease(input: unknown): Release {
  object(input);
  keys(input, [
    'schemaVersion',
    'id',
    'mode',
    'source',
    'scope',
    'officialReleaseDate',
    'officialRevisionDate',
    'ingestedAt',
    'revisionDetectedAt',
    'basis',
    'products',
    'partners',
    'periods',
    'observations',
  ]);
  requireThat(
    input.schemaVersion === 1 &&
      input.basis === 'census-monthly-goods-nsa-usd-v1',
    'Unsupported statistical contract',
  );
  text(input.id, 80);
  requireThat(/^[a-z0-9][a-z0-9-]{2,79}$/.test(input.id), 'Invalid release id');
  requireThat(
    (input.mode === 'sample' && input.source === 'synthetic') ||
      (input.mode === 'official' && input.source === 'census'),
    'Source/mode mismatch',
  );
  text(input.scope, 500);
  date(input.officialReleaseDate);
  date(input.officialRevisionDate);
  date(input.ingestedAt, true);
  date(input.revisionDetectedAt, true);
  requireThat(input.ingestedAt !== null, 'Missing ingestion timestamp');
  for (const [name, max] of [
    ['products', 99],
    ['partners', 300],
    ['periods', 72],
    ['observations', 2_000_000],
  ] as const)
    requireThat(
      Array.isArray(input[name]) &&
        input[name].length > 0 &&
        input[name].length <= max,
      `Invalid ${name}`,
    );
  const r = input as unknown as Release;
  const products = new Set<string>(),
    partners = new Set<string>(),
    periods = new Set<string>();
  for (const p of r.products) {
    object(p);
    keys(p, ['code', 'name', 'edition']);
    text(p.name);
    requireThat(
      typeof p.code === 'string' &&
        /^\d{2}$/.test(p.code) &&
        p.edition === 'HS2022' &&
        !products.has(p.code),
      'Invalid or duplicate product',
    );
    products.add(p.code);
  }
  for (const p of r.partners) {
    object(p);
    keys(p, ['id', 'name', 'code', 'kind']);
    text(p.name);
    text(p.code, 8);
    requireThat(
      typeof p.id === 'string' &&
        /^[a-z][a-z0-9-]{0,49}$/.test(p.id) &&
        ['country', 'aggregate'].includes(p.kind) &&
        !partners.has(p.id),
      'Invalid or duplicate partner',
    );
    partners.add(p.id);
  }
  requireThat(
    r.partners.filter((p) => p.kind === 'aggregate').length === 1 &&
      r.partners.some((p) => p.id === 'world' && p.kind === 'aggregate'),
    'World control required',
  );
  for (const p of r.periods) {
    requireThat(
      typeof p === 'string' && periodPattern.test(p) && !periods.has(p),
      'Invalid or duplicate period',
    );
    periods.add(p);
  }
  requireThat(
    r.periods.every((p, i) => i === 0 || p > r.periods[i - 1]),
    'Periods must be ordered',
  );
  const seen = new Set<string>();
  for (const row of r.observations) {
    object(row);
    keys(row, ['product', 'partner', 'flow', 'period', 'value', 'status']);
    requireThat(
      products.has(row.product) &&
        partners.has(row.partner) &&
        periods.has(row.period) &&
        (row.flow === 'imports' || row.flow === 'exports'),
      'Unknown observation relationship',
    );
    requireThat(statuses.includes(row.status), 'Invalid status');
    if (row.status === 'reported' || row.status === 'reported_zero') {
      requireThat(
        typeof row.value === 'string' && integerPattern.test(row.value),
        'Invalid dollar value',
      );
      requireThat(
        (row.value === '0') === (row.status === 'reported_zero'),
        'Value/status contradiction',
      );
    } else requireThat(row.value === null, 'Unavailable values must be null');
    const key = `${row.product}|${row.partner}|${row.flow}|${row.period}`;
    requireThat(!seen.has(key), 'Duplicate observation');
    seen.add(key);
  }
  requireThat(
    seen.size === products.size * partners.size * periods.size * 2,
    'Incomplete coverage: explicit unavailable rows required',
  );
  return r;
}
export function sum(values: (string | null)[]): string | null {
  return !values.length || values.some((v) => v === null)
    ? null
    : values.reduce<bigint>((a, b) => a + BigInt(b!), 0n).toString();
}
export function change(current: string | null, previous: string | null) {
  if (current === null || previous === null)
    return { delta: null, percent: null };
  const a = BigInt(current),
    b = BigInt(previous),
    delta = a - b;
  return {
    delta: delta.toString(),
    // Round the exact ratio once to a tenth of a percentage point, half away from zero.
    percent:
      b === 0n
        ? null
        : ((delta < 0n ? -1 : 1) *
            Number(((delta < 0n ? -delta : delta) * 1000n + b / 2n) / b)) /
          10,
  };
}
export function money(value: string | null, compact = true): string {
  if (value === null) return 'Unavailable';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: compact ? 1 : 0,
  }).format(BigInt(value));
}
export function pct(value: number | null) {
  return value === null
    ? 'Not defined'
    : `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
}
export function chartTick(value: number): string {
  // Axis geometry is approximate; observation tables and downloads remain exact.
  return money(BigInt(Math.round(value)).toString());
}
export function previousYear(period: string) {
  return `${Number(period.slice(0, 4)) - 1}${period.slice(4)}`;
}
export function valueAt(
  r: Release,
  product: string,
  partner: string,
  flow: Flow,
  period: string,
) {
  return (
    r.observations.find(
      (o) =>
        o.product === product &&
        o.partner === partner &&
        o.flow === flow &&
        o.period === period,
    )?.value ?? null
  );
}
export function csvCell(value: string, numeric = false): string {
  if (numeric) {
    requireThat(
      /^-?(0|[1-9]\d{0,23})$/.test(value),
      'Invalid numeric CSV cell',
    );
    return value;
  }
  const safe = /^[\s\u0000-\u001f\u007f]*[=+@-]/.test(value)
    ? `'${value}`
    : value;
  return `"${safe.replaceAll('"', '""')}"`;
}
export function csv(r: Release, rows: Observation[]): string {
  const header = [
    'release',
    'data_mode',
    'product_code',
    'product',
    'partner',
    'flow',
    'period',
    'value_usd',
    'status',
    'statistical_basis',
    'official_release_date',
    'official_revision_date',
    'ingested_at',
  ];
  return (
    '\uFEFF' +
    [
      header.map((v) => csvCell(v)).join(','),
      ...rows.map((o) =>
        [
          r.id,
          r.mode,
          o.product,
          r.products.find((p) => p.code === o.product)!.name,
          r.partners.find((p) => p.id === o.partner)!.name,
          o.flow,
          o.period,
          o.value ?? '',
          o.status,
          `${BASIS[o.flow]}; Census basis; nominal USD; not seasonally adjusted`,
          r.officialReleaseDate ?? 'Unknown',
          r.officialRevisionDate ?? 'Unknown',
          r.ingestedAt,
        ]
          .map((v, i) => csvCell(v, i === 7 && o.value !== null))
          .join(','),
      ),
    ].join('\r\n')
  );
}
export interface Query {
  flow: Flow;
  period: string;
  product: string;
  partners: string[];
  release: string;
  error: string | null;
}
export function parseQuery(params: URLSearchParams, r: Release): Query {
  const result: Query = {
    flow: 'imports',
    period: r.periods.at(-1)!,
    product: r.products[0].code,
    partners: [],
    release: r.id,
    error: null,
  };
  const allowed = ['flow', 'period', 'product', 'partners', 'release'];
  if (
    [...params.keys()].some(
      (k) => !allowed.includes(k) || params.getAll(k).length !== 1,
    ) ||
    params.toString().length > 1000
  )
    result.error =
      'This link contains unsupported or repeated filters. Reset the filters to continue.';
  const flow = params.get('flow'),
    period = params.get('period'),
    product = params.get('product'),
    release = params.get('release');
  if (
    ['flow', 'period', 'product', 'release'].some(
      (key) => params.has(key) && !params.get(key),
    )
  )
    result.error =
      'This link contains an empty required filter. Reset the filters to continue.';
  if (flow) {
    if (flow === 'imports' || flow === 'exports') result.flow = flow;
    else result.error = 'Choose imports or exports.';
  }
  if (period) {
    if (r.periods.includes(period)) result.period = period;
    else result.error = 'This period is not included in this release.';
  }
  if (product) {
    if (product === 'all' || r.products.some((p) => p.code === product))
      result.product = product;
    else result.error = 'This product is not included in this release.';
  }
  if (release && release !== r.id)
    result.error =
      'This link refers to a different release. Open its release record or reset to the available release.';
  const partners = params.get('partners')?.split(',').filter(Boolean) ?? [];
  if (
    partners.length > 3 ||
    new Set(partners).size !== partners.length ||
    partners.some(
      (id) => !r.partners.some((p) => p.id === id && p.kind === 'country'),
    )
  )
    result.error = 'Choose up to three available countries.';
  else result.partners = partners;
  return result;
}
export function queryString(q: Query): string {
  return new URLSearchParams({
    flow: q.flow,
    period: q.period,
    product: q.product,
    partners: q.partners.join(','),
    release: q.release,
  }).toString();
}
