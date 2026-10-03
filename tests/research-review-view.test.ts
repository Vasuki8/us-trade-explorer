import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { validateResearchCandidate } from '../packages/contracts/research-candidate.ts';
import { renderReview, escapeHTML } from '../tools/research-review/view.ts';

const fixture = JSON.parse(
  readFileSync(
    new URL('./fixtures/research-candidate.example.json', import.meta.url),
    'utf8',
  ),
).bundle.data;
const data = () => validateResearchCandidate(structuredClone(fixture));

test('product direct entry includes subject, basis, world and selected scope, source and next actions', () => {
  const result = renderReview(data(), '/products/09?flow=imports', 'fixture');
  assert.equal(result.status, 200);
  for (const text of [
    'Coffee, tea, maté and spices',
    'July 2026',
    'General imports',
    'Customs value',
    'Monthly',
    'USD',
    'Not seasonally adjusted',
    'World chapter value',
    '$100',
    'Four-country subtotal',
    '$60',
    'Four selected countries',
    '10.00%',
    'Sources and methodology',
    'Fabricated test data',
    'Unpublished local review',
  ])
    assert.ok(result.html.includes(text), text);
  assert.match(result.html, /\/countries\/canada\?flow=imports/);
  assert.doesNotMatch(result.html, /<script|https:\/\/[^" ]+\.(?:js|css|woff)/);
});

test('country direct entry qualifies the chapter and links back with the selected flow', () => {
  const result = renderReview(
    data(),
    '/countries/india?flow=exports',
    'candidate',
  );
  for (const text of [
    'US trade with India',
    'Chapter 09',
    'Total exports',
    'FAS value',
    'US exports to India',
    '$0',
    'Reported zero',
    '0.00%',
    'not total US trade with this country',
    'Retained Census candidate',
    'publication not approved',
  ])
    assert.ok(result.html.includes(text), text);
  assert.match(result.html, /\/products\/09\?flow=exports/);
  assert.match(result.html, /\/sources\?flow=exports/);
  assert.doesNotMatch(result.html, /Fabricated test data/);
});

test('source view distinguishes four time concepts and separate classification definitions', () => {
  const result = renderReview(data(), '/sources?flow=exports', 'candidate');
  for (const text of [
    'Reporting period',
    'First retained retrieval',
    'Official release date',
    'Official revision date',
    'Publication time',
    'Not published',
    'Unknown',
    'Schedule B',
    'Schedule C',
    'API classification vintage',
    'not identified',
    'Historical comparability',
    'not established',
    'ALL_VAL_MO',
    'FAS value',
  ])
    assert.ok(result.html.includes(text), text);
  assert.ok(
    result.html.includes(
      'https://www.census.gov/foreign-trade/schedules/b/2026/c09.pdf',
    ),
  );
  assert.doesNotMatch(result.html, /GEN_VAL_MO|Chapter%209/);
});

test('unobserved country is distinct from zero and makes selected subtotal unavailable', () => {
  const raw = structuredClone(fixture),
    f = raw.flows[0];
  Object.assign(f.countries[2], {
    status: 'unobserved',
    value: null,
    shareOfWorldPercent: null,
    shareUnavailableReason: 'partner-not-observed',
  });
  Object.assign(f.coverage, {
    allSelectedObserved: false,
    missingSelectedCodes: ['5330'],
  });
  Object.assign(f.totals, {
    selectedTotalUSD: null,
    selectedShareOfWorldPercent: null,
  });
  const candidate = validateResearchCandidate(raw);
  const country = renderReview(candidate, '/countries/india', 'fixture').html;
  assert.match(country, /Not observed/);
  assert.match(country, /country observation is missing/);
  assert.doesNotMatch(country, /\$0|Reported zero|0\.00%/);
  const product = renderReview(candidate, '/products/09', 'fixture').html;
  assert.match(product, /Incomplete selected coverage/);
  assert.match(product, /Observed selected values/);
  assert.match(product, /\$60/);
});

test('missing and zero world controls explain unavailable shares without inventing numbers', () => {
  for (const zero of [false, true]) {
    const raw = structuredClone(fixture),
      f = raw.flows[0];
    f.world = {
      status: zero ? 'reported_zero' : 'unobserved',
      value: zero ? '0' : null,
    };
    for (const row of f.countries) {
      if (zero) Object.assign(row, { status: 'reported_zero', value: '0' });
      Object.assign(row, {
        shareOfWorldPercent: null,
        shareUnavailableReason: zero
          ? 'zero-world-denominator'
          : 'world-not-observed',
      });
    }
    if (zero)
      Object.assign(f.totals, {
        observedSelectedUSD: '0',
        selectedTotalUSD: '0',
      });
    f.totals.selectedShareOfWorldPercent = null;
    const html = renderReview(
      validateResearchCandidate(raw),
      '/countries/canada',
      'fixture',
    ).html;
    assert.ok(
      html.includes(
        zero ? 'world control is zero' : 'world control was not observed',
      ),
    );
    assert.doesNotMatch(html, /0\.00%/);
  }
});

test('all screens explain unavailable analyses and cannot infer historical change', () => {
  for (const path of ['/products/09', '/countries/china', '/sources']) {
    const html = renderReview(data(), path, 'fixture').html;
    for (const text of [
      'Only July 2026',
      'Year-over-year change',
      'Quantities',
      'country-level concentration',
      'noindex, nofollow',
    ])
      assert.ok(html.includes(text), text);
  }
});

test('root redirects, invalid filters fail clearly and unknown/private paths stay 404', () => {
  const root = renderReview(data(), '/', 'candidate');
  assert.equal(root.status, 302);
  assert.equal(root.location, '/products/09?flow=imports');
  for (const path of [
    '/products/09?flow=nope',
    '/products/09?flow=imports&flow=exports',
    '/products/09?period=2026-08',
    '/sources?x=<script>secret</script>',
  ]) {
    const result = renderReview(data(), path, 'candidate');
    assert.equal(result.status, 400);
    assert.match(result.html, /Reset view/);
    assert.doesNotMatch(result.html, /<script>|secret/);
  }
  for (const path of [
    '/countries/atlantis',
    '/products/0901',
    '/data/fresh.json',
    '/.local/public-candidate/fresh.json',
    '/../../.env',
    '//evil.invalid/products/09',
  ])
    assert.equal(renderReview(data(), path, 'candidate').status, 404);
});

test('escaping covers markup and attributes while values retain exact integer precision', () => {
  assert.equal(
    escapeHTML('<img onerror="x"> & \'y\''),
    '&lt;img onerror=&quot;x&quot;&gt; &amp; &#39;y&#39;',
  );
  const raw = structuredClone(fixture),
    f = raw.flows[0];
  f.world.value = '200000000000000000000000';
  const value = '1010000000000000000000';
  f.countries.forEach((row: any, index: number) =>
    Object.assign(row, {
      value: index ? '0' : value,
      status: index ? 'reported_zero' : 'reported',
      shareOfWorldPercent: index ? '0.00' : '0.51',
    }),
  );
  Object.assign(f.totals, {
    observedSelectedUSD: value,
    selectedTotalUSD: value,
    selectedShareOfWorldPercent: '0.51',
  });
  assert.match(
    renderReview(validateResearchCandidate(raw), '/countries/canada', 'fixture')
      .html,
    /\$1,010,000,000,000,000,000,000/,
  );
});

test('profile export actions retain the selected flow and explain local retry', () => {
  for (const path of ['/products/09', '/countries/india']) {
    const result = renderReview(data(), path + '?flow=exports', 'fixture');
    assert.match(
      result.html,
      new RegExp(`href="${path}\\.csv\\?flow=exports"[^>]*>Download CSV</a>`),
    );
    assert.match(
      result.html,
      new RegExp(
        `href="${path}/print\\?flow=exports"[^>]*>Printable summary</a>`,
      ),
    );
    assert.match(result.html, /download.*(?:fail|does not start)/i);
    assert.match(result.html, /retry/i);
    assert.doesNotMatch(
      result.html,
      /download (?:complete|succeeded|successful)/i,
    );
  }
  assert.doesNotMatch(
    renderReview(data(), '/sources', 'fixture').html,
    /Download CSV|Printable summary/,
  );
});

test('exact profile CSV routes return downloads only after flow validation', () => {
  for (const path of [
    '/products/09',
    '/countries/canada',
    '/countries/mexico',
    '/countries/india',
    '/countries/china',
  ]) {
    const result = renderReview(data(), path + '.csv?flow=exports', 'fixture');
    assert.equal(result.status, 200, path);
    assert.equal(result.html, '');
    assert.ok(result.download);
    assert.match(result.download.filename, /^[a-z0-9-]+\.csv$/);
    assert.match(result.download.csv, /ALL_VAL_MO/);
    assert.doesNotMatch(result.download.csv, /GEN_VAL_MO/);
  }
  for (const suffix of ['.csv', '/print']) {
    for (const query of [
      'flow=balance',
      'flow=imports&flow=exports',
      'period=2026-08',
      'flow=imports?x=private',
      'flow=imports&x=private',
    ]) {
      const result = renderReview(
        data(),
        '/countries/india' + suffix + '?' + query,
        'fixture',
      );
      assert.equal(result.status, 400, query);
      assert.equal(result.download, undefined);
      assert.match(result.html, /Reset view/);
      assert.doesNotMatch(result.html, /private/);
    }
  }
  for (const path of [
    '/products/0901.csv',
    '/countries/atlantis.csv',
    '/sources.csv',
    '/sources/print',
    '/products/09/print.csv',
    '/products/09.csv/print',
    '/countries/india/print/',
    '/products/09.csv/',
    '/countries/India.csv',
    '/products/%30%39.csv',
  ]) {
    const result = renderReview(data(), path + '?flow=exports', 'fixture');
    assert.equal(result.status, 404, path);
    assert.equal(result.download, undefined);
  }
});

test('printable chapter summary carries values and definitions without another page', () => {
  const result = renderReview(
    data(),
    '/products/09/print?flow=exports',
    'fixture',
  );
  assert.equal(result.status, 200);
  assert.equal(result.download, undefined);
  for (const text of [
    'Printable summary',
    'Coffee, tea, maté and spices',
    'July 2026',
    'US merchandise trade',
    'Exports',
    'World chapter value',
    '$100',
    'Four-country subtotal',
    '$60',
    'Canada',
    '$10',
    'Mexico',
    '$20',
    'India',
    '$0',
    'China',
    '$30',
    'Reported zero',
    'Total exports (domestic exports + re-exports)',
    'FAS value',
    'ALL_VAL_MO',
    'Not seasonally adjusted',
    'Nominal',
    'US dollars',
    'Missing values are not zero',
    'Official release date',
    'Official revision date',
    'Revision detection time',
    'Unknown',
    '2026-10-02T01:02:03Z',
    'Not published',
    'API classification vintage',
    'not identified',
    'Historical comparability',
    'not established',
    'Schedule B',
    'Schedule C',
    'Hong Kong, Macao and Taiwan',
    'Andaman, Nicobar, and Laccadive',
    'Isla de Cozumel',
    'Year-over-year change',
    'country-level concentration',
    'browser',
    'Save as PDF',
    'Unpublished local review',
    'Fabricated test data',
  ]) {
    assert.ok(result.html.includes(text), text);
  }
  for (const url of [
    'https://api.census.gov/data/timeseries/intltrade/exports/hs',
    'https://www.census.gov/foreign-trade/guide/sec2.html',
    ...data().flows[1].classification.referenceURLs,
    ...data().geography.referenceURLs,
  ]) {
    assert.ok(
      result.html.includes('>' + escapeHTML(url) + '</a>'),
      'Visible URL: ' + url,
    );
  }
  assert.match(
    result.html,
    /href="\/products\/09\?flow=exports"[^>]*>Back to profile/,
  );
  assert.match(result.html, /<table>/);
  assert.doesNotMatch(
    result.html,
    /<script|<form|GEN_VAL_MO|General imports|Customs value/,
  );
});

test('printable country summary excludes unrelated values and explains its geography', () => {
  const result = renderReview(
    data(),
    '/countries/india/print?flow=imports',
    'candidate',
  );
  assert.equal(result.status, 200);
  for (const text of [
    'US trade with India',
    'US imports from India',
    'General imports',
    'Customs value',
    'GEN_VAL_MO',
    '$0',
    '0.00%',
    'Reported zero',
    'not total US trade with this country',
    'Includes the Andaman, Nicobar, and Laccadive Islands.',
    'Schedule C 5330',
    'Retained Census candidate',
    'publication not approved',
  ]) {
    assert.ok(result.html.includes(text), text);
  }
  assert.match(
    result.html,
    /href="\/countries\/india\?flow=imports"[^>]*>Back to profile/,
  );
  assert.doesNotMatch(
    result.html,
    /\$10(?:<|\b)|\$20(?:<|\b)|\$30(?:<|\b)|\$60(?:<|\b)|ALL_VAL_MO|FAS value|Fabricated test data/,
  );
});

test('printable summaries retain missing observations and share denominator reasons', () => {
  const missing = structuredClone(fixture),
    f = missing.flows[0];
  Object.assign(f.countries[2], {
    status: 'unobserved',
    value: null,
    shareOfWorldPercent: null,
    shareUnavailableReason: 'partner-not-observed',
  });
  Object.assign(f.coverage, {
    allSelectedObserved: false,
    missingSelectedCodes: ['5330'],
  });
  Object.assign(f.totals, {
    selectedTotalUSD: null,
    selectedShareOfWorldPercent: null,
  });
  const candidate = validateResearchCandidate(missing);
  const country = renderReview(
    candidate,
    '/countries/india/print',
    'fixture',
  ).html;
  assert.match(country, /Not observed/);
  assert.match(country, /country observation is missing/);
  assert.match(country, /Incomplete selected coverage/);
  assert.doesNotMatch(
    country.match(/<table>[\s\S]*?<\/table>/)![0],
    /\$0|0\.00%|Reported zero/,
  );
  const product = renderReview(candidate, '/products/09/print', 'fixture').html;
  assert.match(product, /Observed selected values/);
  assert.match(product, /partial sum excludes missing observations/);
  for (const zero of [false, true]) {
    const raw = structuredClone(fixture),
      flow = raw.flows[0];
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
    const html = renderReview(
      validateResearchCandidate(raw),
      '/products/09/print',
      'fixture',
    ).html;
    assert.ok(
      html.includes(
        zero ? 'world control is zero' : 'world control was not observed',
      ),
    );
    assert.doesNotMatch(html, /0\.00%/);
  }
});
