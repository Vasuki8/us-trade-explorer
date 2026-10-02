# US Trade Explorer

Design baseline: 1 October 2026. Status updated: 2 October 2026. The working public preview uses synthetic data; authenticated private Census acquisition, recovery and selected-market/world checks have passed. No production website, accounts, advertisements or payment integration has been deployed. Start with the [development handoff](docs/handoff.md) for current commits, verification receipts, operating boundaries and next steps.

## Run the preview

```sh
npm ci --ignore-scripts
npm run dev
```

Requires Node 24. Open the loopback URL printed by Astro. The sample has four product chapters, five countries and 25 months; its figures are invented. All pages are noindex, and production publication is deliberately blocked. See [operations and Census key setup](docs/operations.md), [implementation status](docs/implementation-status.md), and the [implementation plan](docs/superpowers/plans/2026-10-01-public-mvp.md).

Run `npm test`, `npm run check`, `npm run build`, and `python -m unittest discover -s pipeline/tests -v`. Browser journeys use `npx playwright test` after `npx playwright install chromium`. Tests cover data contracts, missing values, exact dollars, safe exports, source limits, recovery, UI journeys and failed downloads.

Build a fast public reference for US merchandise imports and exports. Visitors should find a product or trading partner, understand its measured changes, compare markets, and download a reproducible result. Public profiles remain useful and free when subscriptions arrive.

## Confirmed business context

- Operator location: Gujarat, India. Legal entity, address, registrations and responsible contacts remain to be supplied.
- Target markets: United States, Canada, Mexico, China, India and Europe, including the United Kingdom. Exact European countries remain unresolved; EU/EEA and UK requirements are assessed separately.
- Future subscriptions: businesses and consumers.
- Existing asset: this private GitHub repository. Domain, hosting, advertising, analytics, email and payment accounts are unselected.
- Provisional infrastructure budget: US$25–50/month before taxes and professional services. This is a planning assumption, not a spending authorization or price guarantee.

## Recommendation

**Current development decision:** develop and test in GitHub, using a temporary sample preview where Pages eligibility permits. AWS is deferred until development is complete. See [GitHub development and preview setup](docs/github-development.md) for the build workflow, hosting limitations and transition plan. The architecture below remains the commercial launch target.

Use Astro static pages and small TypeScript interactions, with a Python/DuckDB ingestion pipeline in bounded GitHub Actions jobs. Store immutable raw and normalized releases in private object storage; publish only validated aggregates, compact datasets and HTML. Use GitHub for code, specifications, source registries, schemas, reviewed release manifests and deployment receipts, not the historical data warehouse.

For this India-based business, prefer private AWS S3 buckets in Mumbai behind CloudFront, using pay-as-you-go configuration, short-lived CI identity, configurable security headers and an explicit security-log archive in India. This adds some infrastructure setup but makes logging, private storage and future backend boundaries explicit. An alternative Cloudflare Pages deployment is simpler, subject to resolving log access and retention requirements. GitHub Pages is unsuitable for the planned commercial service under its [published restrictions](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).

Start with direct sponsorship placements served from our own static assets. Avoid third-party ad scripts and visitor analytics at launch. This is an advertising-supported model with fewer processors and less consent complexity; it does not eliminate hosting logs, privacy duties or sponsor contracting. Programmatic advertising is a later gated integration.

## Design deliverables

| Deliverable | Document |
|---|---|
| Architecture, components, trust boundaries, costs and recovery | [01 Architecture](docs/design/01-architecture.md) |
| Public and subscriber flow diagrams, interface and SEO rules | [02 Experience and SEO](docs/design/02-experience-and-seo.md) |
| Classification, statistical basis, periods, revisions and metrics | [03 Data model](docs/design/03-data-model.md) |
| Threat model, prioritized controls and verification cases | [04 Security](docs/design/04-security.md) |
| Jurisdiction and licence matrix, inventory and draft notices | [05 Legal and privacy](docs/design/05-legal-and-privacy.md) |
| Public MVP and subscription phases with acceptance gates | [06 Delivery plan](docs/design/06-delivery-plan.md) |

The diagrams are Mermaid source so they stay editable and reviewable in GitHub. These documents specify desired controls, not controls already implemented. The legal matrix distinguishes verified source statements, conditional applicability and unresolved professional-review questions.

