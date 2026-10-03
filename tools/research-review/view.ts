/** Server-rendered review screens. No imports from or into the public application. */
import type { ResearchCandidate } from '../../packages/contracts/research-candidate.ts';

type Flow = ResearchCandidate['flows'][number];
type Country = Flow['countries'][number];
type Mode = 'candidate' | 'fixture';
export type ReviewPage = { status: number; html: string; location?: string };
const SLUGS = ['canada', 'mexico', 'india', 'china'];

export function escapeHTML(value: string): string {
  return value.replace(
    /[&<>"']/g,
    (char) =>
      ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[
        char
      ]!,
  );
}
const dollars = (value: string | null) =>
  value === null ? 'Not observed' : '$' + BigInt(value).toLocaleString('en-US');
const href = (path: string, flow: string) => `${path}?flow=${flow}`;
const status = (value: { status: string }) =>
  value.status === 'reported_zero'
    ? 'Reported zero'
    : value.status === 'unobserved'
      ? 'Not observed'
      : 'Reported';
function definition(flow: Flow) {
  return flow.flow === 'imports'
    ? {
        label: 'Imports',
        basis: 'General imports',
        valuation: 'Customs value',
        relation: 'from',
      }
    : {
        label: 'Exports',
        basis: 'Total exports (domestic exports + re-exports)',
        valuation: 'FAS value',
        relation: 'to',
      };
}
function reason(row: Country): string {
  return (
    (
      {
        'partner-not-observed': 'The country observation is missing.',
        'world-not-observed': 'The world control was not observed.',
        'zero-world-denominator':
          'The world control is zero; a percentage cannot be calculated.',
      } as Record<string, string>
    )[row.shareUnavailableReason ?? ''] ?? ''
  );
}
function share(row: Country): string {
  return row.shareOfWorldPercent === null
    ? `<span>Unavailable</span><small>${escapeHTML(reason(row))}</small>`
    : escapeHTML(row.shareOfWorldPercent) + '%';
}
function limitations(): string {
  return `<section class="limits" aria-labelledby="limits-title"><span class="eyebrow">WHAT CHANGED?</span>
    <h2 id="limits-title">A single month, with clear limits</h2><p>Only July 2026 is included in this candidate. Year-over-year change and historical trends are unavailable.</p>
    <p>Quantities, value-per-unit metrics and country-level concentration are not supported. Four selected countries do not establish a global ranking. These values identify no cause for a change.</p></section>`;
}
function coverage(flow: Flow): string {
  return `<section class="card"><span class="eyebrow">COVERAGE</span><h2>Four selected countries</h2>
    <p>Canada, Mexico, India and China. Other partners are outside this review; the world control includes trade beyond these four countries.</p>
    <p class="coverage-state">${flow.coverage.allSelectedObserved ? 'All four selected observations are present.' : 'Incomplete selected coverage. A complete four-country subtotal is unavailable.'}</p>
    <p>Country shares use the same-flow world chapter value, when it is observed and positive.</p></section>`;
}
function context(flow: Flow): string {
  const d = definition(flow);
  return `<div class="basis" aria-label="Statistical basis"><span>July 2026</span><span>${d.basis}</span><span>${d.valuation}</span><span>USD</span><span>Monthly</span><span>Not seasonally adjusted</span></div>
    <p class="small">US merchandise trade · Nominal values, not adjusted for inflation · Chapter 09 (HS2)</p>`;
}
function controls(path: string, flow: Flow): string {
  return `<form class="flow-form" action="${path}" method="get"><label for="trade-flow">Trade flow</label>
    <select id="trade-flow" name="flow"><option value="imports"${flow.flow === 'imports' ? ' selected' : ''}>Imports</option><option value="exports"${flow.flow === 'exports' ? ' selected' : ''}>Exports</option></select><button type="submit">Apply</button>
    <span class="small">Period: July 2026 · the only included month</span></form>`;
}
function sourceSummary(flow: Flow): string {
  return `<section class="card source-card"><span class="eyebrow">VERIFY THE SOURCE</span><h2>Source and collection</h2>
    <p>US Census Bureau · <a href="${escapeHTML(flow.source.datasetURL)}" rel="noreferrer">Official dataset definition</a></p>
    <dl><dt>Reporting period</dt><dd>July 2026</dd><dt>First retained retrieval</dt><dd><time datetime="${escapeHTML(flow.times.retrievedAt)}">${escapeHTML(flow.times.retrievedAt.replace('T', ' ').replace('Z', ' UTC'))}</time></dd>
    <dt>Official release / revision dates</dt><dd>Unknown for this retained API snapshot</dd><dt>Publication time</dt><dd>Not published</dd></dl>
    <p class="small">Collection time does not identify an official revision or establish that this is the latest release.</p>
    <a href="${href('/sources', flow.flow)}">Sources and methodology <span aria-hidden="true">→</span></a></section>`;
}
function product(data: ResearchCandidate, flow: Flow): string {
  const d = definition(flow);
  const subtotal =
    flow.totals.selectedTotalUSD === null
      ? 'Unavailable'
      : dollars(flow.totals.selectedTotalUSD);
  return `<header class="page-head"><span class="eyebrow">PRODUCT PROFILE · HS2 CHAPTER 09</span><h1>${escapeHTML(data.scope.product.name)}</h1>
    <p class="lede">What the United States ${flow.flow === 'imports' ? 'imports from' : 'exports to'} the world, and the role of four selected trading partners.</p>${context(flow)}</header>
    ${controls('/products/09', flow)}<div class="content-grid"><div>
    <section class="metrics" aria-label="Chapter values"><div class="metric"><span>World chapter value</span><strong>${dollars(flow.world.value)}</strong><small>${status(flow.world)} · ${d.label.toLowerCase()} across all partners in the source world control</small></div>
    <div class="metric"><span>Four-country subtotal</span><strong>${subtotal}</strong><small>${flow.totals.selectedShareOfWorldPercent === null ? 'Share of world unavailable' : flow.totals.selectedShareOfWorldPercent + '% of world chapter value'}</small></div></section>
    ${flow.totals.selectedTotalUSD === null ? `<p class="notice">Incomplete selected coverage. Observed selected values: <strong>${dollars(flow.totals.observedSelectedUSD)}</strong>. This partial sum excludes missing observations.</p>` : ''}
    <section class="card table-card"><div class="section-heading"><div><span class="eyebrow">COUNTRY BREAKDOWN</span><h2>Explore the selected partners</h2></div><span class="small">Schedule C order · not a ranking</span></div>
    <div class="table-scroll" tabindex="0" role="region" aria-label="Selected partner values"><table><caption>Chapter 09 · ${d.label} · July 2026 · nominal USD</caption><thead><tr><th scope="col">Trading partner</th><th scope="col">Value (USD)</th><th scope="col">Share of world chapter</th><th scope="col">Observation</th></tr></thead><tbody>
    ${flow.countries.map((row, index) => `<tr><th scope="row"><a href="${href('/countries/' + SLUGS[index], flow.flow)}">${escapeHTML(row.name)}</a></th><td class="numeric">${dollars(row.value)}</td><td class="numeric">${share(row)}</td><td>${status(row)}</td></tr>`).join('')}</tbody></table></div></section>
    ${limitations()}</div><aside aria-label="Coverage and sources">${coverage(flow)}${sourceSummary(flow)}</aside></div>`;
}
function country(data: ResearchCandidate, flow: Flow, index: number): string {
  const row = flow.countries[index],
    d = definition(flow);
  return `<header class="page-head"><span class="eyebrow">COUNTRY PROFILE · SELECTED CHAPTER</span><h1>US trade with ${escapeHTML(row.name)}</h1>
    <p class="lede">Chapter 09 · ${escapeHTML(data.scope.product.name)}</p><p>This covers one chapter only; it is not total US trade with this country.</p>${context(flow)}</header>
    ${controls('/countries/' + SLUGS[index], flow)}<div class="content-grid"><div>
    <section class="metrics" aria-label="Country chapter values"><div class="metric"><span>US ${flow.flow} ${d.relation} ${escapeHTML(row.name)}</span><strong>${dollars(row.value)}</strong><small>${status(row)} · Chapter 09 only</small></div>
    <div class="metric"><span>Share of world chapter value</span><strong>${share(row)}</strong></div></section>
    <section class="card"><span class="eyebrow">COUNTRY DEFINITION</span><h2>${escapeHTML(row.name)} · Schedule C ${row.code}</h2>
    <p>${escapeHTML(row.geographicNote ?? 'Reviewed as the named Schedule C country designation.')}</p><p class="small">The reviewed references do not certify a complete global partner inventory or an effective date for every designation.</p>
    <a href="${href('/products/09', flow.flow)}">Compare the four selected countries <span aria-hidden="true">→</span></a></section>
    ${limitations()}</div><aside aria-label="Coverage and sources">${coverage(flow)}${sourceSummary(flow)}</aside></div>`;
}
function sources(data: ResearchCandidate, flow: Flow): string {
  const d = definition(flow);
  return `<header class="page-head"><span class="eyebrow">SOURCES AND METHODOLOGY</span><h1>Follow a value back to its source</h1><p class="lede">Definitions, collection context and limits for this unpublished candidate.</p>${context(flow)}</header>
    ${controls('/sources', flow)}<div class="content-grid"><div><section class="card"><h2>Statistical definitions</h2><dl>
    <dt>Reporter / scope</dt><dd>United States merchandise trade, chapter 09, July 2026</dd><dt>Trade basis</dt><dd>${d.basis}</dd><dt>Valuation</dt><dd>${d.valuation}</dd>
    <dt>Source measure</dt><dd>${flow.statisticalBasis.measure}</dd><dt>Unit / adjustment</dt><dd>Nominal USD · Monthly · Not seasonally adjusted</dd></dl>
    <p>${flow.flow === 'imports' ? 'General imports record arrivals into the United States, including entries into bonded warehouses and foreign trade zones; they differ from imports for consumption. Customs value excludes international freight, insurance and other import charges.' : 'Total exports include domestic exports and re-exports. FAS (free alongside ship) value includes the value at the US port of export, including inland freight and related costs to that point.'}</p>
    <p><a href="https://www.census.gov/foreign-trade/guide/sec2.html" rel="noreferrer">Read the Census statistical guide</a> for the full definitions and limitations.</p>
    <p>Partner shares divide a selected country value by the same-flow world chapter value. Exact integer dollars are retained; percentages are rounded half-up to two decimal places. Missing values are not zero.</p></section>
    <section class="card"><h2>Classification and country references</h2><dl><dt>Product classification</dt><dd>${flow.classification.system} · Chapter 09 at HS2 level</dd><dt>API classification vintage</dt><dd>not identified</dd><dt>Historical comparability</dt><dd>not established</dd><dt>Provision / designation effective dates</dt><dd>Unknown</dd></dl>
    <h3>${flow.classification.system} references</h3><ul>${flow.classification.referenceURLs.map((url, index) => `<li><a href="${escapeHTML(url)}" rel="noreferrer">${flow.flow === 'imports' ? `2026 HTS revision ${11 + index} — chapter 09` : index === 0 ? '2026 Schedule B index' : '2026 Schedule B chapter 09'}</a></li>`).join('')}</ul>
    <h3>Schedule C country designations</h3><ul>${data.geography.referenceURLs.map((url, index) => `<li><a href="${escapeHTML(url)}" rel="noreferrer">2026 HTS revision ${11 + index} — statistical annexes</a></li>`).join('')}</ul>
    <p>These references support the reviewed single-month chapter and selected country labels. They do not establish continuous classifications through history, compatible quantities or fine-code equivalence between imports and exports.</p></section>
    <section class="card"><h2>Dates have different meanings</h2><dl><dt>Reporting period</dt><dd>July 2026 — when the trade occurred</dd><dt>First retained retrieval</dt><dd>${escapeHTML(flow.times.retrievedAt)} — when this snapshot was collected</dd><dt>Official release date</dt><dd>Unknown for this API snapshot</dd><dt>Official revision date</dt><dd>Unknown</dd><dt>Revision detection time</dt><dd>Unknown</dd><dt>Publication time</dt><dd>Not published</dd></dl>
    <p>A checksum verifies consistent bytes, not official source authenticity or publication approval. This review uses a validated local candidate and does not contact the Census API.</p></section>${limitations()}</div>
    <aside aria-label="Coverage and sources">${coverage(flow)}${sourceSummary(flow)}</aside></div>`;
}
function shell(title: string, body: string, flow: string, mode: Mode): string {
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex, nofollow"><meta name="referrer" content="no-referrer"><title>${escapeHTML(title)} | US Trade Explorer — Local review</title><link rel="stylesheet" href="/review.css"></head>
    <body><a class="skip" href="#main">Skip to content</a><div class="review-banner"><strong>Unpublished local review</strong><span>${mode === 'fixture' ? 'Fabricated test data — all figures are invented.' : 'Retained Census candidate — publication not approved.'}</span></div>
    <header class="site-header"><div class="container header-inner"><a class="brand" href="${href('/products/09', flow)}">US Trade <span>Explorer</span></a><span class="local-tag">LOCAL RESEARCH REVIEW</span></div><nav class="container" aria-label="Main navigation"><a href="${href('/products/09', flow)}">Chapter profile</a><a href="${href('/sources', flow)}">Sources and methodology</a></nav></header>
    <main id="main" class="container">${body}</main><footer class="container"><strong>US Trade Explorer</strong><p>Local review only. No public release, account, tracking or API request. Source links open official reference pages when selected.</p></footer></body></html>`;
}
export function renderReview(
  data: ResearchCandidate,
  target: string,
  mode: Mode,
): ReviewPage {
  const [path, query = ''] = target.split('?');
  const index = SLUGS.findIndex((slug) => path === '/countries/' + slug);
  const known =
    path === '/' ||
    path === '/products/09' ||
    path === '/sources' ||
    index !== -1;
  const error = (code: number) => ({
    status: code,
    html: shell(
      code === 400 ? 'Invalid view' : 'Page not found',
      `<section class="page-head"><h1>${code === 400 ? 'This filter combination is not available' : 'Page not found'}</h1><p>Review chapter 09 for July 2026 with imports or exports.</p><a href="/products/09?flow=imports">Reset view</a></section>`,
      'imports',
      mode,
    ),
  });
  if (!known) return error(404);
  const params = new URLSearchParams(query),
    selected = params.get('flow') ?? 'imports';
  if (
    target.length > 2048 ||
    target.split('?').length > 2 ||
    [...params.keys()].some((key) => key !== 'flow') ||
    params.getAll('flow').length > 1 ||
    !['imports', 'exports'].includes(selected)
  )
    return error(400);
  if (path === '/')
    return { status: 302, html: '', location: href('/products/09', selected) };
  const flow = data.flows.find((entry) => entry.flow === selected)!;
  const body =
    path === '/products/09'
      ? product(data, flow)
      : path === '/sources'
        ? sources(data, flow)
        : country(data, flow, index);
  const title =
    index >= 0
      ? 'US trade with ' + flow.countries[index].name
      : path === '/sources'
        ? 'Sources and methodology'
        : data.scope.product.name;
  return { status: 200, html: shell(title, body, selected, mode) };
}
