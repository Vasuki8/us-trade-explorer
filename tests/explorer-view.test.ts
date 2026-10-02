import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  change,
  csv,
  type Query,
  type Release,
  type Observation,
} from '../packages/contracts/trade.ts';
import { explorerView } from '../src/lib/explorer-view.ts';

const sample = () =>
  JSON.parse(
    readFileSync(
      new URL('./fixtures/sample-release.json', import.meta.url),
      'utf8',
    ),
  ) as Release;
const query = (overrides: Partial<Query> = {}): Query => ({
  product: 'all',
  partners: ['canada'],
  flow: 'imports',
  period: '2026-07',
  release: 'sample-2026-07-v1',
  error: null,
  ...overrides,
});

test('country view sums the pinned chapters with an independently known prior-year total', () => {
  const r = sample();
  const view = explorerView(r, query());
  assert.equal(view.rows.length, 1);
  assert.equal(view.rows[0].partner, 'canada');
  assert.equal(view.rows[0].value, '20742720000');
  assert.equal(view.rows[0].previous, '18735360000');
  assert.deepEqual(change(view.rows[0].value, view.rows[0].previous), {
    delta: '2007360000',
    percent: 10.7,
  });
  assert.match(view.rows[0].statusLabel, /calculated/i);
});

test('export comparison uses the same chapter set and never substitutes a partial India baseline', () => {
  const view = explorerView(
    sample(),
    query({ flow: 'exports', partners: ['canada', 'india'] }),
  );
  assert.deepEqual(
    view.rows.map(({ partner, value, previous }) => ({
      partner,
      value,
      previous,
    })),
    [
      { partner: 'canada', value: '6222816000', previous: '5620608000' },
      { partner: 'india', value: '6229507200', previous: null },
    ],
  );
  assert.deepEqual(change(view.rows[1].value, view.rows[1].previous), {
    delta: null,
    percent: null,
  });
});

test('CSV receives only unchanged selected-month authentic detail observations', () => {
  const r = sample();
  const view = explorerView(
    r,
    query({ flow: 'exports', partners: ['canada', 'india'] }),
  );
  const expected = r.observations.filter(
    (row) =>
      row.period === '2026-07' &&
      row.flow === 'exports' &&
      ['canada', 'india'].includes(row.partner),
  );
  assert.equal(view.observations.length, 8);
  assert.deepEqual(view.observations, expected);
  assert.ok(view.observations.every((row) => r.observations.includes(row)));
  const output = csv(r, view.observations);
  assert.equal(output, csv(r, expected));
  assert.equal(output.trim().split('\r\n').length, 9);
  assert.ok(!output.includes('"all"'));
  assert.ok(!output.includes('"2025-07"'));
});

// A tiny independent release makes precision and coverage boundaries observable.
function smallRelease(
  current: (string | null)[],
  prior: (string | null)[],
): Release {
  const r = sample();
  r.products = r.products.slice(0, 2);
  r.partners = r.partners.filter((p) =>
    ['world', 'canada', 'india'].includes(p.id),
  );
  r.periods = ['2025-07', '2026-07'];
  r.observations = [];
  for (const [period, values] of [
    ['2026-07', current],
    ['2025-07', prior],
  ] as const) {
    values.forEach((value, index) =>
      r.observations.push({
        product: r.products[index].code,
        partner: 'canada',
        flow: 'imports',
        period,
        value,
        status:
          value === null
            ? 'suppressed'
            : value === '0'
              ? 'reported_zero'
              : 'reported',
      }),
    );
  }
  return r;
}

test('included chapter totals retain integers beyond Number precision', () => {
  const view = explorerView(
    smallRelease(['999999999999999999999999', '2'], ['9007199254740993', '2']),
    query(),
  );
  assert.equal(view.rows[0].value, '1000000000000000000000001');
  assert.equal(view.rows[0].previous, '9007199254740995');
});

