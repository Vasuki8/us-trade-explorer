import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/review-browser',
  outputDir: './.local/research-review/test-results',
  fullyParallel: true,
  workers: 2,
  timeout: 30000,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:4323',
    headless: true,
    javaScriptEnabled: false,
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1440, height: 1000 } } },
    {
      name: 'mobile',
      use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' },
    },
  ],
  webServer: {
    command: 'node tools/research-review/server.ts --fixture --port 4323',
    url: 'http://127.0.0.1:4323/products/09?flow=imports',
    reuseExistingServer: false,
    timeout: 10000,
  },
});
