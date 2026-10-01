# Phased delivery and acceptance plan

This is the requested preimplementation roadmap. It is not a claim that the listed features or controls exist. Build estimates below are planning ranges for one experienced engineer and exclude provider approval and legal/accounting turnaround.

## Phase 0 — Decisions and launch eligibility

Deliver the six design artifacts, identify the Gujarat operator, select a domain and hosting plan, appoint privacy/incident/grievance contacts, obtain a Census key and establish the release/source licence register. Confirm the actual monthly budget, exact European launch countries, log scope/retention and payment availability. Preserve the user's global target-market objective while sequencing country-specific activation where review is incomplete.

Exit: recorded architecture decision, operator identity, hosting/logging agreement, source scope, privacy inventory and country/feature launch matrix. No claim that a cookie-free site is exempt from privacy law. No fake production data while awaiting a source key.

## Phase 1 — Reproducible data foundation

Estimated implementation effort: 3–5 working days after source access.

- Versioned schemas/source allowlist, fixtures, locked Python dependencies and isolated Census connector.
- Initial HS2/partner/month partitions for a 60-month window; historic bootstrap in bounded manual shards.
- Immutable raw/Parquet archive, release manifest, metrics and provenance.
- Ingestion/validation CI jobs with least privilege, timeouts, retries and no production promotion from pull requests.
- Release calendar, freshness state and recovery commands.

Exit: representative real data reconciles to the correct official basis; repetition makes no duplicates; malformed/partial data cannot publish; annual revision replay is demonstrated; secret canaries stay out of logs and artifacts. If official control totals cannot be obtained on the same basis, record and resolve that limitation before treating aggregate reconciliation as passed.

## Phase 2 — Public website MVP

Estimated effort: 5–8 working days after the data contract stabilizes.

- Astro routes for all seven sections, prerendered profiles/tables and controlled indexable coverage.
- Product search, imports/exports, period selection, 2–4-series comparisons, source inspection, shareable exploration URLs and safe CSV downloads.
- Light responsive interface and all specified empty/missing/suppressed/stale/download failure states.
- Canonicals, redirects, sitemaps, crawlable internal links and correct HTTP error behavior.
- Portability configuration and reserved, inactive private-app boundary.

Exit: direct-entry journeys work without visiting home; default profiles remain useful with JavaScript disabled; changes match fixtures and selected live records; keyboard/screen-reader checks and representative mobile layout pass; URL state round-trips; unsafe text is inert and exported text is safe. No authentication, billing or alert delivery in this phase.

## Phase 3 — Commercial public launch

Estimated effort: 2–4 working days plus external reviews.

- Provision the chosen host through reviewed infrastructure code and short-lived deployment credentials.
- Enable security headers, selected access/security logs, India archive, independent freshness monitoring, cost alerts and backups.
- Publish notices only after comparing them with real network requests and provider settings.
- Offer direct sponsorship placements, with an ad policy and written creative/content rights. No programmatic tags by default.
- Complete launch-country legal reviews required even for public traffic, especially targeted EU/UK/China processing and India duties.

Exit: one deliberately failed update leaves the prior release usable; a backup restores within the target; production HTTPS, canonical, 404 and header checks pass; logs reach the intended destination and expire correctly; data is fresh or accurately marked stale; privacy contacts work. Record exclusions/limitations in the launch receipt.

## Phase 4 — Audience and data-depth expansion

Measure aggregate readership, search demand and sponsor interest using the least collection necessary. Increase HS4 coverage only after timing and payload tests. Improve curated comparison pages and source explanations. Establish editorial correction handling. A reviewed ad network or analytics tool is a separate privacy/security change with consent and transfer tests, not a marketing-only toggle.

Exit: measured utility and cost justify expansion; no uncontrolled indexable filter explosion; sponsor revenue is reported as actual revenue rather than a forecast.

## Phase 5 — Accounts and private workspaces

