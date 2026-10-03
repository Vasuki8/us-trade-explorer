import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import {
  validateResearchCandidate,
  type ResearchCandidate,
} from '../packages/contracts/research-candidate.ts';
import { createReviewDownload } from '../tools/research-review/download.ts';

const fixture = JSON.parse(
  readFileSync(
    new URL('./fixtures/research-candidate.example.json', import.meta.url),
    'utf8',
  ),
).bundle.data;
const data = () => validateResearchCandidate(structuredClone(fixture));

// Read the exported format independently, including quoted embedded newlines.
function records(csv: string): Record<string, string>[] {
  assert.equal(csv[0], '\uFEFF');
  const rows: string[][] = [];
  let row: string[] = [],
    cell = '',
    quoted = false;
  for (let index = 1; index < csv.length; index++) {
    const character = csv[index];
    if (character === '"') {
      if (quoted && csv[index + 1] === '"') {
        cell += '"';
        index++;
      } else quoted = !quoted;
    } else if (character === ',' && !quoted) {
      row.push(cell);
      cell = '';
    } else if (character === '\r' && csv[index + 1] === '\n' && !quoted) {
      row.push(cell);
      rows.push(row);
      row = [];
      cell = '';
      index++;
    } else cell += character;
  }
  assert.equal(quoted, false, 'CSV has no unterminated quoted fields');
  if (cell !== '' || row.length) {
    row.push(cell);
    rows.push(row);
  }
  const header = rows.shift()!;
  assert.equal(new Set(header).size, header.length);
  return rows.map((values) => {
    assert.equal(values.length, header.length);
    return Object.fromEntries(
      header.map((name, index) => [name, values[index]]),
    );
  });
}

test('chapter CSV exports only the chosen flow with the world, four countries and complete subtotal', () => {
  for (const flow of ['imports', 'exports'] as const) {
    const result = createReviewDownload(data(), flow, null, 'candidate');
    const rows = records(result.csv);
    assert.equal(
      result.filename,
      `ust-chapter09-${flow}-2026-07-unpublished.csv`,
    );
    assert.deepEqual(
      rows.map((row) => row.row_kind),
      [
        'world',
        'country',
        'country',
        'country',
        'country',
        'selected_subtotal',
      ],
    );
    assert.deepEqual(
      rows.map((row) => row.value_nominal_usd),
      ['100', '10', '20', '0', '30', '60'],
    );
    assert.deepEqual(
      rows
        .filter((row) => row.row_kind === 'country')
        .map((row) => row.partner_code),
      ['1220', '2010', '5330', '5700'],
    );
    assert.equal(rows[5].share_of_world_percent, '60.00');
    for (const row of rows) {
      assert.equal(row.flow, flow);
      assert.equal(
        row.statistical_basis,
        flow === 'imports'
          ? 'general-imports'
          : 'total-exports-domestic-plus-reexports',
      );
      assert.equal(
        row.valuation,
        flow === 'imports' ? 'customs-value' : 'FAS-value',
      );
      assert.equal(
        row.source_measure,
        flow === 'imports' ? 'GEN_VAL_MO' : 'ALL_VAL_MO',
      );
    }
    assert.equal(rows[0].share_of_world_percent, '');
    assert.equal(
      rows[0].share_unavailable_reason,
      'not-applicable-world-control',
    );
  }
});

test('each detached row retains definitions, selected/global coverage, provenance and explicit unknown dates', () => {
  const rows = records(
    createReviewDownload(data(), 'imports', null, 'candidate').csv,
  );
  for (const row of rows) {
    for (const [field, expected] of Object.entries({
      reporter: 'US',
      product_code: '09',
      product: 'Coffee, tea, maté and spices',
      product_level: 'HS2',
      reporting_period: '2026-07',
      period_kind: 'month',
      unit: 'USD',
      price_basis: 'nominal',
      seasonal_adjustment: 'not-seasonally-adjusted',
      commodity_classification: 'HTS',
      classification_system: 'HTSUS',
      selected_scope: 'selected-four-country-subset',
      all_selected_observed: 'true',
      missing_selected_codes: '',
      global_coverage_complete: 'false',
      source_agency: 'US Census Bureau',
      source_url: 'https://api.census.gov/data/timeseries/intltrade/imports/hs',
      methodology_url: 'https://www.census.gov/foreign-trade/guide/sec2.html',
      retrieved_at: '2026-10-02T01:02:03Z',
      official_release_date: '',
      official_release_date_state: 'unknown',
      official_revision_date: '',
      official_revision_date_state: 'unknown',
      revision_detected_at: '',
      revision_detected_at_state: 'unknown',
      published_at: '',
      publication_state: 'unpublished-review',
      data_mode: 'candidate',
      api_classification_vintage: 'not-identified',
      provision_effective_from: '',
      provision_effective_from_state: 'unknown',
      historical_comparability: 'not-established',
      historical_growth: 'not-supported',
      fine_code_joins: 'not-supported',
      quantity_metrics: 'not-supported',
      global_rankings_and_concentration: 'not-supported',
      geography_system: 'Schedule C',
      geography_claim: 'selected-schedule-c-designations-only',
      designation_effective_from: '',
      designation_effective_from_state: 'unknown',
    }))
      assert.equal(row[field], expected, field);
    assert.match(row.data_notice, /publication not approved/i);
    assert.match(row.scope_note, /chapter 09 only/i);
    assert.match(row.share_methodology, /same-flow world chapter value/i);
    assert.match(row.share_methodology, /half-up/i);
    for (const revision of [11, 12, 13, 14]) {
      assert.ok(
        row.classification_reference_urls.includes(
          `https://hts.usitc.gov/reststop/file?release=2026HTSRev${revision}&filename=Chapter%209`,
        ),
      );
      assert.ok(
        row.geography_reference_urls.includes(
          `https://hts.usitc.gov/reststop/file?release=2026HTSRev${revision}&filename=Statistical%20Annexes`,
        ),
      );
    }
  }
  assert.equal(
    rows[2].geographic_note,
    'Includes Isla de Cozumel and Islas Revillagigedo.',
  );
  assert.equal(
    rows[4].geographic_note,
    'Hong Kong, Macao and Taiwan have separate Schedule C designations.',
  );
});

