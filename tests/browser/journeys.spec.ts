import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
const sample = JSON.parse(
  readFileSync(
    new URL('../fixtures/sample-release.json', import.meta.url),
    'utf8',
  ),
);
test('overview fits the viewport and search leads to a substantive product profile', async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(
    page.getByRole('heading', { name: 'A clearer view of US trade.' }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `.local/overview-${info.project.name}.png`,
    fullPage: false,
  });
  await page
    .getByRole('textbox', { name: 'Search a product or HS code' })
    .fill('coffee');
  await page.getByRole('button', { name: 'Explore' }).click();
  await expect(page.getByRole('status')).toContainText(
    '1 matching sample chapter',
  );
  await page.getByRole('link', { name: /HS 09 Coffee/ }).click();
  await expect(
    page.getByRole('heading', { name: 'Coffee, tea & spices', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(/General imports · customs value · Census basis/),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
test('the proposed strict CSP permits filtering without inline scripts', async ({
  page,
}) => {
  const policy = JSON.parse(
    readFileSync(
      new URL('../../infra/cloudfront/response-headers.json', import.meta.url),
      'utf8',
    ),
  ).SecurityHeadersConfig.ContentSecurityPolicy.ContentSecurityPolicy;
  const errors: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  await page.route('**/compare/', async (route) => {
    const response = await route.fetch();
    await route.fulfill({
      response,
      headers: { ...response.headers(), 'Content-Security-Policy': policy },
    });
  });
  await page.goto('/compare/');
  await page.getByLabel('Canada', { exact: true }).check();
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(page.locator('#result-table')).toContainText('Canada');
  expect(errors).toEqual([]);
});
test('comparisons preserve filters and unavailable baselines, and export sample metadata', async ({
  page,
}) => {
  await page.goto('/compare/');
  await expect(page.getByRole('status').first()).toContainText(
    'comparison is empty',
  );
  await page.getByLabel('India', { exact: true }).check();
  await page.getByLabel('Canada', { exact: true }).check();
  await page.getByLabel('Trade flow').selectOption('exports');
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(page).toHaveURL(/partners=canada%2Cindia/);
  await expect(page.locator('#result-table')).toContainText('Not defined');
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download selected CSV' }).click();
  const path = await (await download).path();
  expect(path).not.toBeNull();
  const csv = readFileSync(path!, 'utf8');
  expect(csv).toContain('"sample"');
  expect(csv).toContain('"2026-07"');
  expect(csv).toContain('FAS value');
  await page.reload();
  await expect(page.getByLabel('India', { exact: true })).toBeChecked();
  await expect(page.locator('#result-table')).toContainText('Canada');
  await page.goto('/compare/?period=2026-13');
  await expect(page.getByRole('status').first()).toContainText('not included');
  await expect(page.locator('#explore-result')).toBeHidden();
});
test('hostile source descriptions stay text and failed downloads keep selected state', async ({
  page,
}) => {
  const altered = structuredClone(sample);
  altered.partners.find((p: { id: string }) => p.id === 'canada').name =
    '<img src=x onerror=alert(1)>';
  await page.route('**/data/*.json', (route) =>
    route.fulfill({ json: altered }),
  );
  await page.addInitScript(() => {
    URL.createObjectURL = () => {
      throw new Error('download blocked');
    };
  });
  await page.goto('/compare/?partners=canada');
  await expect(page.locator('#result-table')).toContainText(
    '<img src=x onerror=alert(1)>',
  );
  expect(await page.locator('#result-table img').count()).toBe(0);
  await page.getByRole('button', { name: 'Download selected CSV' }).click();
  await expect(page.locator('#download-status')).toContainText(
    'could not be prepared',
  );
  await expect(page).toHaveURL(/partners=canada/);
});
test('failed datasets, no search matches and real 404 responses are explicit', async ({
  page,
}) => {
  await page.route('**/data/*.json', (route) => route.abort());
  await page.goto('/explore/?product=09');
  await expect(page.getByRole('status').first()).toContainText(
    'could not be loaded',
  );
  await expect(page.locator('#explore-result')).toBeHidden();
  await page.goto('/search/?q=unfindable');
  await expect(
    page.getByRole('heading', { name: 'No matching sample chapter' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Show all sample chapters' }).click();
  await expect(page.getByRole('status')).toContainText('4 matching');
  const response = await page.goto('/this-page-does-not-exist/');
  expect(response?.status()).toBe(404);
});
test('public profiles remain readable without JavaScript and need no third party resources', async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  const external: string[] = [];
  page.on('request', (request) => {
    if (new URL(request.url()).hostname !== '127.0.0.1')
      external.push(request.url());
  });
  await page.goto('http://127.0.0.1:4321/products/hs/HS2022/09/imports/');
  await expect(
    page.getByRole('heading', { name: 'Coffee, tea & spices', exact: true }),
  ).toBeVisible();
  await expect(page.getByRole('table').last()).toContainText('Canada');
  expect(external).toEqual([]);
  await context.close();
});
