import {
  validateRelease,
  parseQuery,
  queryString,
  valueAt,
  previousYear,
  change,
  money,
  pct,
  csv,
  BASIS,
  type Release,
  type Query,
  type Observation,
} from '../../packages/contracts/trade';
const root = document.querySelector<HTMLElement>('#explorer');
if (root) {
  const form = document.querySelector<HTMLFormElement>('#filters')!,
    message = document.querySelector<HTMLElement>('#explore-message')!,
    result = document.querySelector<HTMLElement>('#explore-result')!,
    status = document.querySelector<HTMLElement>('#download-status')!;
  let release: Release,
    query: Query,
    selected: Observation[] = [];
  const fail = (text: string) => {
    message.hidden = false;
    message.textContent = text;
    result.hidden = true;
  };
  function restore() {
    query = parseQuery(new URLSearchParams(location.search), release);
    selected = [];
    status.textContent = '';
    const fallback =
      document.querySelector<HTMLInputElement>('#share-fallback')!;
    fallback.hidden = true;
    fallback.value = '';
    for (const name of ['product', 'flow', 'period'] as const)
      (form.elements.namedItem(name) as HTMLSelectElement).value = query[name];
    form
      .querySelectorAll<HTMLInputElement>('input[name=partner]')
      .forEach((el) => (el.checked = query.partners.includes(el.value)));
    if (query.error) {
      fail(query.error);
      return;
    }
    if (root!.dataset.mode === 'compare' && !query.partners.length) {
      fail(
        'Your comparison is empty. Choose up to three countries above, then apply the filters.',
      );
      return;
    }
    const partners = query.partners.length
      ? query.partners
      : release.partners.filter((p) => p.kind === 'country').map((p) => p.id);
    selected = release.observations.filter(
      (o) =>
        o.flow === query.flow &&
        o.period === query.period &&
        o.product === query.product &&
        partners.includes(o.partner),
    );
    message.hidden = true;
    result.hidden = false;
    document.querySelector('#result-title')!.textContent =
      `${release.products.find((p) => p.code === query.product)!.name} · ${query.period}`;
    document.querySelector('#result-basis')!.textContent =
      `${BASIS[query.flow]} · nominal USD · not seasonally adjusted · sample figures`;
    const table = document.createElement('table'),
      caption = document.createElement('caption');
    caption.textContent = `Sample ${query.flow} for HS ${query.product}, ${query.period}`;
    table.append(caption);
    const head = table.createTHead().insertRow();
    for (const text of [
      'Partner',
      'Trade value (USD)',
      'Year over year',
      'Value status',
    ]) {
      const th = document.createElement('th');
      th.scope = 'col';
      th.textContent = text;
      head.append(th);
    }
    const body = table.createTBody();
    for (const row of selected) {
      const tr = body.insertRow(),
        th = document.createElement('th');
      th.scope = 'row';
      th.textContent = release.partners.find((p) => p.id === row.partner)!.name;
      tr.append(th);
      for (const text of [
        money(row.value, false),
        pct(
          change(
            row.value,
            valueAt(
              release,
              row.product,
              row.partner,
              row.flow,
              previousYear(row.period),
            ),
          ).percent,
        ),
        row.status.replaceAll('_', ' '),
      ]) {
        const td = tr.insertCell();
        td.textContent = text;
      }
    }
    document.querySelector('#result-table')!.replaceChildren(table);
  }
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (!release) {
      fail('The dataset is not loaded. Reload this page to retry.');
      return;
    }
    const params = new URLSearchParams();
    for (const name of ['product', 'flow', 'period', 'release'])
      params.set(name, String(new FormData(form).get(name)));
    params.set(
      'partners',
      [
        ...form.querySelectorAll<HTMLInputElement>(
          'input[name=partner]:checked',
        ),
      ]
        .map((el) => el.value)
        .join(','),
    );
    const next = parseQuery(params, release);
    if (next.error) {
      fail(next.error);
      return;
    }
    history.pushState({}, '', `${location.pathname}?${queryString(next)}`);
    restore();
  });
  document.querySelector('#share')!.addEventListener('click', async () => {
    const url = new URL(location.href);
    url.search = queryString(query);
    try {
      await navigator.clipboard.writeText(url.href);
      status.textContent =
        'Link copied. It includes the selected filters and release.';
    } catch {
      const fallback =
        document.querySelector<HTMLInputElement>('#share-fallback')!;
      fallback.hidden = false;
      fallback.value = url.href;
      fallback.select();
      status.textContent = 'Copy the link from the field below.';
    }
  });
  document.querySelector('#download')!.addEventListener('click', () => {
    try {
      const blob = new Blob([csv(release, selected)], {
          type: 'text/csv;charset=utf-8',
        }),
        url = URL.createObjectURL(blob),
        a = document.createElement('a');
      a.href = url;
      a.download = `sample-${query.product}-${query.flow}-${query.period}.csv`;
      document.body.append(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
      status.textContent =
        'Your sample CSV is ready. If saving was blocked, allow downloads for this page and try again.';
    } catch {
      status.textContent =
        'The download could not be prepared. Your filters are preserved; try again or open the provenance JSON.';
    }
  });
  window.addEventListener('popstate', () => {
    if (release) restore();
  });
  fetch(root.dataset.releaseUrl!, {
    signal: AbortSignal.timeout(15000),
    credentials: 'omit',
  })
    .then(async (response) => {
      if (!response.ok) throw new Error('Unavailable');
      const data = await response.text();
      if (data.length > 2_000_000) throw new Error('Oversized');
      release = validateRelease(JSON.parse(data));
      restore();
    })
    .catch(() =>
      fail(
        'The dataset could not be loaded. Reload this page to retry. Your URL filters are preserved; static product profiles are still available.',
      ),
    );
}
