import { defineConfig } from 'astro/config';
const site = process.env.SITE_URL || 'https://example.invalid';
const base = process.env.BASE_PATH || '/';
if (!/^\/(?:[a-zA-Z0-9_-]+\/)*$/.test(base))
  throw new Error(
    'BASE_PATH must be / or slash-delimited path segments with a trailing slash',
  );
const url = new URL(site);
if (
  url.protocol !== 'https:' ||
  url.username ||
  url.password ||
  url.search ||
  url.hash ||
  url.pathname !== '/'
)
  throw new Error('SITE_URL must be a clean HTTPS origin');
// A production switch cannot turn sample figures into official statistics.
if (process.env.PUBLICATION_MODE === 'production')
  throw new Error(
    'Production publication is disabled until live reconciliation, host checks and notices are verified. See docs/operations.md.',
  );
export default defineConfig({
  site: url.origin,
  base,
  output: 'static',
  trailingSlash: 'always',
  build: { format: 'directory', inlineStylesheets: 'never' },
  vite: { build: { assetsInlineLimit: 0 } },
  devToolbar: { enabled: false },
});