test('country CSV includes only the selected country and its world denominator without unrelated amounts', () => {
  const candidate = data();
  const expected = [
    ['1220', 'Canada', '10'],
    ['2010', 'Mexico', '20'],
    ['5330', 'India', '0'],
    ['5700', 'China', '30'],
  ];
  for (let index = 0; index < expected.length; index++) {
    const [code, name, value] = expected[index];
    const result = createReviewDownload(candidate, 'exports', index, 'fixture');
    assert.equal(
      result.filename,
      `ust-country${code}-chapter09-exports-2026-07-fixture.csv`,
    );
    const rows = records(result.csv);
    assert.deepEqual(
      rows.map((row) => row.row_kind),
      ['world', 'country'],
    );
    assert.equal(rows[0].value_nominal_usd, '100');
    assert.equal(rows[1].partner_code, code);
    assert.equal(rows[1].partner, name);
    assert.equal(rows[1].value_nominal_usd, value);
    for (const row of rows) {
      assert.equal(row.data_mode, 'fixture');
      assert.match(row.data_notice, /fabricated/i);
      assert.match(row.data_notice, /invented/i);
      assert.match(row.scope_note, /not total US trade with this country/i);
      assert.equal(row.classification_system, 'Schedule B');
      assert.ok(
        row.classification_reference_urls.includes(
          'https://www.census.gov/foreign-trade/schedules/b/2026/c09.pdf',
        ),
      );
    }
    assert.ok(rows.every((row) => row.value_nominal_usd !== '60'));
    assert.doesNotMatch(result.csv, /GEN_VAL_MO|general-imports|customs-value/);
  }
});

test('unobserved countries remain blank while zero remains numeric and partial sums are explicitly incomplete', () => {
  const raw = structuredClone(fixture),
    flow = raw.flows[0];
  Object.assign(flow.countries[0], {
    status: 'unobserved',
    value: null,
    shareOfWorldPercent: null,
    shareUnavailableReason: 'partner-not-observed',
  });
  Object.assign(flow.totals, {
    observedSelectedUSD: '50',
    selectedTotalUSD: null,
    selectedShareOfWorldPercent: null,
  });
  Object.assign(flow.coverage, {
    allSelectedObserved: false,
    missingSelectedCodes: ['1220'],
  });
  const candidate = validateResearchCandidate(raw);
  const rows = records(
    createReviewDownload(candidate, 'imports', null, 'fixture').csv,
  );
  assert.equal(rows[1].value_nominal_usd, '');
  assert.equal(rows[1].observation_status, 'unobserved');
  assert.equal(rows[1].share_of_world_percent, '');
  assert.equal(rows[1].share_unavailable_reason, 'partner-not-observed');
  assert.equal(rows[3].value_nominal_usd, '0');
  assert.equal(rows[3].observation_status, 'reported_zero');
  assert.equal(rows[3].share_of_world_percent, '0.00');
  assert.ok(rows.every((row) => row.row_kind !== 'selected_subtotal'));
  assert.equal(rows[5].row_kind, 'observed_selected_partial');
  assert.equal(rows[5].value_nominal_usd, '50');
  assert.equal(rows[5].observation_status, 'calculated_partial_sum');
  assert.equal(rows[5].share_of_world_percent, '');
  assert.equal(
    rows[5].share_unavailable_reason,
    'incomplete-selected-coverage',
  );
  assert.match(rows[5].observation_note, /excludes unobserved countries/i);
  for (const row of rows) {
    assert.equal(row.all_selected_observed, 'false');
    assert.equal(row.missing_selected_codes, '1220');
  }
  const countryRows = records(
    createReviewDownload(candidate, 'imports', 0, 'fixture').csv,
  );
  assert.equal(countryRows.length, 2);
  assert.equal(countryRows[1].observation_status, 'unobserved');
  assert.ok(countryRows.every((row) => row.value_nominal_usd !== '50'));
});

