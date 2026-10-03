import { test } from 'node:test';
import assert from 'node:assert/strict';
import { changeView } from '../src/lib/change-view.ts';

const observation = { priorYearIncluded: true, scope: 'observation' } as const;
const chapters = {
  priorYearIncluded: true,
  scope: 'included-chapters',
} as const;

for (const { name, current, previous, options, reason } of [
  {
    name: 'current null',
    current: null,
    previous: '10',
    options: observation,
    reason: 'Current value unavailable',
  },
  {
    name: 'prior null',
    current: '10',
    previous: null,
    options: observation,
    reason: 'Prior-year value unavailable',
  },
  {
    name: 'both null prioritizes current',
    current: null,
    previous: null,
    options: observation,
    reason: 'Current value unavailable',
  },
  {
    name: 'absent prior month precedes prior null',
    current: '10',
    previous: null,
    options: { ...observation, priorYearIncluded: false },
    reason: 'Prior-year month is not included in this release',
  },
  {
    name: 'current null precedes absent month',
    current: null,
    previous: null,
    options: { ...observation, priorYearIncluded: false },
    reason: 'Current value unavailable',
  },
  {
    name: 'current chapter coverage',
    current: null,
    previous: '10',
    options: chapters,
    reason: 'Current value unavailable for one or more included chapters',
  },
  {
    name: 'prior chapter coverage',
    current: '10',
    previous: null,
    options: chapters,
    reason: 'Prior-year value unavailable for one or more included chapters',
  },
  {
    name: 'both chapter sums unavailable prioritizes current coverage',
    current: null,
    previous: null,
    options: chapters,
    reason: 'Current value unavailable for one or more included chapters',
  },
] as const) {
  test(`${name} explains an undefined comparison without inventing an observation status`, () => {
    assert.deepEqual(changeView(current, previous, options), {
      delta: null,
      percent: null,
      reason,
    });
  });
}

for (const { current, previous, delta, percent, reason } of [
  {
    current: '10',
    previous: '0',
    delta: '10',
    percent: null,
    reason: 'Percentage undefined from zero baseline',
  },
  {
    current: '0',
    previous: '0',
    delta: '0',
    percent: null,
    reason: 'Percentage undefined from zero baseline',
  },
  { current: '0', previous: '10', delta: '-10', percent: -100, reason: null },
  {
    current: '900719925474099312345679',
    previous: '900719925474099312345678',
    delta: '1',
    percent: 0,
    reason: null,
  },
  {
    current: '900719925474099312345678',
    previous: '450359962737049656172839',
    delta: '450359962737049656172839',
    percent: 100,
    reason: null,
  },
  { current: '10001', previous: '10000', delta: '1', percent: 0, reason: null },
  { current: '105', previous: '100', delta: '5', percent: 5, reason: null },
] as const) {
  test(`comparison ${current} / ${previous} preserves exact arithmetic and defined rounded zero`, () => {
    assert.deepEqual(changeView(current, previous, observation), {
      delta,
      percent,
      reason,
    });
  });
}

test('a missing prior month inside noncontiguous release periods remains absent, without mutating options', () => {
  const periods = Object.freeze(['2024-07', '2025-06', '2025-08', '2026-07']);
  const options = Object.freeze({
    priorYearIncluded: periods.includes('2025-07'),
    scope: 'included-chapters' as const,
  });
  assert.deepEqual(changeView('10', null, options), {
    delta: null,
    percent: null,
    reason: 'Prior-year month is not included in this release',
  });
  assert.deepEqual(options, {
    priorYearIncluded: false,
    scope: 'included-chapters',
  });
  assert.deepEqual(periods, ['2024-07', '2025-06', '2025-08', '2026-07']);
});
