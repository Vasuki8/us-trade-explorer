import { test as base, expect, type Page } from '@playwright/test';

const origin = 'http://127.0.0.1:4323';
const productName = 'Coffee, tea, maté and spices';
const flows = ['imports', 'exports'] as const;
type Flow = (typeof flows)[number];

// Every journey fails if the review begins requesting data, assets or telemetry
// from another origin. Official source links remain links until selected.
const test = base.extend<{ localRequests: void }>({
  localRequests: [
    async ({ context }, use) => {
      const externalRequests: string[] = [];
      context.on('request', (request) => {
        if (new URL(request.url()).origin !== origin) {
          externalRequests.push(request.url());
        }
      });
      await use();
      expect(externalRequests).toEqual([]);
    },
    { auto: true },
  ],
});

async function expectReviewContext(page: Page, flow: Flow) {
  const body = page.locator('body');
  await expect(body).toContainText('Unpublished local review');
  await expect(body).toContainText('Fabricated test data');
  await expect(body).toContainText('July 2026');
  await expect(body).toContainText(/US merchandise trade/i);
  await expect(body).toContainText(/HS2.*09|chapter 09/i);
  await expect(body).toContainText(/US dollars|USD/);
  await expect(body).toContainText(
    /historical (?:change|trends).*unavailable/i,
  );
  await expect(page.getByLabel('Trade flow', { exact: true })).toHaveValue(
    flow,
  );
  await expect(body).toContainText(
    flow === 'imports'
      ? 'General imports'
      : 'Total exports (domestic exports + re-exports)',
  );
  await expect(body).toContainText(
    flow === 'imports' ? 'Customs value' : 'FAS value',
  );
  await expect(page.locator('script')).toHaveCount(0);
}

