# Public preview implementation status

Implementation date: 1 October 2026 (local date). Branch: `feat/public-mvp`.

Update: PR #1 was merged into `main` with explicit user approval. GitHub-first development is now documented in [GitHub development](github-development.md); AWS remains deferred. The subsequent preview-workflow increment adds a tested browser CSP, GitHub project-path browser checks and private build artifacts. GitHub rejected Pages setup under the current repository plan, so no hosted preview is claimed. The original evidence below describes the public-preview increment at its completion; current provider and ingestion results are recorded separately.

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

Before final review, 7 Node contract tests, 11 Python source/store/reconciliation tests, and 12 desktop/mobile Playwright journeys passed locally. Astro checks reported zero errors, warnings or hints. Both root and `/trade/` builds verified 30 HTML pages and their internal links. Browser tests include escaped hostile source text, download failure, failed data loading, missing baselines, invalid URLs, actual HTTP 404, no-JavaScript profiles and compatibility with the proposed CSP. The dependency installation and production dependency audits reported zero known vulnerabilities at the time of checking; that result is not a complete security audit. The [licence inventory](dependency-licences.md) records the lockfile's declared licences, including copyleft transitive build dependencies.

An independent whole-branch review found encoded credential reflection and incomplete response deadline enforcement, plus percentage rounding, large chart ticks and stale clipboard fallback issues. Each received a failing regression test before correction. The source reader now rejects keys after JSON decoding and uses an absolute socket watchdog through both response headers and detached bodies. Displayed percentage ratios round once using integer arithmetic; chart ticks accept the full declared value range; changing filters clears obsolete share links. Final post-review totals are recorded below after the complete suite.

Final local result: **9 Node tests + 13 Python tests + 14 browser tests = 36 passing tests**. Astro reported zero errors, warnings or hints; the build verified 30 HTML pages, internal links, noindex, artifact secret patterns and 4,441 bytes of compressed JavaScript. A production-mode build was deliberately attempted and correctly rejected. Root and subpath output checks passed. All five review findings were addressed; no review findings were deferred. Remote GitHub Actions and real Census acquisition have not run at the time of this local receipt.

Preview screenshots are generated under ignored `.local/` by browser tests. The app's interactive browser connection timed out; isolated headless Chrome was used for browser testing and screenshot inspection instead. Desktop and mobile screenshots were inspected; no horizontal page overflow was observed at the tested sizes. This is not a full screen-reader or WCAG conformance audit.

## Not yet verified or deployed

- Live Census responses, zero markers/default dimensions, all-partner/classification inventory, actual official reconciliation and annual revisions.
- Full public release assembly and production activation, private raw history, backfill orchestration, freshness scheduling/notifications and object-store backup restoration.
- CloudFront/S3 provisioning, commercial terms acceptance, DNS/TLS, deployed security headers, custom 404 routing, provider log delivery/retention and bill measurements.
- Actual Excel/LibreOffice import behavior beyond tested CSV encoding.
- Production privacy notices, company identity/contact, sponsor arrangements, and feature-specific jurisdiction/tax review.
- Accounts, subscriptions, private workspaces, alerts and payment integration (design only).

The local store's atomic filesystem tests do not prove atomic cloud activation. The proposed CSP can be tested in a local browser, but host enforcement requires real deployment checks. Production publication remains blocked to keep these distinctions explicit.

## Implementation decisions and review scope

- Used a manual sibling worktree because the app's native tool targeted a non-repository parent. Cost: this checkout is not a managed app attachment and must be retained for local work.
- Kept a labelled synthetic preview until live reconciliation is available. Cost: it is not an official-data launch.
- Started with standard-library Python and JSON. Cost: bulk Parquet/history storage remains future work.
- Kept the single Astro app at repository root. Cost: introduce a workspace layout when a backend is added.
- Used a Windows-native temporary execution ledger instead of Unix workflow helpers. No product behavior depends on it.
- Used isolated headless Chrome after the in-app browser timed out. Cost: the in-app interactive preview itself remains unverified.
- Treated the three functional review findings as material because wrong displayed comparisons, contract-valid build failures and stale shared views violate the public analytics journey; fixed them in the same regression-tested pass as the two acquisition findings.
- Deferred judging live data semantics, provider enforcement/restoration/terms, backend billing, actual spreadsheet application imports and full accessibility conformance because those systems/evidence are not present. Each remains a named launch or expansion gate; no compliance or production-readiness claim is made.