Implement managed identity, sessions, workspace API, PostgreSQL tenant model, saved queries/watchlists, private storage, export/deletion, email preference handling and audited administration. Keep public pages on the static architecture. Select processor/identity/email providers only after India availability, contracts, transfer, retention and country checks.

Exit: cross-user read/write/delete/export tests fail safely; session/CSRF/rate-limit checks pass; account deletion and backup expiry are verified; private content cannot enter a static build, sitemap, source map, public bucket or CDN cache. Workspace value is proven before charging consumers.

## Phase 6 — Subscriptions, alerts and reports

Add a complete offer and country-aware checkout, hosted payment flow, signed idempotent webhooks, entitlement state machine, billing portal/cancellation and durable receipts. Add queued release-aware alerts and reports with idempotency, quotas and authorization. Localize legally required disclosures and consumer support before activating a market. Price and actual terms remain a separate business decision.

Exit: duplicate/out-of-order/forged events, failed renewal, expired grace, cancellation, refund, dispute, interrupted checkout and missed-webhook recovery all pass. Confirm RBI recurring-payment behavior, applicable notice timing, tax/invoice obligations and hosted-provider responsibilities. Validate public profiles remain available after cancellation and to non-subscribers.

## Evidence to retain

| Gate | Test evidence |
|---|---|
| Data accuracy | Control source, period/basis comparison, residual report and approval for any documented exception |
| Release integrity | Kill/retry trace, immutable hashes, failed-candidate quarantine and previous-release HTTP/data checks |
| Secret boundary | Canary scan of tracked files, build output, CSVs, logs, archives, source maps and workflow evidence |
| Rendering/download safety | Malicious strings through every render/export path; real spreadsheet import check |
| Public/private boundary | Anonymous request matrix and build allowlist inspection, repeated when backend appears |
| SEO | Rendered HTML inspection, crawler route test, canonical/base-path test, sitemap and true-404 check |
| Accessibility/performance | Automated audit plus manual keyboard/screen-reader and mobile/zoom checks; payload and layout-shift budgets |
| Hosting | Actual headers/TLS, preview restriction, log destination/retention, rollback and backup restoration |
| Privacy/consent | Browser request inventory before consent/after reject/after withdrawal; deletion and retention evidence |
| Subscription | Processor test-mode transitions plus controlled live checkout/cancel/refund acceptance when authorized |

Do not add tests merely to mirror a low-impact implementation detail. Prioritize failures that could publish wrong data, expose information, charge incorrectly or prevent recovery. Failed gates block the affected feature, not unrelated documentation or local UI work.

## Suggested repository layout

```text
docs/design/                 approved architecture and decision history
apps/web/                    static public site
packages/contracts/          versioned public schema and query model
pipeline/                    fetch, validate, normalize, metrics
sources/                     source registry, metadata contracts, calendar
releases/                    small immutable manifest and deployment receipts
tests/fixtures/              synthetic and small permitted reference cases
infra/                       host, IAM, logs, backup and deployment adapters
.github/workflows/           separated checks, ingest, build and publish
```

Later add `apps/api/`, `workers/` and private database migrations. Large historical files, `.env`, raw logs, downloaded packages, build output and private records never enter Git history. Use object storage and immutable content-addressed references instead. The repository remains the source of truth for how data is acquired, transformed and published.

## Present verification status

Design and official-source research completed; repository confirmed and cloned. Document checks verified seven Markdown files, four Mermaid diagram blocks, balanced code fences and all six internal document links. No generic TODO/FIXME/TBD markers or common credential patterns were found. Company/price/provider placeholders are intentionally labelled unpublished draft material. Mermaid visual rendering has not been independently tested.

Runtime tests require implementation, credentials and a host; no application test or deployed-control pass is claimed. The legal matrix is a scoped applicability assessment with named launch reviews, not universal legal certification. Budget and traffic assumptions require measurement after the first real dataset and deployment.