for (const flow of flows) {
  test(`direct ${flow} product entry explains the world control and selected partners`, async ({
    page,
  }, info) => {
    await page.goto(`/products/09?flow=${flow}`);
    await expect(
      page.getByRole('heading', { name: productName, exact: true }),
    ).toBeVisible();
    await expectReviewContext(page, flow);
    await expect(page.getByText('$100', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('$60', { exact: true }).first()).toBeVisible();
    const table = page.getByRole('table').first();
    for (const [country, value, share] of [
      ['Canada', '$10', '10.00%'],
      ['Mexico', '$20', '20.00%'],
      ['India', '$0', '0.00%'],
      ['China', '$30', '30.00%'],
    ]) {
      const row = table.getByRole('row').filter({ hasText: country });
      await expect(row).toContainText(value);
      await expect(row).toContainText(share);
      await expect(
        row.getByRole('link', { name: country, exact: true }),
      ).toHaveAttribute(
        'href',
        `/countries/${country.toLowerCase()}?flow=${flow}`,
      );
    }
    await expect(
      table.getByRole('row').filter({ hasText: 'India' }),
    ).toContainText(/reported zero/i);
    await expect(page.locator('body')).toContainText(
      /selected.*(?:four|4)|(?:four|4).*selected/i,
    );
    await page.screenshot({
      path: `.local/research-review/screenshots/product-${flow}-${info.project.name}.png`,
      fullPage: true,
    });
  });

  test(`direct ${flow} country profiles stay within chapter 09`, async ({
    page,
  }, info) => {
    for (const [country, value] of [
      ['Canada', '$10'],
      ['Mexico', '$20'],
      ['India', '$0'],
      ['China', '$30'],
    ]) {
      await page.goto(`/countries/${country.toLowerCase()}?flow=${flow}`);
      await expect(
        page.getByRole('heading', {
          name: `US trade with ${country}`,
          exact: true,
        }),
      ).toBeVisible();
      await expectReviewContext(page, flow);
      await expect(page.locator('body')).toContainText(/chapter 09/i);
      await expect(page.locator('body')).toContainText(
        /not.*(?:total.*country|(?:country|national).*total)/i,
      );
      await expect(
        page.getByText(value, { exact: true }).first(),
      ).toBeVisible();
      await expect(
        page.getByRole('link', { name: 'Chapter profile', exact: true }),
      ).toHaveAttribute('href', `/products/09?flow=${flow}`);
      if (country === 'India') {
        await expect(page.locator('body')).toContainText(/reported zero/i);
        await page.screenshot({
          path: `.local/research-review/screenshots/country-${flow}-${info.project.name}.png`,
          fullPage: true,
        });
      }
    }
  });

  test(`direct ${flow} sources entry separates source dates from publication`, async ({
    page,
  }, info) => {
    await page.goto(`/sources?flow=${flow}`);
    await expectReviewContext(page, flow);
    await expect(
      page.locator(
        `a[href="https://api.census.gov/data/timeseries/intltrade/${flow}/hs"]`,
      ),
    ).toBeVisible();
    const body = page.locator('body');
    await expect(body).toContainText('US Census Bureau');
    await expect(body).toContainText(/official release date/i);
    await expect(body).toContainText(/official revision date/i);
    await expect(body).toContainText(/retriev|collect/i);
    await expect(body).toContainText('2026-10-02');
    await expect(body).toContainText(/not published|unpublished/i);
    await expect(body).toContainText(
      /not known|unknown|not supplied|unavailable|not identified/i,
    );
    await expect(body).toContainText(
      flow === 'imports' ? 'HTSUS' : 'Schedule B',
    );
    await expect(body).toContainText('Schedule C');
    await page.screenshot({
      path: `.local/research-review/screenshots/sources-${flow}-${info.project.name}.png`,
      fullPage: true,
    });
  });
}

test('flow selection survives cross-links, history and reload with JavaScript disabled', async ({
  page,
}) => {
  await page.goto('/');
  await expect(page).toHaveURL(`${origin}/products/09?flow=imports`);
  await expect(page.locator('form')).toHaveAttribute('method', /get/i);
  await page.getByLabel('Trade flow', { exact: true }).selectOption('exports');
  await page.getByRole('button', { name: 'Apply', exact: true }).click();
  await expect(page).toHaveURL(`${origin}/products/09?flow=exports`);
  await page.getByRole('link', { name: 'India', exact: true }).click();
  await expect(page).toHaveURL(`${origin}/countries/india?flow=exports`);
  await expectReviewContext(page, 'exports');
  await page
    .getByRole('navigation', { name: 'Main navigation' })
    .getByRole('link', { name: 'Sources and methodology', exact: true })
    .click();
  await expect(page).toHaveURL(`${origin}/sources?flow=exports`);
  await expectReviewContext(page, 'exports');
  await page.goBack();
  await expect(page).toHaveURL(`${origin}/countries/india?flow=exports`);
  await page.goBack();
  await expect(page).toHaveURL(`${origin}/products/09?flow=exports`);
  await page.goBack();
  await expect(page).toHaveURL(`${origin}/products/09?flow=imports`);
  await page.goForward();
  await expect(page).toHaveURL(`${origin}/products/09?flow=exports`);
  await page.reload();
  await expectReviewContext(page, 'exports');
});

test('keyboard-only flow selection and table navigation fit the viewport', async ({
  page,
}) => {
  await page.goto('/products/09?flow=imports');
  const flow = page.getByLabel('Trade flow', { exact: true });
  for (
    let tabs = 0;
    tabs < 12 &&
    !(await flow.evaluate((element) => element === document.activeElement));
    tabs++
  ) {
    await page.keyboard.press('Tab');
  }
  await expect(flow).toBeFocused();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Tab');
  await expect(
    page.getByRole('button', { name: 'Apply', exact: true }),
  ).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(`${origin}/products/09?flow=exports`);
  await expectReviewContext(page, 'exports');
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  const region = page
    .getByRole('region')
    .filter({ has: page.getByRole('table') })
    .first();
  await expect(region).toHaveAttribute('tabindex', '0');
  await region.focus();
  await expect(region).toBeFocused();
  const dimensions = await region.evaluate((element) => ({
    client: element.clientWidth,
    scroll: element.scrollWidth,
  }));
  if (dimensions.scroll > dimensions.client) {
    await page.keyboard.press('ArrowRight');
    await expect
      .poll(() => region.evaluate((element) => element.scrollLeft))
      .toBeGreaterThan(0);
  }
});

test('country and source flow controls preserve the current review page', async ({
  page,
}) => {
  for (const path of ['/countries/canada', '/sources']) {
    await page.goto(`${path}?flow=imports`);
    await page
      .getByLabel('Trade flow', { exact: true })
      .selectOption('exports');
    await page.getByRole('button', { name: 'Apply', exact: true }).click();
    await expect(page).toHaveURL(`${origin}${path}?flow=exports`);
    await expectReviewContext(page, 'exports');
    await page
      .getByRole('link', { name: 'Chapter profile', exact: true })
      .click();
    await expect(page).toHaveURL(`${origin}/products/09?flow=exports`);
  }
});

test('review responses are private, noindex and have no script or download surface', async ({
  page,
}) => {
  const response = await page.goto('/products/09?flow=imports');
  expect(response?.status()).toBe(200);
  const headers = response!.headers();
  expect(headers['cache-control']).toContain('no-store');
  expect(headers['x-robots-tag']).toContain('noindex');
  expect(headers['content-security-policy']).toContain("default-src 'none'");
  expect(headers['x-content-type-options']).toBe('nosniff');
  expect(headers['referrer-policy']).toBe('no-referrer');
  expect(headers['x-frame-options']).toBe('DENY');
  await expect(page.locator('a[download], script, iframe')).toHaveCount(0);
  const stylesheet = page.locator('link[rel="stylesheet"]');
  await expect(stylesheet).toHaveAttribute('href', '/review.css');
  const css = await page.request.get('/review.css');
  expect(css.status()).toBe(200);
  expect(css.headers()['content-type']).toContain('text/css');
  for (const path of [
    '/data/candidate.json',
    '/api/candidate',
    '/countries/germany?flow=imports',
  ]) {
    const unavailable = await page.goto(path);
    expect(unavailable?.status()).toBe(404);
    await expect(page.locator('body')).toContainText(
      'Unpublished local review',
    );
    await expect(page.locator('body')).toContainText('Fabricated test data');
    await page
      .getByRole('link', { name: 'Chapter profile', exact: true })
      .click();
    await expect(page).toHaveURL(/\/products\/09\?flow=imports$/);
  }
});

// This deliberate injection has its own transport guard: Playwright emits a
// request event even when CSP rejects it before a network route can run.
base.describe('enforced review CSP', () => {
  base.use({ javaScriptEnabled: true });

  base(
    'blocks inline and external scripts when the browser permits JavaScript',
    async ({ page }) => {
      const outbound: string[] = [];
      await page.route('https://untrusted.example.test/**', (route) => {
        outbound.push(route.request().url());
        return route.abort();
      });
      await page.goto('/products/09?flow=imports');
      await page.evaluate(() => {
        document.addEventListener('securitypolicyviolation', (event) => {
          document.body.dataset.blocked = `${document.body.dataset.blocked || ''}|${event.blockedURI}`;
        });
        const inline = document.createElement('script');
        inline.textContent = "document.body.dataset.injected = 'yes'";
        document.head.append(inline);
        const remote = document.createElement('script');
        remote.src = 'https://untrusted.example.test/review-csp.js';
        document.head.append(remote);
      });
      await expect(page.locator('body')).toHaveAttribute(
        'data-blocked',
        /inline/,
      );
      await expect(page.locator('body')).toHaveAttribute(
        'data-blocked',
        /untrusted\.example\.test/,
      );
      await expect(page.locator('body')).not.toHaveAttribute('data-injected');
      expect(outbound).toEqual([]);
      await page
        .getByLabel('Trade flow', { exact: true })
        .selectOption('exports');
      await page.getByRole('button', { name: 'Apply', exact: true }).click();
      await expect(page).toHaveURL(`${origin}/products/09?flow=exports`);
    },
  );
});

test('unsupported flows and duplicate filters show a recoverable bad request', async ({
  page,
}) => {
  for (const path of [
    '/products/09?flow=balance',
    '/countries/india?flow=imports&flow=exports',
  ]) {
    const response = await page.goto(path);
    expect(response?.status()).toBe(400);
    await expect(page.locator('body')).toContainText(
      'Unpublished local review',
    );
    await expect(page.locator('body')).toContainText('Fabricated test data');
    await page
      .getByRole('link', { name: 'Chapter profile', exact: true })
      .click();
    await expect(page).toHaveURL(/\/products\/09\?flow=imports$/);
  }
});