test('unknown and zero world denominators keep distinct unavailable reasons and observation states', () => {
  for (const zero of [false, true]) {
    const raw = structuredClone(fixture),
      flow = raw.flows[1];
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
    const rows = records(
      createReviewDownload(
        validateResearchCandidate(raw),
        'exports',
        null,
        'candidate',
      ).csv,
    );
    assert.equal(rows[0].value_nominal_usd, zero ? '0' : '');
    assert.equal(
      rows[0].observation_status,
      zero ? 'reported_zero' : 'unobserved',
    );
    for (const row of rows.slice(1)) {
      assert.equal(row.share_of_world_percent, '');
      assert.equal(
        row.share_unavailable_reason,
        zero ? 'zero-world-denominator' : 'world-not-observed',
      );
      assert.equal(
        row.world_denominator_status,
        zero ? 'reported_zero' : 'unobserved',
      );
    }
    assert.equal(
      rows[5].observation_status,
      zero ? 'calculated_zero_subtotal' : 'calculated_subtotal',
    );
  }
});

test('nominal dollar observations retain exact 24-digit integers without floating point rounding or text prefixes', () => {
  const raw = structuredClone(fixture),
    flow = raw.flows[0];
  flow.world.value = '200000000000000000000000';
  flow.countries.forEach((row: Record<string, unknown>, index: number) =>
    Object.assign(row, {
      value: index ? '0' : '1010000000000000000000',
      status: index ? 'reported_zero' : 'reported',
      shareOfWorldPercent: index ? '0.00' : '0.51',
    }),
  );
  Object.assign(flow.totals, {
    observedSelectedUSD: '1010000000000000000000',
    selectedTotalUSD: '1010000000000000000000',
    selectedShareOfWorldPercent: '0.51',
  });
  const result = createReviewDownload(
    validateResearchCandidate(raw),
    'imports',
    null,
    'fixture',
  );
  const rows = records(result.csv);
  assert.equal(rows[0].value_nominal_usd, '200000000000000000000000');
  assert.equal(rows[1].value_nominal_usd, '1010000000000000000000');
  assert.equal(rows[5].value_nominal_usd, '1010000000000000000000');
  assert.match(result.csv, /,200000000000000000000000,/);
  assert.match(result.csv, /,1010000000000000000000,/);
  assert.doesNotMatch(result.csv, /'101000|2e\+23|1\.01e\+21/);
});

test('external text is CSV-escaped and formula-neutralized after whitespace or controls without changing numeric observations', () => {
  // The loader already validates all names/URLs. Exercise the encoder boundary
  // with hostile external text directly so it remains safe if that schema expands.
  for (const text of [
    '=1+1',
    ' \t+SUM(1,2)',
    '\r\n-42',
    '\u0000\u001f@HYPERLINK("bad")',
    '\u007f=1',
    '\u00a0\t=1',
  ]) {
    const raw = structuredClone(fixture) as ResearchCandidate;
    raw.scope.product.name = text;
    raw.flows[0].countries[0].geographicNote = 'coffee,"tea"\r\nspices';
    const result = createReviewDownload(raw, 'imports', 0, 'fixture');
    const rows = records(result.csv);
    assert.equal(rows[0].product, `'${text}`);
    assert.equal(rows[1].product, `'${text}`);
    assert.equal(rows[1].geographic_note, 'coffee,"tea"\r\nspices');
    assert.equal(rows[1].value_nominal_usd, '10');
    assert.match(result.csv, /,10,/);
    assert.match(result.csv, /"coffee,""tea""\r\nspices"/);
    assert.equal(
      result.filename,
      'ust-country1220-chapter09-imports-2026-07-fixture.csv',
    );
  }
});

test('download selectors reject invalid runtime values before constructing a filename', () => {
  const candidate = data();
  for (const index of [-1, 4, 0.5, NaN, Infinity, '0', undefined]) {
    assert.throws(() =>
      createReviewDownload(candidate, 'imports', index as number, 'fixture'),
    );
  }
  assert.throws(() =>
    createReviewDownload(candidate, '../secret' as 'imports', null, 'fixture'),
  );
  assert.throws(() =>
    createReviewDownload(candidate, 'imports', null, '../secret' as 'fixture'),
  );
});

test('exporting frozen candidates is deterministic and does not alter the source snapshot', () => {
  const candidate = data(),
    before = JSON.stringify(candidate);
  assert.ok(Object.isFrozen(candidate.flows[0].countries));
  const first = createReviewDownload(candidate, 'imports', null, 'candidate');
  assert.deepEqual(
    createReviewDownload(candidate, 'imports', null, 'candidate'),
    first,
  );
  assert.equal(JSON.stringify(candidate), before);
});
