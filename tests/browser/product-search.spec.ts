import { test, expect } from '@playwright/test';

const sitePath = (path: string) =>
  `${process.env.BASE_PATH || '/'}${path.replace(/^\//, '')}`;
const searchPath = (term: string) =>
  sitePath(`/search/?q=${encodeURIComponent(term)}`);

test('a detailed code offers broader parent coverage only after an explicit click', async ({
  page,
}) => {
  await page.goto(searchPath('090111'));
  const parent = page.getByRole('link', {
    name: /Explore broader HS 09 chapter/,
  });
  await expect(parent).toBeVisible();
  await expect(page.getByRole('status')).toContainText(
    /HS2 chapter totals only/,
  );
  await expect(page.getByRole('status')).toContainText(
    /cannot verify.*detailed code.*report its trade/,
  );
  await expect(
    page.locator('#product-results .product-card:visible'),
  ).toHaveCount(0);
  await expect(page.getByLabel('Product name or HS code')).toHaveValue(
    '090111',
  );
  expect(new URL(page.url()).searchParams.get('q')).toBe('090111');
  await expect(parent).toHaveAttribute(
    'href',
    sitePath('/products/hs/HS2022/09/imports/'),
  );
  await page.screenshot({
    path: `.local/product-search/detail-${test.info().project.name}.png`,
    fullPage: true,
  });
  await parent.click();
  await expect(page).toHaveURL(new RegExp('/products/hs/HS2022/09/imports/$'));
  await expect(
    page.getByRole('heading', { name: 'Coffee, tea & spices', exact: true }),
  ).toBeVisible();
});

test('exact chapter codes accept HS prefixes and preserve the leading zero', async ({
  page,
}) => {
  for (const term of ['09', 'HS09', 'hs 09']) {
    await page.goto(searchPath(term));
    await expect(
      page.locator('#product-results .product-card:visible'),
    ).toHaveCount(1);
    await expect(
      page.getByRole('link', { name: /HS 09 Coffee/ }),
    ).toBeVisible();
    await expect(page.getByLabel('Product name or HS code')).toHaveValue(term);
  }
});

test('unsupported detail levels never expose ordinary matching chapter cards', async ({
  page,
}) => {
  for (const term of ['0901', 'HS 090111', '09011100', 'hs0901110000']) {
    await page.goto(searchPath(term));
    await expect(
      page.getByRole('link', { name: /Explore broader HS 09 chapter/ }),
    ).toBeVisible();
    await expect(
      page.locator('#product-results .product-card:visible'),
    ).toHaveCount(0);
  }
});

test('missing parents and malformed codes explain limited coverage and recover', async ({
  page,
}) => {
  for (const term of [
    '990111',
    '9',
    '0',
    '009',
    '090',
    '09011',
    '0901111',
    'HS09coffee',
    '09-01',
    '090111x',
    'HS 09 01',
  ]) {
    await page.goto(searchPath(term));
    await expect(page.getByRole('status')).toContainText(
      /missing result does not mean.*zero/i,
    );
    await expect(
      page.locator('#product-results .product-card:visible'),
    ).toHaveCount(0);
    await expect(
      page.getByRole('link', { name: /Explore broader HS/ }),
    ).toHaveCount(0);
    if (term === '990111') {
      await expect(page.getByRole('status')).toContainText(
        /parent chapter HS 99.*not included/i,
      );
      await expect(page.getByRole('status')).toContainText(/cannot verify/);
    }
    await page
      .getByRole('button', { name: 'Show all sample chapters' })
      .click();
    await expect(
      page.locator('#product-results .product-card:visible'),
    ).toHaveCount(4);
    await expect(page.getByLabel('Product name or HS code')).toHaveValue('');
    expect(new URL(page.url()).searchParams.has('q')).toBe(false);
  }
});

test('ambiguous product names retain every match and ask the visitor to choose', async ({
  page,
}) => {
  await page.goto(searchPath('MACHINERY'));
  await expect(
    page.locator('#product-results .product-card:visible'),
  ).toHaveCount(2);
  await expect(
    page.getByRole('link', { name: /HS 84 Machinery/ }),
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: /HS 85 Electrical/ }),
  ).toBeVisible();
  await expect(page.getByRole('status')).toContainText(/choose a description/i);
  expect(new URL(page.url()).searchParams.get('q')).toBe('MACHINERY');
});

