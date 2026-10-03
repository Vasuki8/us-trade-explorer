import type { ResearchCandidate } from '../../packages/contracts/research-candidate.ts';
import { csvCell } from '../../packages/contracts/trade.ts';

const COUNTRY_CODES = ['1220', '2010', '5330', '5700'] as const;
const METHODOLOGY_URL = 'https://www.census.gov/foreign-trade/guide/sec2.html';

/**
 * Export an already validated snapshot. Unknown dates are blank and have an
 * explicit state column; publication stays absent for this unpublished review.
 * Dollar cells are exact integer strings. Other cells use the shared encoder's
 * quoting and formula-injection protection, including leading controls/spaces.
 */

export function createReviewDownload(
  data: ResearchCandidate,
  flowName: 'imports' | 'exports',
  countryIndex: number | null,
  mode: 'candidate' | 'fixture',
): { csv: string; filename: string } {
  if (
    (flowName !== 'imports' && flowName !== 'exports') ||
    (mode !== 'candidate' && mode !== 'fixture') ||
    (countryIndex !== null &&
      (!Number.isInteger(countryIndex) ||
        countryIndex < 0 ||
        countryIndex >= COUNTRY_CODES.length))
  )
    throw new Error('Invalid review download selection');
  const flow = data.flows.find((item) => item.flow === flowName);
  if (!flow) throw new Error('Missing review download flow');
  const basis = flow.statisticalBasis;
  const context = {
    reporter: data.scope.reporter,
    product_code: data.scope.product.code,
    product: data.scope.product.name,
    product_level: data.scope.product.level,
    flow: flow.flow,
    reporting_period: data.scope.period,
    period_kind: data.scope.periodKind,
    statistical_basis: basis.tradeBasis,
    valuation: basis.valuation,
    source_measure: basis.measure,
    unit: basis.unit,
    price_basis: basis.priceBasis,
    seasonal_adjustment: basis.seasonalAdjustment,
    commodity_classification: basis.commodityClassification,
    classification_system: flow.classification.system,
    selected_scope: data.coverage.kind,
    all_selected_observed: String(flow.coverage.allSelectedObserved),
    missing_selected_codes: flow.coverage.missingSelectedCodes.join('; '),
    global_coverage_complete: String(data.coverage.globalCoverageComplete),
    world_denominator_status: flow.world.status,
    source_agency: flow.source.agency,
    source_url: flow.source.datasetURL,
    methodology_url: METHODOLOGY_URL,
    retrieved_at: flow.times.retrievedAt,
    official_release_date: flow.times.officialReleaseDate ?? '',
    official_release_date_state: 'unknown',
    official_revision_date: flow.times.officialRevisionDate ?? '',
    official_revision_date_state: 'unknown',
    revision_detected_at: flow.times.revisionDetectedAt ?? '',
    revision_detected_at_state: 'unknown',
    published_at: flow.times.publishedAt ?? '',
    published_at_state: 'not-published',
    publication_state: data.publicationState,
    data_mode: mode,
    data_notice:
      mode === 'fixture'
        ? 'Fabricated test data; all figures are invented. Unpublished local review.'
        : 'Retained Census candidate; publication not approved.',
    classification_reference_urls: flow.classification.referenceURLs.join('; '),
    api_classification_vintage: flow.classification.apiClassificationVintage,
    provision_effective_from:
      flow.classification.provisionEffectiveFromVerified ?? '',
    provision_effective_from_state: 'unknown',
    historical_comparability: flow.classification.historicalComparability,
    historical_growth: data.analysisPolicy.historicalGrowth,
    fine_code_joins: data.analysisPolicy.fineCodeJoins,
    quantity_metrics: data.analysisPolicy.quantityMetrics,
    global_rankings_and_concentration:
      data.analysisPolicy.globalRankingsAndConcentration,
    geography_system: data.geography.system,
    geography_claim: data.geography.claim,
    geography_reference_urls: data.geography.referenceURLs.join('; '),
    designation_effective_from: data.geography.effectiveFromVerified ?? '',
    designation_effective_from_state: 'unknown',
    scope_note:
      countryIndex === null
        ? 'Chapter 09 only; world control and four selected countries, not all product trade.'
        : 'Chapter 09 only; not total US trade with this country.',
    share_methodology:
      'Country or complete selected subtotal divided by the same-flow world chapter value when observed and positive; rounded half-up to two decimal places. Missing values are not zero.',
  };
  function row(
    kind: string,
    partnerCode: string,
    partner: string,
    value: string | null,
    status: string,
    note: string,
    share: string | null,
    shareReason: string | null,
    geographicNote: string | null = null,
  ) {
    return {
      row_kind: kind,
      partner_code: partnerCode,
      partner,
      value_nominal_usd: value ?? '',
      observation_status: status,
      observation_note: note,
      share_of_world_percent: share ?? '',
      share_unavailable_reason: shareReason ?? '',
      geographic_note: geographicNote ?? '',
      ...context,
    };
  }
  const rows = [
    row(
      'world',
      '',
      'World chapter value',
      flow.world.value,
      flow.world.status,
      'Source world control across all trading partners, including those outside the selected subset.',
      null,
      'not-applicable-world-control',
    ),
  ];
  const countries =
    countryIndex === null ? flow.countries : [flow.countries[countryIndex]];
  for (const country of countries)
    rows.push(
      row(
        'country',
        country.code,
        country.name,
        country.value,
        country.status,
        country.status === 'unobserved'
          ? 'No observation in this retained snapshot; blank does not mean zero.'
          : country.status === 'reported_zero'
            ? 'Observed value is explicitly zero.'
            : 'Observed country chapter value.',
        country.shareOfWorldPercent,
        country.shareUnavailableReason,
        country.geographicNote,
      ),
    );
  if (countryIndex === null) {
    const complete = flow.totals.selectedTotalUSD !== null;
    const value = complete
      ? flow.totals.selectedTotalUSD!
      : flow.totals.observedSelectedUSD;
    const reason = !complete
      ? 'incomplete-selected-coverage'
      : flow.world.status === 'unobserved'
        ? 'world-not-observed'
        : flow.world.status === 'reported_zero'
          ? 'zero-world-denominator'
          : null;
    rows.push(
      row(
        complete ? 'selected_subtotal' : 'observed_selected_partial',
        '',
        complete
          ? 'Four selected countries subtotal'
          : 'Observed selected values only (partial)',
        value,
        complete
          ? value === '0'
            ? 'calculated_zero_subtotal'
            : 'calculated_subtotal'
          : 'calculated_partial_sum',
        complete
          ? 'Calculated sum of all four selected countries; not a global total.'
          : 'Partial sum excludes unobserved countries; a complete selected subtotal is unavailable.',
        complete ? flow.totals.selectedShareOfWorldPercent : null,
        reason,
      ),
    );
  }
  const header = Object.keys(rows[0]) as (keyof (typeof rows)[number])[];
  const csv =
    '\uFEFF' +
    [
      header.map((name) => csvCell(name)).join(','),
      ...rows.map((item) =>
        header
          .map((name) =>
            csvCell(
              item[name],
              name === 'value_nominal_usd' && item[name] !== '',
            ),
          )
          .join(','),
      ),
    ].join('\r\n');
  // Only fixed contract selectors enter Content-Disposition, never source labels.
  const subject =
    countryIndex === null
      ? 'chapter09'
      : `country${COUNTRY_CODES[countryIndex]}-chapter09`;
  const marker = mode === 'fixture' ? 'fixture' : 'unpublished';
  return { csv, filename: `ust-${subject}-${flowName}-2026-07-${marker}.csv` };
}
