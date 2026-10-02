import { test } from 'node:test';
import assert from 'node:assert/strict';
import { searchProducts } from '../src/lib/product-search.ts';

const chapters = [
  { code: '09', name: 'Coffee, tea & spices' },
  { code: '84', name: 'Machinery & mechanical appliances' },
  { code: '85', name: 'Electrical machinery & equipment' },
  { code: '87', name: 'Vehicles & transport equipment' },
];

test('chapter lookup accepts a case-insensitive HS prefix and preserves code zero', () => {
  for (const term of ['09', 'HS09', 'hs 09', '  HS 09  ']) {
    const result = searchProducts(term, chapters);
    assert.equal(result.kind, 'chapter', term);
    assert.deepEqual(
      result.matches.map((p) => p.code),
      ['09'],
      term,
    );
  }
  assert.equal(searchProducts('HS 09', chapters).term, 'HS 09');
});

test('detailed codes offer an available parent without calling it a matching product', () => {
  for (const term of [
    '0901',
    '090111',
    '09011100',
    '0901110000',
    'hs090111',
    'HS 090111',
  ]) {
    const result = searchProducts(term, chapters);
    assert.equal(result.kind, 'detail', term);
    assert.deepEqual(result.matches, [], term);
    assert.equal(result.parent?.code, '09', term);
    assert.equal(result.parentCode, '09', term);
    assert.equal(result.term, term);
  }
});

test('a detailed code with an absent parent does not invent chapter coverage', () => {
  const result = searchProducts('990111', chapters);
  assert.equal(result.kind, 'detail');
  assert.equal(result.parentCode, '99');
  assert.equal(result.parent, undefined);
  assert.deepEqual(result.matches, []);
});

test('ambiguous names include every case-insensitive name match', () => {
  const result = searchProducts('MaCHiNeRY', chapters);
  assert.equal(result.kind, 'name');
  assert.deepEqual(
    result.matches.map((p) => p.code),
    ['84', '85'],
  );
});

test('empty terms expose the supplied directory rather than a fixed chapter count', () => {
  const result = searchProducts('  ', chapters.slice(0, 2));
  assert.equal(result.kind, 'all');
  assert.equal(result.term, '');
  assert.deepEqual(
    result.matches.map((p) => p.code),
    ['09', '84'],
  );
});

test('unsupported numeric lengths and mixed codes cannot substring-match chapters', () => {
  for (const term of [
    '0',
    '9',
    '8',
    '009',
    '090',
    '09011',
    '0901111',
    '090111000',
    '09011100000',
    'HS09coffee',
    '09-01',
    '090111x',
    'HS 09 01',
    '84 machinery',
  ]) {
    const result = searchProducts(term, chapters);
    assert.equal(result.kind, 'invalid', term);
    assert.deepEqual(result.matches, [], term);
    assert.equal(result.parent, undefined, term);
  }
  assert.deepEqual(searchProducts('00', chapters).matches, []);
});

test('terms are bounded before matching while their display case is retained', () => {
  const result = searchProducts('x'.repeat(120) + ' machinery', chapters);
  assert.equal(result.term, 'x'.repeat(120));
  assert.deepEqual(result.matches, []);
  assert.equal(searchProducts('  COFFEE  ', chapters).term, 'COFFEE');
  assert.deepEqual(
    searchProducts('  COFFEE  ', chapters).matches.map((p) => p.code),
    ['09'],
  );
});

test('hostile text remains a literal term without creating a match or a parent', () => {
  const term = '<img src=x onerror="alert(1)">';
  const result = searchProducts(term, chapters);
  assert.equal(result.term, term);
  assert.deepEqual(result.matches, []);
  assert.equal(result.parent, undefined);
});
