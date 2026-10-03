import sample from '../../tests/fixtures/sample-release.json';
import manifest from '../../releases/sample-2026-07-v1.manifest.json';
import {
  encodePublicRelease,
  loadPublicRelease,
  validatePublicManifest,
} from '../../packages/contracts/public-release';
import {
  valueAt,
  sum,
  previousYear,
  type Flow,
} from '../../packages/contracts/trade';
import { changeView } from './change-view';
const sampleBytes = encodePublicRelease(sample);
export const publicManifest = validatePublicManifest(manifest);
export const release = await loadPublicRelease(
  publicManifest,
  (contentHash) => {
    if (contentHash !== publicManifest.contentHash) {
      throw new Error('Unsupported public sample content hash');
    }
    return sampleBytes;
  },
);
// Immutable text preserves the exact validated UTF-8 encoding for the endpoint.
export const publicReleaseJSON = new TextDecoder('utf-8', {
  fatal: true,
}).decode(sampleBytes);
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
  ).map((r) => ({
    ...r,
    change: changeView(r.value, r.previous, {
      priorYearIncluded: release.periods.includes(previousYear(period)),
      scope: 'observation',
    }),
  }));
}
