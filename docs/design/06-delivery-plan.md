# Phased delivery and acceptance plan

This is a roadmap, not a claim that the listed features or controls exist. The [permanent instructions](../../AGENTS.md) §31 and [2 October decision](../decisions/2026-10-02-operating-model.md) set the current order: official ingestion, coverage/validation, definitions/provenance and verified data replacement before feature expansion. The agent owns technical delivery; the owner decides material business consequences. Older build estimates below are planning ranges, not deadlines or grounds to skip validation.

## Phase 0 — Decisions and launch eligibility

Maintain the six design artifacts, source/licence register, safe existing Census credential boundary and documented operating model. Do not block reversible data engineering on unchosen paid providers. Before public launch, resolve the Gujarat operator's identity/contacts, authorized domain/host, actual budget, exact European launch countries and applicable log scope/retention. Payment availability is a later-phase question. Preserve global target-market intent while sequencing country-specific activation where review is incomplete.

Development prerequisites: recorded direction, safe source access and scope, privacy/source inventory and known blockers. Operator identity, hosting/logging agreements and country/feature reviews remain launch gates rather than permission to provision services now. No claim that a cookie-free site is exempt from privacy law. No fake production data while awaiting source evidence.

## Phase 1 — Reproducible data foundation

Current milestone: July 2026 / HS2 09 archived acquisition/discovery/diagnostics exist; next resolve period-effective partner inventory, applicable import/export classification and official revision-vintage evidence before generalizing or building a publication producer. The [coverage review](../census-coverage-review.md) lists outstanding approval evidence. Exact residuals alone are insufficient.

Estimated implementation effort: 3–5 working days after source access.

- Versioned schemas/source allowlist, fixtures, locked Python dependencies and isolated Census connector.
- Initial HS2/partner/month partitions for a 60-month window; historic bootstrap in bounded manual shards.
- Immutable raw and appropriate analytical objects, release manifest, metrics and provenance; introduce Parquet/DuckDB when justified rather than installing infrastructure for its own sake.
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

## Phase 3 — Verified public launch

Estimated effort: 2–4 working days plus external reviews.

- Provision the chosen host through reviewed infrastructure code and short-lived deployment credentials.
- Enable security headers, selected access/security logs, India archive, independent freshness monitoring, cost alerts and backups.
- Publish notices only after comparing them with real network requests and provider settings.
- Grow useful organic research first; advertising is not a launch prerequisite. Any later sponsorship, analytics or network integration needs explicit business/privacy approval and verified operating practices.
- Complete launch-country legal reviews required even for public traffic, especially targeted EU/UK/China processing and India duties.

Exit: one deliberately failed update leaves the prior release usable; a backup restores within the target; production HTTPS, canonical, 404 and header checks pass; logs reach the intended destination and expire correctly; data is fresh or accurately marked stale; privacy contacts work. Record exclusions/limitations in the launch receipt.

## Phase 4 — Audience, data depth and local research

Expand overview/product/country analysis in AGENTS.md priority order: comparable changes and contributions, coverage-qualified concentration, validated quantities and historical warnings. Increase HS depth only after classification, data-volume and payload tests. Improve curated comparisons and source explanations; maintain editorial corrections. Prefer user-requested browser-local saved products/countries/baskets/views without accounts solely for saving, preventing category/descendant double counting and providing clear/export behavior. Any aggregate readership/analytics or later advertising collection requires its actual privacy/business assessment and authorization; do not create a vendor integration to measure demand automatically.

Exit: useful analysis and justified costs, no uncontrolled indexable filter explosion, safe reusable local research and accurate coverage. Ads are optional later work; any revenue must be reported as actual rather than forecast.

## Phase 5 — Accounts and private workspaces

Only after the product phase and explicit account/provider approval justify it, implement secure identity/sessions, server-authorized workspace API and tenant records, cross-device saved queries/watchlists, private storage, export/deletion and audited administration. Choose a fitting small application store then; D1 may fit metadata, while PostgreSQL/queues need demonstrated requirements. Keep public pages static and first-phase saving browser-local. Processor/identity/email services require business approval and India availability, contract, transfer, retention and country checks before activation.

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
