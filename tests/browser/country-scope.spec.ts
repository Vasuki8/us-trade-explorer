import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';

const sitePath = (path: string) =>
  `${process.env.BASE_PATH || '/'}${path.replace(/^\//, '')}`;

test('country profile explore carries the same included chapter total', async ({
  page,
}) => {
  await page.goto(sitePath('/countries/canada/imports/'));
  await page.getByRole('link', { name: 'Change period & explore' }).click();
  const canada = page
    .locator('#result-table tbody tr')
    .filter({ hasText: 'Canada' });
  await expect(canada).toContainText('$20,742,720,000');
  await expect(canada).toContainText('+10.7%');
  await expect(page).toHaveURL(/product=all/);
  await expect(
    page.getByRole('combobox', { name: 'Product', exact: true }),
  ).toHaveValue('all');
  await expect(page.locator('#result-table tbody tr')).toHaveCount(1);
  await expect(page.locator('#result-scope')).toContainText(
    /4.*09.*84.*85.*87/,
  );
  await expect(page.locator('#result-scope')).toContainText(
    /not a country total/i,
  );
  await expect(page.locator('#result-scope')).toContainText(
    /CSV.*chapter.*selected month/i,
  );
  await expect(
    page.locator('select[name=product] option').last(),
  ).toHaveAttribute('value', 'all');
});

test('country profile comparison sums exports and keeps the missing prior year undefined', async ({
  page,
}) => {
  await page.goto(sitePath('/countries/canada/exports/'));
  await page.getByRole('link', { name: 'Compare markets' }).click();
  await expect(page.locator('#result-table')).toContainText('$6,222,816,000');
  await expect(page).toHaveURL(/product=all/);
  await page.getByLabel('India', { exact: true }).check();
  await page.getByRole('button', { name: 'Apply filters' }).click();
  const india = page
    .locator('#result-table tbody tr')
    .filter({ hasText: 'India' });
  await expect(india).toContainText('$6,229,507,200');
  await expect(india).toContainText('Not defined');
  await expect(page.locator('#result-table tbody tr')).toHaveCount(2);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `.local/country-scope/aggregate-${process.env.BASE_PATH ? 'subpath' : 'root'}-${test.info().project.name}.png`,
    fullPage: true,
  });

  const downloading = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download selected CSV' }).click();
  const download = await downloading;
  const contents = readFileSync((await download.path())!, 'utf8');
  const lines = contents.trim().split('\r\n');
  expect(lines).toHaveLength(9);
  expect(contents).not.toContain('"all"');
  expect(contents).not.toContain('"2025-07"');
  expect(contents).not.toContain('"World"');
  for (const country of ['Canada', 'India']) {
    const rows = lines.slice(1).filter((line) => line.includes(`"${country}"`));
    expect(rows).toHaveLength(4);
    expect(rows.map((line) => line.split(',')[2])).toEqual([
      '"09"',
      '"84"',
      '"85"',
      '"87"',
    ]);
    expect(rows.every((line) => line.includes('"exports","2026-07"'))).toBe(
      true,
    );
  }
  expect(contents).toContain(
    '"09","Coffee, tea & spices","Canada","exports","2026-07",107136000,"reported"',
  );
  expect(contents).toContain(
    '"09","Coffee, tea & spices","India","exports","2026-07",107251200,"reported"',
  );
});

test('all chapter scope survives chapter switching, history, reload and sharing', async ({
  page,
}) => {
  await page.addInitScript(() => {
    navigator.clipboard.writeText = async () => {
      throw new Error('denied');
    };
  });
  await page.goto(sitePath('/explore/?product=all&partners=canada'));
  await expect(page.locator('#result-table')).toContainText('$20,742,720,000');
  await page
    .getByRole('combobox', { name: 'Product', exact: true })
    .selectOption('09');
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(page.locator('#result-table')).toContainText('$357,120,000');
  await expect(page.locator('#result-table')).toContainText('reported');
  await page.goBack();
  await expect(
    page.getByRole('combobox', { name: 'Product', exact: true }),
  ).toHaveValue('all');
  await expect(page.locator('#result-table')).toContainText('$20,742,720,000');
  await page.goForward();
  await expect(
    page.getByRole('combobox', { name: 'Product', exact: true }),
  ).toHaveValue('09');
  await page
    .getByRole('combobox', { name: 'Product', exact: true })
    .selectOption('all');
  await page
    .getByRole('combobox', { name: 'Month', exact: true })
    .selectOption('2025-07');
  await page.getByRole('button', { name: 'Apply filters' }).click();
  await expect(page.locator('#result-table')).toContainText('$18,735,360,000');
  await page.reload();
  await expect(
    page.getByRole('combobox', { name: 'Product', exact: true }),
  ).toHaveValue('all');
  await expect(
    page.getByRole('combobox', { name: 'Month', exact: true }),
  ).toHaveValue('2025-07');
  await expect(page.locator('#result-table')).toContainText('$18,735,360,000');
  await page.getByRole('button', { name: 'Copy link' }).click();
  const shared = await page
    .getByRole('textbox', { name: 'Shareable link' })
    .inputValue();
  const params = new URL(shared).searchParams;
  expect(params.get('product')).toBe('all');
  expect(params.get('partners')).toBe('canada');
  expect(params.get('period')).toBe('2025-07');
  expect(params.get('release')).toBe('sample-2026-07-v1');
  await page.goto(shared);
  await expect(page.locator('#result-table')).toContainText('$18,735,360,000');
});

test('omitted product and product profile links retain the chapter view', async ({
  page,
}) => {
  await page.goto(sitePath('/explore/?partners=canada'));
  await expect(
    page.getByRole('combobox', { name: 'Product', exact: true }),
  ).toHaveValue('09');
  await expect(page.locator('#result-table')).toContainText('$357,120,000');
  await page.goto(sitePath('/products/hs/HS2022/85/imports/'));
  await page.getByRole('link', { name: 'Change period & explore' }).click();
  await expect(page).toHaveURL(/product=85/);
  await expect(
    page.getByRole('combobox', { name: 'Product', exact: true }),
  ).toHaveValue('85');
  await page.goto(sitePath('/products/hs/HS2022/85/imports/'));
  await page.getByRole('link', { name: 'Compare markets' }).click();
  await expect(page).toHaveURL(/product=85/);
});

test('country profile links expose included scope without JavaScript', async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto(
    `http://127.0.0.1:4321${sitePath('/countries/canada/imports/')}`,
  );
  await expect(page.getByRole('table').last()).toContainText(
    'Coffee, tea & spices',
  );
  for (const name of ['Change period & explore', 'Compare markets']) {
    const target = await page.getByRole('link', { name }).getAttribute('href');
    expect(new URL(target!, page.url()).searchParams.get('product')).toBe(
      'all',
    );
  }
  await context.close();
});
