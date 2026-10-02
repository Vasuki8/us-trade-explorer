import sample from '../../tests/fixtures/sample-release.json';
import {
  validateRelease,
  valueAt,
  sum,
  change,
  previousYear,
  type Flow,
} from '../../packages/contracts/trade';
export const release = validateRelease(sample);
export const latest = release.periods.at(-1)!;
export const countries = release.partners.filter((p) => p.kind === 'country');
export const href = (path: string) =>
  `${import.meta.env.BASE_URL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
export const productUrl = (code: string, flow: Flow = 'imports') =>
  href(`products/hs/HS2022/${code}/${flow}/`);
export const countryUrl = (id: string, flow: Flow = 'imports') =>
  href(`countries/${id}/${flow}/`);
export const month = (p: string) =>
  new Intl.DateTimeFormat('en-US', {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${p}-01T00:00:00Z`));
export function total(partner: string, flow: Flow, period = latest) {
  return sum(
    release.products.map((p) =>
      valueAt(release, p.code, partner, flow, period),
    ),
  );
}
export function profileRows(
  kind: 'product' | 'country',
  id: string,
  flow: Flow,
  period = latest,
) {
  return (
    kind === 'product'
      ? countries.map((p) => ({
          id: p.id,
          name: p.name,
          code: p.code,
          url: countryUrl(p.id, flow),
          value: valueAt(release, id, p.id, flow, period),
          previous: valueAt(release, id, p.id, flow, previousYear(period)),
        }))
      : release.products.map((p) => ({
          id: p.code,
          name: p.name,
          code: p.code,
          url: productUrl(p.code, flow),
          value: valueAt(release, p.code, id, flow, period),
          previous: valueAt(release, p.code, id, flow, previousYear(period)),
        }))
  ).map((r) => ({ ...r, change: change(r.value, r.previous) }));
}
