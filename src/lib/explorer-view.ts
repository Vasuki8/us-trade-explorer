import {
  previousYear,
  sum,
  valueAt,
  type Query,
  type Release,
} from '../../packages/contracts/trade.ts';

// Display calculations are not observations and must never enter the CSV.
export interface ExplorerRow {
  partner: string;
  value: string | null;
  previous: string | null;
  statusLabel: string;
}

export function explorerView(release: Release, query: Query) {
  const partners = release.partners
    .filter(
      (p) =>
        p.kind === 'country' &&
        (!query.partners.length || query.partners.includes(p.id)),
    )
    .map((p) => p.id);
  const products = release.products
    .filter((p) => query.product === 'all' || p.code === query.product)
    .map((p) => p.code);
  const observations = release.observations.filter(
    (o) =>
      o.flow === query.flow &&
      o.period === query.period &&
      products.includes(o.product) &&
      partners.includes(o.partner),
  );
  const rows: ExplorerRow[] =
    query.product === 'all'
      ? partners.map((partner) => {
          const value = sum(
            products.map((product) =>
              valueAt(release, product, partner, query.flow, query.period),
            ),
          );
          return {
            partner,
            value,
            previous: sum(
              products.map((product) =>
                valueAt(
                  release,
                  product,
                  partner,
                  query.flow,
                  previousYear(query.period),
                ),
              ),
            ),
            statusLabel:
              value === null
                ? 'Unavailable chapter sum'
                : 'Calculated chapter sum',
          };
        })
      : observations.map((o) => ({
          partner: o.partner,
          value: o.value,
          previous: valueAt(
            release,
            o.product,
            o.partner,
            o.flow,
            previousYear(o.period),
          ),
          statusLabel: o.status.replaceAll('_', ' '),
        }));
  return { rows, observations };
}