test('search restores normal and detail states through reload, back and forward without requests', async ({
  page,
}) => {
  await page.goto(searchPath('coffee'));
  await expect(
    page.locator('#product-results .product-card:visible'),
  ).toHaveCount(1);
  const requests: string[] = [];
  page.on('request', (request) => {
    // Chrome can refresh its icon on same-document history changes.
    if (new URL(request.url()).pathname !== sitePath('/favicon.svg')) {
      requests.push(request.url());
    }
  });
  await page.getByLabel('Product name or HS code').fill('090111');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(
    page.getByRole('link', { name: /Explore broader HS 09 chapter/ }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Show all sample chapters' }).click();
  await expect(
    page.locator('#product-results .product-card:visible'),
  ).toHaveCount(4);
  await page.goBack();
  await expect(page.getByLabel('Product name or HS code')).toHaveValue(
    '090111',
  );
  await expect(
    page.getByRole('link', { name: /Explore broader HS 09 chapter/ }),
  ).toBeVisible();
  await page.goBack();
  await expect(page.getByLabel('Product name or HS code')).toHaveValue(
    'coffee',
  );
  await expect(
    page.locator('#product-results .product-card:visible'),
  ).toHaveCount(1);
  await page.goForward();
  await expect(
    page.getByRole('link', { name: /Explore broader HS 09 chapter/ }),
  ).toBeVisible();
  expect(requests).toEqual([]);
  await page.reload();
  await expect(page.getByLabel('Product name or HS code')).toHaveValue(
    '090111',
  );
  await expect(
    page.getByRole('link', { name: /Explore broader HS 09 chapter/ }),
  ).toBeVisible();
});

test('external and submitted terms share a bounded URL state', async ({
  page,
}) => {
  const long = 'x'.repeat(150);
  await page.goto(searchPath(long));
  await expect(page.getByLabel('Product name or HS code')).toHaveValue(
    'x'.repeat(120),
  );
  expect(new URL(page.url()).searchParams.get('q')).toBe('x'.repeat(120));
  await page.reload();
  await expect(page.getByLabel('Product name or HS code')).toHaveValue(
    'x'.repeat(120),
  );
  await page
    .getByLabel('Product name or HS code')
    .evaluate((input: HTMLInputElement) => {
      input.value = 'y'.repeat(150);
    });
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await expect(page.getByLabel('Product name or HS code')).toHaveValue(
    'y'.repeat(120),
  );
  expect(new URL(page.url()).searchParams.get('q')).toBe('y'.repeat(120));
  await page.goBack();
  await expect(page.getByLabel('Product name or HS code')).toHaveValue(
    'x'.repeat(120),
  );
  await page.goForward();
  await expect(page.getByLabel('Product name or HS code')).toHaveValue(
    'y'.repeat(120),
  );
});

test('external CR and LF terms keep visible input, matching and URL equal through resubmission and reload', async ({
  page,
}) => {
  const cases = [
    { raw: '09\n0111', term: '090111', detail: true },
    { raw: '0\r\n9', term: '09', detail: false },
    { raw: 'H\rS \n09', term: 'HS 09', detail: false },
    { raw: 'cof\r\nfee', term: 'coffee', detail: false },
  ];
  for (const { raw, term, detail } of cases) {
    await page.goto(searchPath(raw));
    await expect(page.getByLabel('Product name or HS code')).toHaveValue(term);
    if (detail) {
      await expect(
        page.getByRole('link', { name: /Explore broader HS 09 chapter/ }),
      ).toBeVisible();
      await expect(page.getByRole('status')).toContainText(
        /cannot verify.*detailed code.*report its trade/,
      );
      await expect(
        page.locator('#product-results .product-card:visible'),
      ).toHaveCount(0);
    } else {
      await expect(
        page.locator('#product-results .product-card:visible'),
      ).toHaveCount(1);
      await expect(
        page.getByRole('link', { name: /HS 09 Coffee/ }),
      ).toBeVisible();
    }
    expect(new URL(page.url()).searchParams.get('q')).toBe(term);
    const status = await page.getByRole('status').textContent();
    await page.getByRole('button', { name: 'Search', exact: true }).click();
    await expect(page.getByLabel('Product name or HS code')).toHaveValue(term);
    await expect(page.getByRole('status')).toHaveText(status!);
    expect(new URL(page.url()).searchParams.get('q')).toBe(term);
    await page.reload();
    await expect(page.getByLabel('Product name or HS code')).toHaveValue(term);
    await expect(page.getByRole('status')).toHaveText(status!);
    expect(new URL(page.url()).searchParams.get('q')).toBe(term);
  }
});

test('hostile query text stays inert and visible through URL restoration', async ({
  page,
}) => {
  const hostile = '<img src=x onerror="document.body.dataset.injected=1">';
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(searchPath(hostile));
  await expect(page.getByLabel('Product name or HS code')).toHaveValue(hostile);
  await expect(
    page.locator('#search-summary img, #empty-search img'),
  ).toHaveCount(0);
  await expect(page.locator('body')).not.toHaveAttribute('data-injected');
  await expect(
    page.locator('#product-results .product-card:visible'),
  ).toHaveCount(0);
  expect(new URL(page.url()).searchParams.get('q')).toBe(hostile);
  expect(errors).toEqual([]);
});

test('the sample directory remains readable with JavaScript disabled', async ({
  browser,
}) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  try {
    const page = await context.newPage();
    await page.goto(`http://127.0.0.1:4321${searchPath('090111')}`);
    await expect(
      page.locator('#product-results .product-card:visible'),
    ).toHaveCount(4);
    await expect(
      page.getByRole('link', { name: /HS 09 Coffee/ }),
    ).toBeVisible();
    await expect(page.getByRole('status')).toContainText(/4.*sample chapters/);
    await expect(
      page.getByText('Explore US imports, exports and trading partners.', {
        exact: true,
      }),
    ).toHaveCount(4);
  } finally {
    await context.close();
  }
});
