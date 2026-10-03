import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const sitePath = (path: string) =>
  `${process.env.BASE_PATH || '/'}${path.replace(/^\//, '')}`;

test('India profile explains missing prior-year chapter coverage beside its undefined percentage', async ({
  page,
}) => {
  await page.goto(sitePath('/countries/india/exports/'));
  const metric = page.locator('.stat').filter({ hasText: 'YEAR OVER YEAR' });
  await expect(metric).toContainText('Not defined');
  await expect(
    metric.getByText(
      /prior-year value unavailable for one or more included chapters/i,
    ),
  ).toBeVisible({ timeout: 5000 });
  const coffee = page
    .getByRole('row')
    .filter({ hasText: 'Coffee, tea & spices' });
  await expect(coffee.getByRole('cell').nth(1)).toContainText(
    /Not defined.*Prior-year value unavailable/,
  );
  await expect(coffee.locator('.change-reason')).toBeVisible();
});

test('prerendered country and product explanations are visible without JavaScript', async ({
  browser,
  page,
}) => {
  const context = await browser.newContext({
    javaScriptEnabled: false,
    viewport: page.viewportSize()!,
  });
  const staticPage = await context.newPage();
  try {
    await staticPage.goto(
      `http://127.0.0.1:4321${sitePath('/countries/india/exports/')}`,
    );
    const metric = staticPage
      .locator('.stat')
      .filter({ hasText: 'YEAR OVER YEAR' });
    await expect(metric.locator('.change-reason')).toBeVisible();
    await expect(metric).toContainText(
      /Not defined.*Prior-year value unavailable for one or more included chapters/,
    );
    expect(
      await staticPage.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await staticPage.screenshot({
      path: `.local/yoy-explanations/static-${process.env.BASE_PATH ? 'subpath' : 'root'}-${test.info().project.name}.png`,
      fullPage: true,
    });
    await staticPage.goto(
      `http://127.0.0.1:4321${sitePath('/products/hs/HS2022/09/exports/')}`,
    );
    const india = staticPage.getByRole('row').filter({ hasText: 'India' });
    await expect(india.getByRole('cell').nth(1)).toContainText(
      /Not defined.*Prior-year value unavailable/,
    );
    await expect(india.locator('.change-reason')).toBeVisible();
    await expect(india).not.toContainText('for one or more included chapters');
  } finally {
    await context.close();
  }
});

test('explorer reasons follow period, coverage and history while detail CSV stays unchanged', async ({
  page,
}) => {
  await page.addInitScript(() => {
    navigator.clipboard.writeText = async () => {
      throw new Error('denied');
    };
  });
  await page.goto(
    sitePath('/explore/?product=09&partners=india&flow=exports&period=2026-07'),
  );
  const table = page.locator('#result-table');
  const reason = table.locator('.change-reason');
  await expect(reason).toHaveText('Prior-year value unavailable');
  await expect(reason).toBeVisible();
  await expect(
    table.getByRole('row').last().getByRole('cell').nth(1),
  ).toContainText(/Not defined.*Prior-year value unavailable/);

  const apply = () =>
    page.getByRole('button', { name: 'Apply filters' }).click();
  const product = page.getByRole('combobox', { name: 'Product', exact: true });
  const period = page.getByRole('combobox', { name: 'Month', exact: true });
  await period.selectOption('2025-07');
  await apply();
  await expect(reason).toHaveText('Current value unavailable');
  await expect(table).not.toContainText('Prior-year value unavailable');
  await expect(table).toContainText('not available');
  await product.selectOption('all');
  await apply();
  await expect(reason).toHaveText(
    'Current value unavailable for one or more included chapters',
  );
  await expect(table).toContainText('Unavailable chapter sum');
  await period.selectOption('2024-07');
  await apply();
  await expect(reason).toHaveText(
    'Prior-year month is not included in this release',
  );
  await expect(table).not.toContainText('for one or more included chapters');
  await period.selectOption('2026-07');
  await apply();
  await expect(reason).toHaveText(
    'Prior-year value unavailable for one or more included chapters',
  );
  await expect(table).toContainText('$6,229,507,200');
  await expect(page.locator('#result-scope')).toContainText(
    'not a country total',
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect(
    await table.evaluate((el) => {
      const bounds = el.getBoundingClientRect();
      return bounds.left >= 0 && bounds.right <= innerWidth;
    }),
  ).toBe(true);
  // The table intentionally scrolls on narrow screens; reveal the YoY cell.
  await reason.scrollIntoViewIfNeeded();
  await page.screenshot({
    path: `.local/yoy-explanations/dynamic-${process.env.BASE_PATH ? 'subpath' : 'root'}-${test.info().project.name}.png`,
    fullPage: true,
  });

  await page.getByLabel('India', { exact: true }).uncheck();
  await page.getByLabel('Canada', { exact: true }).check();
  await apply();
  await expect(table).toContainText('+10.7%');
  await expect(reason).toHaveCount(0);
  await expect(table).not.toContainText('Not defined');
  await page.goBack();
  await expect(reason).toHaveText(
    'Prior-year value unavailable for one or more included chapters',
  );
  await page.goForward();
  await expect(reason).toHaveCount(0);
  await page.reload();
  await expect(table).toContainText('+10.7%');
  await expect(reason).toHaveCount(0);
  await page.goBack();
  await expect(reason).toHaveText(
    'Prior-year value unavailable for one or more included chapters',
  );
  await page.getByRole('button', { name: 'Copy link' }).click();
  const shared = await page
    .getByRole('textbox', { name: 'Shareable link' })
    .inputValue();
  expect(new URL(shared).searchParams.get('product')).toBe('all');
  expect(new URL(shared).searchParams.get('period')).toBe('2026-07');
  await page.goto(shared);
  await expect(reason).toHaveText(
    'Prior-year value unavailable for one or more included chapters',
  );
  const downloading = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download selected CSV' }).click();
  const download = await downloading;
  const contents = readFileSync((await download.path())!, 'utf8');
  expect(contents.trim().split('\r\n')).toHaveLength(5);
  expect(contents).toContain(
    '"09","Coffee, tea & spices","India","exports","2026-07",107251200,"reported"',
  );
  expect(contents).not.toMatch(
    /Not defined|unavailable:|reason|"all"|"World"|"2025-07"/,
  );
});

test('comparison keeps reasons beside the affected partner only', async ({
  page,
}) => {
  await page.goto(
    sitePath(
      '/compare/?product=all&partners=canada,india&flow=exports&period=2026-07',
    ),
  );
  const rows = page.locator('#result-table tbody tr');
  await expect(
    rows.filter({ hasText: 'India' }).locator('.change-reason'),
  ).toBeVisible();
  await expect(rows.filter({ hasText: 'India' })).toContainText(
    'Prior-year value unavailable for one or more included chapters',
  );
  await expect(rows.filter({ hasText: 'Canada' })).toContainText('+10.7%');
  await expect(
    rows.filter({ hasText: 'Canada' }).locator('.change-reason'),
  ).toHaveCount(0);
});