## Initial product boundary

English interface; US reporter; monthly goods trade; nominal USD; Census basis; no seasonally adjusted claims. Start with all available HS2 chapters and trading partners for a selected 60-month window. Add HS4 only after measuring data volume and build costs. No HS6/HS10 coverage promise, customs classification advice, company-level shipment intelligence, services trade, live prices or tariff calculator. Country profiles describe each country's trade **with the US**, not its total worldwide trade.

The seven public sections are overview, product search, product profiles, country profiles, comparisons, recent changes, and sources/methodology. Future paid features are saved workspaces, watchlists, alerts, advanced comparisons and reports; none requires making ordinary public profiles private.

## What has been verified

Official source documentation, current API authentication requirements, major hosting terms and selected jurisdiction requirements were checked on 1 October 2026. The repository was confirmed empty before these documents were added. Important findings include Census API authentication and attribution requirements, India’s phased DPDP commencement, CERT-In logging/reporting requirements, the 2025 Mexico subscription amendments, and Stripe's invite-only onboarding in India. Each substantive finding is linked in the relevant document.

Authenticated private Census acquisition has passed for July 2026, HS2 chapter 09: eight selected-market observations and two world controls. Real Actions recovery preserved the market evidence, and the [private control report](docs/census-controls.md) independently verified its normalized inputs and the pinned initial-release announcement. Its two subset checks passed; full world reconciliation, API revision vintage and classification comparability remain unverified. Exact [raw statistical-response archiving](docs/census-archive.md) is now implemented on trusted `main`; authenticated market/world archive acquisition and recovery workflows have passed. Their verification receipts and remaining limits are recorded in the [handoff](docs/handoff.md). The website still uses synthetic data and rejects production builds.

The [private partner-discovery increment](docs/census-partners.md) is reviewed, merged and live-verified for the same month/chapter: 138 import observations and 122 export observations, with exact raw evidence, immutable receipts and byte-identical Actions recovery. Numeric codes remain unreviewed observations until a period-specific additive inventory is approved. The [handoff](docs/handoff.md) records review, integration, authenticated runs, evidence identities and expiry as each task completes.

The [public release boundary](docs/public-release-boundary.md) connects the fixed synthetic fixture to a public-only frozen projection and checksum-pinned loader. JSON, CSV and sample metadata share that validated release. Browser exploration/comparisons now use the same committed pin through bounded credential-free same-origin transport; changed bytes and redirects fail safely before rendering/export, with URL filters retained. Local checks cover HTTP download integrity and browser behavior at root/project paths; review/CI/integration outcomes are recorded separately in the handoff. The [July coverage review](docs/census-coverage-review.md) retains unresolved inventory/vintage/classification gates; official publication remains unsupported.

The [offline coverage diagnostic](docs/partner-coverage-diagnostics.md) generates source-bound private worksheets and exact inclusion/exclusion/unresolved totals from preserved partner evidence. All observed codes default to unresolved; scenario decisions and zero residuals never approve inventory, vintage, reconciliation or publication. Locally verified reports stay under ignored `.local/` and are rejected by the public release boundary. Review, CI and integration outcomes are recorded separately in the handoff.

Local contract, recovery, browser and static-output checks are implemented; see the [implementation status](docs/implementation-status.md) and [handoff](docs/handoff.md) for specific evidence and limits. Actual provider logging, production security enforcement, comprehensive accessibility, payment and cross-region hosting tests remain outstanding. Some primary legal pages could not be fully retrieved; those gaps are identified instead of being treated as verified law.

Product search accepts exact chapter codes such as `09` and `HS 09`. A detailed query such as `090111` explains the HS2-only preview boundary and offers broader chapter `09` coverage by explicit choice. The suggestion does not validate the detailed code or represent its trade. Broad name searches retain every match; absent/malformed queries provide clear recovery, and bounded query state survives reload/back/forward. The [handoff](docs/handoff.md) distinguishes local tests from review/CI/integration receipts.

## Decisions still needed

Supply the operator's legal identity and contact information, domain, actual budget and launch-country order. Confirm provider contracts, retention capabilities and India payment onboarding. Obtain the scoped legal/accounting reviews in the matrix before activating the affected features. Repository visibility stays private unless deliberately changed.
