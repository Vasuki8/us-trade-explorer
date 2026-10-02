import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  validateRelease,
  change,
  sum,
  csvCell,
  parseQuery,
  queryString,
  pct,
  chartTick,
  type Release,
} from '../packages/contracts/trade.ts';

const sample = () =>
  JSON.parse(
    readFileSync(
      new URL('./fixtures/sample-release.json', import.meta.url),
      'utf8',
    ),
  ) as Release;
test('percentages round the exact ratio once', () => {
  assert.equal(pct(change('101151', '100000').percent), '+1.2%');
  assert.equal(pct(change('98849', '100000').percent), '-1.2%');
});
test('large chart ticks remain formattable within the release contract range', () => {
  assert.doesNotThrow(() => chartTick(1.18e21));
});
test('rejects duplicate rows instead of doubling a trade total', () => {
  const r = sample();
  r.observations.push(r.observations[0]);
  assert.throws(() => validateRelease(r), /duplicate/i);
});
test('rejects a missing coverage slot instead of calling it zero', () => {
  const r = sample();
  r.observations.pop();
  assert.throws(() => validateRelease(r), /coverage/i);
});
test('rejects nonnumeric dollars, negative gross value, bad periods and private fields', () => {
  for (const value of ['NaN', '1.5', '-1', '9007199254740993e3']) {
    const r = sample();
    r.observations[0].value = value;
    assert.throws(() => validateRelease(r));
  }
  const r = sample();
  r.periods[0] = '2026-13';
  assert.throws(() => validateRelease(r));
  assert.throws(
    () => validateRelease({ ...sample(), workspace: { notes: 'private' } }),
    /field/i,
  );
});
test('rejects status/value contradictions and unknown product relationships', () => {
  const r = sample();
  r.observations[0].status = 'suppressed';
  assert.throws(() => validateRelease(r));
  const s = sample();
  s.observations[0].product = '99';
  assert.throws(() => validateRelease(s));
});
test('calculates exact dollar differences above Number precision and refuses zero baseline percentage', () => {
  assert.deepEqual(change('9007199254740995', '9007199254740993'), {
    delta: '2',
    percent: 0,
  });
  assert.deepEqual(change('120', '100'), { delta: '20', percent: 20 });
  assert.deepEqual(change('50', '0'), { delta: '50', percent: null });
  assert.deepEqual(change(null, '10'), { delta: null, percent: null });
  assert.equal(sum(['9007199254740993', '2']), '9007199254740995');
  assert.equal(sum(['10', null]), null);
  assert.equal(sum([]), null);
});
test('CSV neutralizes formulas after whitespace and controls while preserving numeric cells', () => {
  assert.equal(csvCell(' \t=HYPERLINK("bad")'), '"\' \t=HYPERLINK(""bad"")"');
  assert.equal(csvCell('\r\n+1'), '"\'\r\n+1"');
  assert.equal(csvCell('-42', true), '-42');
  assert.throws(() => csvCell('=1', true));
  assert.equal(csvCell('coffee,"tea"'), '"coffee,""tea"""');
});
test('valid share URLs round-trip and invalid filters cannot silently select misleading data', () => {
  const r = sample();
  const q = parseQuery(
    new URLSearchParams(
      'flow=exports&period=2026-07&product=09&partners=india,china',
    ),
    r,
  );
  assert.equal(q.error, null);
  assert.deepEqual(q.partners, ['india', 'china']);
  const again = parseQuery(new URLSearchParams(queryString(q)), r);
  assert.deepEqual(again, q);
  for (const raw of [
    'flow=',
    'period=',
    'product=',
    'release=',
    'flow=evil',
    'period=2026-13',
    'product=9999',
    'partners=unknown',
    'flow=imports&flow=exports',
    'release=wrong',
  ]) {
    assert.ok(parseQuery(new URLSearchParams(raw), r).error, raw);
  }
});

test('included-chapter query scope round-trips without changing the omitted chapter default', () => {
  const r = sample();
  const q = parseQuery(new URLSearchParams('product=all&partners=canada'), r);
  assert.equal(q.error, null);
  assert.equal(q.product, 'all');
  assert.deepEqual(parseQuery(new URLSearchParams(queryString(q)), r), q);
  assert.equal(parseQuery(new URLSearchParams(), r).product, '09');
  for (const product of [
    'ALL',
    'All',
    'all-goods',
    'world',
    'all,09',
    ' all',
  ]) {
    assert.ok(parseQuery(new URLSearchParams({ product }), r).error, product);
  }
  assert.ok(parseQuery(new URLSearchParams('product=all&product=09'), r).error);
});