for (const { name, current, prior, value, previous, delta, percent } of [
  {
    name: 'all reported zeros',
    current: ['0', '0'],
    prior: ['4', '6'],
    value: '0',
    previous: '10',
    delta: '-10',
    percent: -100,
  },
  {
    name: 'zero prior baseline',
    current: ['4', '6'],
    prior: ['0', '0'],
    value: '10',
    previous: '0',
    delta: '10',
    percent: null,
  },
  {
    name: 'unavailable current chapter',
    current: ['4', null],
    prior: ['4', '6'],
    value: null,
    previous: '10',
    delta: null,
    percent: null,
  },
  {
    name: 'unavailable prior chapter',
    current: ['4', '6'],
    prior: [null, '6'],
    value: '10',
    previous: null,
    delta: null,
    percent: null,
  },
] as const) {
  test(`${name} never becomes a partial sum or a fabricated percentage`, () => {
    const r = smallRelease([...current], [...prior]);
    const view = explorerView(r, query());
    assert.equal(view.rows[0].value, value);
    assert.equal(view.rows[0].previous, previous);
    assert.deepEqual(change(view.rows[0].value, view.rows[0].previous), {
      delta,
      percent,
    });
    assert.deepEqual(
      view.observations.map((o) => o.value),
      current,
    );
    if (value === null) assert.match(view.rows[0].statusLabel, /unavailable/i);
    assert.ok(
      !['reported', 'reported_zero', 'suppressed'].includes(
        view.rows[0].statusLabel,
      ),
    );
  });
}

for (const period of ['2026-07', '2025-07']) {
  test(`a missing ${period} chapter makes only its corresponding total unavailable`, () => {
    const r = smallRelease(['4', '6'], ['4', '6']);
    r.observations = r.observations.filter(
      (o) => !(o.product === '84' && o.period === period),
    );
    const row = explorerView(r, query()).rows[0];
    assert.equal(row.value, period === '2026-07' ? null : '10');
    assert.equal(row.previous, period === '2025-07' ? null : '10');
  });
}

test('declared chapters, country partners, month and flow bound the display and CSV scope', () => {
  const r = smallRelease(['4', '6'], ['2', '3']);
  const extra: Observation[] = [
    {
      product: '99',
      partner: 'canada',
      flow: 'imports',
      period: '2026-07',
      value: '1000',
      status: 'reported',
    },
    {
      product: '09',
      partner: 'world',
      flow: 'imports',
      period: '2026-07',
      value: '1000',
      status: 'reported',
    },
    {
      product: '84',
      partner: 'world',
      flow: 'imports',
      period: '2026-07',
      value: '1000',
      status: 'reported',
    },
    {
      product: '09',
      partner: 'india',
      flow: 'imports',
      period: '2026-07',
      value: '7',
      status: 'reported',
    },
    {
      product: '84',
      partner: 'india',
      flow: 'imports',
      period: '2026-07',
      value: '8',
      status: 'reported',
    },
    {
      product: '09',
      partner: 'canada',
      flow: 'exports',
      period: '2026-07',
      value: '9',
      status: 'reported',
    },
    {
      product: '84',
      partner: 'canada',
      flow: 'exports',
      period: '2026-07',
      value: '11',
      status: 'reported',
    },
  ];
  r.observations.push(...extra);
  const selected = explorerView(r, query());
  assert.equal(selected.rows[0].value, '10');
  assert.equal(selected.observations.length, 2);
  const allCountries = explorerView(r, query({ partners: [] }));
  assert.deepEqual(
    allCountries.rows.map((row) => [row.partner, row.value]),
    [
      ['canada', '10'],
      ['india', '15'],
    ],
  );
  assert.equal(allCountries.observations.length, 4);
  assert.ok(
    allCountries.observations.every(
      (o) => o.partner !== 'world' && o.product !== '99',
    ),
  );
  assert.equal(
    explorerView(r, query({ period: '2025-07' })).rows[0].value,
    '5',
  );
  assert.equal(explorerView(r, query({ flow: 'exports' })).rows[0].value, '20');
});

test('a chapter view preserves detail value status and uses its matching prior-year observation', () => {
  const r = smallRelease(['0', '6'], ['4', '6']);
  const view = explorerView(r, query({ product: '09' }));
  assert.equal(view.rows.length, 1);
  assert.equal(view.rows[0].value, '0');
  assert.equal(view.rows[0].previous, '4');
  assert.equal(view.rows[0].statusLabel, 'reported zero');
  assert.deepEqual(view.observations, [r.observations[0]]);
});
