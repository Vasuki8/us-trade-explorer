# US Trade Explorer design

Design baseline: 1 October 2026. Status: preimplementation design for review. No website, ingestion, accounts, advertisements or payment integration has been deployed.

Build a fast public reference for US merchandise imports and exports. Visitors should find a product or trading partner, understand its measured changes, compare markets, and download a reproducible result. Public profiles remain useful and free when subscriptions arrive.

## Confirmed business context

- Operator location: Gujarat, India. Legal entity, address, registrations and responsible contacts remain to be supplied.
- Target markets: United States, Canada, Mexico, China, India and Europe, including the United Kingdom. Exact European countries remain unresolved; EU/EEA and UK requirements are assessed separately.
- Future subscriptions: businesses and consumers.
- Existing asset: this private GitHub repository. Domain, hosting, advertising, analytics, email and payment accounts are unselected.
- Provisional infrastructure budget: US$25–50/month before taxes and professional services. This is a planning assumption, not a spending authorization or price guarantee.

## Recommendation

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

No live Census dataset has been ingested or reconciled. No runtime security, performance, accessibility, recovery, payment or cross-region hosting test has run. Actual provider logging, entitlement behavior and all launch acceptance tests remain implementation work. Some primary legal pages could not be fully retrieved; those gaps are identified instead of being treated as verified law.

## Decisions still needed

Supply the operator's legal identity and contact information, domain, actual budget and launch-country order. Confirm provider contracts, retention capabilities and India payment onboarding. Obtain the scoped legal/accounting reviews in the matrix before activating the affected features. Repository visibility stays private unless deliberately changed.
