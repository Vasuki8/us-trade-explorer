# Operating model and official data priority

Decision date: **2 October 2026**. Status: owner-approved repository direction; documentation only. Permanent repository-wide instructions are [AGENTS.md](../../AGENTS.md). Current implementation and verification evidence remain in the [handoff](../handoff.md) and [implementation status](../implementation-status.md).

## Engineering responsibility

The user is the product owner, not the software maintainer. The agent owns ordinary architecture, data engineering, implementation, QA, security and release work through available permissions. Inspect the actual repository/deployment, choose supported technical approaches, implement and verify them, update continuity documents and explain material decisions in plain language. Do not hand routine code, configuration, migration, debugging or Git operations to the owner.

Standing authorization to merge tested, independently reviewed PRs remains. New spending, contracts, domains, material access changes, destructive operations, important historical-data deletion, external communications and privacy-affecting services still require authorization. A preferred provider is not permission to create an account or deploy it. Update the handoff after each task and include the recommended next task in completion chat.

## Preferred architecture and current implementation

Prefer GitHub plus bounded Actions pipelines, Python batch processing, analytical tools such as DuckDB when justified, and Parquet/object storage for larger facts. Prefer **Cloudflare Workers + Static Assets** for the future public application and **R2** for larger raw/historical/processed objects. Use **D1 only where smaller relational/application metadata fits**; do not load the complete detailed fact table into an application SQL database by default. Precompute published trade facts and assemble research views from compact results.

This supersedes the earlier AWS/S3/CloudFront launch preference. Existing Astro static output remains suitable for evaluation with the preferred host; no framework rewrite is authorized or required by this instruction update. The actual pipeline still uses the Python standard library. DuckDB, Parquet, Workers, R2 and D1 have not been installed or provisioned. No commercial host, domain or new service is active. The Cloudflare direction remains subject to fresh plan/terms, logging, retention, processing-location, security, cost and deployment checks before selection/activation; no current price, quota, India residency or log capability is asserted here.

Avoid permanent servers, unnecessary database services and queues. Preserve versioned releases, explicit trust boundaries, secret-free public builds, last-valid-release recovery and hosting portability. Retain earlier AWS-specific infrastructure files and dated research as a previous candidate; they are not the current provider mandate. Budgets in earlier designs are historical planning assumptions, not Cloudflare quotations or spending permission.

## Product and sequence

US merchandise trade remains the initial scope; services, company/shipment intelligence, personalized customs/legal advice and unsupported causal claims are outside it. Statistical basis, non-overlapping HS/partner categories, classification changes, quantities/units and missing/zero/suppressed states must stay explicit. Contributions identify measured movement, not causes; concentration requires defensible complete coverage and describes country-level trade rather than a company's supplier risk.

Grow trustworthy public utility and organic traffic first. Advertising is optional later work requiring explicit provider/privacy/business approval; direct sponsorship is no longer a launch prerequisite. Initial saved products, countries, baskets and reusable views should use browser-local storage where appropriate, without introducing accounts solely for saving. Prevent overlapping HS basket double counting. Cloud persistence, accounts, subscriptions, billing, delivery and teams remain later authorized phases with server-side isolation and entitlements.

Follow the full priority order in AGENTS.md §31. Reliable official ingestion, coverage/validation, definitions/provenance and replacement of demonstration data precede further feature expansion. Classification checks necessary for correct publication are immediate prerequisites; richer user-facing historical warnings can follow later. Do not remove sample/noindex/production guards until actual official-data and launch gates pass.

## Current milestone and next task

The public application remains **synthetic, noindex and unhosted**, with 30 prerendered pages. July 2026 / HS2 chapter 09 trusted-main acquisition, exact-response archiving, recovery and partner discovery exist. Private discovery/diagnostics do not approve a period-effective additive inventory, compatible official revision vintage, classification comparability or full-world reconciliation. They cannot feed public pages through a toggle.

Next bounded task: review official **July 2026 / HS2 09 partner inventory, import/export classification and revision-vintage evidence**, using the [coverage review](../census-coverage-review.md) and preserved private evidence. Retain unknowns and establish approval criteria before building an official producer. Current code syntax, reporting lists, `LAST_UPDATE`, matching months and zero residuals cannot supply unsupported approval. This replaces the prior next task of adding dollar-change table columns. Preserve required evidence before seven-day Actions artifacts expire; ignored local copies are not independent durable backups. New storage services and contacting sources remain separately authorized actions.

No source fetch, data approval, source-contract revision, infrastructure migration, dependency change or runtime feature is performed by this documentation decision. Historical task receipts retain their dates and counts; actual evidence overrides assumptions in future work.
