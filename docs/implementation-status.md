# Public preview implementation status

Implementation date: 1 October 2026 (local date). Branch: `feat/public-mvp`.

## Implemented

- Astro static public website: overview, searchable product directory, product profiles for both flows, country directory/profiles, comparisons, interactive exploration, changes, sources/methodology, release record, status, preview privacy and a real 404 page.
- Light responsive interface with system fonts, no external visual assets, semantic tables, keyboard-focus indicators, labelled controls, accessible chart data tables and usable static profiles without JavaScript.
- Shareable flow/month/product/country/release filters, missing-data and empty-comparison states, safe selected CSV export, full sample CSV and metadata JSON.
- Strict public release contract, unknown-field rejection, exact dollar calculations, explicit missingness, schema/relationship/coverage checks and CSV formula neutralization.
- Fixed-host isolated Census candidate adapter, bounded requests/retries, no redirects, sanitized failures, secret-reflection rejection and source hashes. No credentials enter the public build.
- Local immutable release store and checksum-verified rollback model. A candidate does not automatically become a public release.
- Read-only PR checks without secrets, pinned Actions, bounded workflow times, manual main-only acquisition using a separate environment, locked dependencies and Dependabot configuration.
- Configurable origin/base path, canonical URLs, preview noindex, intentionally empty sample sitemap, build artifact/link/size checks and proposed CloudFront security headers.

## Deliberate boundaries

The executable UI uses **synthetic data only**, covering four HS2 chapters, five partner countries plus illustrative world totals, and 25 monthly periods. This is narrower than the live MVP's planned 60-month full HS2 coverage. The real Census key is available to the user but has not been used in this checkout. Official dates and live freshness are not invented.

The frontend resides at repository root `src/` rather than `apps/web/` to keep the single-application toolchain small. Shared contracts and the Python pipeline have separate directories. Move the web app into a workspace when a second application actually exists. Python standard-library JSON storage is implemented first; DuckDB/Parquet and raw historical object storage remain the next ingestion expansion.

## Verification evidence

Verified locally: 7 Node contract tests, 11 Python source/store/reconciliation tests, and 12 desktop/mobile Playwright journeys. Astro checks reported zero errors, warnings or hints. Both root and `/trade/` builds verified 30 HTML pages and their internal links; compressed JavaScript totaled 4,405 bytes. Browser tests include escaped hostile source text, download failure, failed data loading, missing baselines, invalid URLs, actual HTTP 404, no-JavaScript profiles and compatibility with the proposed CSP. The dependency installation audit reported zero known vulnerabilities at the time of installation; that result is not a complete security audit.

Preview screenshots are generated under ignored `.local/` by browser tests. The app's interactive browser connection timed out; isolated headless Chrome was used for browser testing and screenshot inspection instead. Desktop and mobile screenshots were inspected; no horizontal page overflow was observed at the tested sizes. This is not a full screen-reader or WCAG conformance audit.

## Not yet verified or deployed

- Live Census responses, zero markers/default dimensions, all-partner/classification inventory, actual official reconciliation and annual revisions.
- Full public release assembly and production activation, private raw history, backfill orchestration, freshness scheduling/notifications and object-store backup restoration.
- CloudFront/S3 provisioning, commercial terms acceptance, DNS/TLS, deployed security headers, custom 404 routing, provider log delivery/retention and bill measurements.
- Actual Excel/LibreOffice import behavior beyond tested CSV encoding.
- Production privacy notices, company identity/contact, sponsor arrangements, and feature-specific jurisdiction/tax review.
- Accounts, subscriptions, private workspaces, alerts and payment integration (design only).

The local store's atomic filesystem tests do not prove atomic cloud activation. The proposed CSP can be tested in a local browser, but host enforcement requires real deployment checks. Production publication remains blocked to keep these distinctions explicit.
