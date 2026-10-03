# US Trade Explorer

Design baseline: 1 October 2026. Operating model updated: 2 October 2026. The working public preview uses synthetic data; authenticated private Census acquisition, recovery and selected-market/world checks have passed. No production website, accounts, advertisements or payment integration has been deployed. Agents must read the permanent [model instructions](AGENTS.md), [operating-model decision](docs/decisions/2026-10-02-operating-model.md) and [development handoff](docs/handoff.md) for current responsibility, priorities, verification receipts and boundaries. The agent owns routine engineering; the owner makes product/business decisions.

**Actual repository state verified 2 October local / 3 October UTC:** this repository is now public; the agent made no visibility change. Private Census evidence workflows are blocked unless manually dispatched on private main. Existing artifact access follows repository read access. Pages currently reports legacy/errored configuration and its URL returns HTTP 404; no hosted result is claimed. The [visibility record](docs/private-evidence-visibility.md) supersedes private-development assumptions in the dated planning context below. Owner visibility intent and a safe private-evidence path remain unresolved.

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
- Existing asset: this GitHub repository (now verified public). Domain, commercial hosting, advertising, analytics, email and payment accounts are unselected.
- Provisional infrastructure budget: US$25–50/month before taxes and professional services. This is a planning assumption, not a spending authorization or price guarantee.

## Recommendation

**Current development decision:** develop and test in the private GitHub repository using local previews and private build artifacts. No commercial host is active. The preferred future direction is Cloudflare Workers + Static Assets and R2, superseding the earlier AWS launch target; provider selection/activation still requires plan, cost, terms, privacy and security review. See [GitHub development](docs/github-development.md) and the [operating-model decision](docs/decisions/2026-10-02-operating-model.md).

Retain Astro static pages and small TypeScript interactions, with Python ingestion in bounded GitHub Actions jobs. Introduce DuckDB or other analytical tooling and Parquet only when justified by data volume/processing requirements; the current pipeline uses the standard library. Store larger immutable raw and normalized releases in private object storage; publish only validated aggregates, compact datasets and HTML. Use GitHub for code, specifications, source registries, schemas, reviewed release manifests and deployment receipts, not the historical data warehouse.

Evaluate Workers + Static Assets for the public application, R2 for larger history/source/processed objects and D1 only for smaller lookup/application metadata where it fits. Do not automatically put the full trade fact table in an application SQL database. No Cloudflare resources or processing/logging/residency guarantees exist yet; verify the actual service/plan and operating flows before provisioning. The earlier AWS design remains a historical alternative. GitHub Pages remains a development-only candidate under the previously reviewed [published restrictions](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits); recheck terms before any changed use.

First establish validated official coverage, useful public analysis and organic traffic. Advertising, including direct sponsorship, may follow later with explicit business/privacy approval; it is not a launch prerequisite. No ad, analytics, email, account or payment integration is authorized by this operating-model update. Hosting logs still require an accurate inventory and applicable privacy/security review.

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

The seven public sections are overview, product search, product profiles, country profiles, comparisons, recent changes, and sources/methodology. Expand supported analytics according to the permanent instructions after data prerequisites pass. Initial saved products/countries, named baskets and reusable views should use browser-local storage where appropriate; basic saving must not require accounts. Prevent overlapping HS basket double counting. Later paid/cloud capabilities include cross-device workspaces, watchlists, alerts, advanced comparisons and reports; ordinary public profiles remain useful and free.

**Current priority:** official ingestion, coverage/validation, definitions/provenance and replacement of demonstration data take precedence over further feature expansion. Next resolve July 2026 / HS2 09 period-effective partner, classification and revision-vintage evidence described in the [coverage review](docs/census-coverage-review.md). Do not treat acquisition success or scenario residuals as official publication approval.

## What has been verified

The [single-period research assembler](docs/single-period-research.md) now combines the selected-country report with exact reviewed import/export chapter references. It supports the bounded July values/world shares while retaining explicit historical, fine-code and quantity restrictions. The exact export chapter bytes have been captured. The next step is a public-only projection and official-release validation; the website still uses the pinned sample until publication requirements pass.

The [selected-country report](docs/selected-partners.md) now validates retained July chapter-09 observations for Canada, Mexico, India and China and calculates their shares of the same-response world control. Missing values and partial coverage remain explicit; no complete-world concentration or public-data approval follows. See the [handoff](docs/handoff.md) for current verification and the next classification prerequisite.

Official source documentation, current API authentication requirements, major hosting terms and selected jurisdiction requirements were checked on 1 October 2026. The repository was confirmed empty before these documents were added. Important findings include Census API authentication and attribution requirements, India’s phased DPDP commencement, CERT-In logging/reporting requirements, the 2025 Mexico subscription amendments, and Stripe's invite-only onboarding in India. Each substantive finding is linked in the relevant document.

Authenticated private Census acquisition has passed for July 2026, HS2 chapter 09: eight selected-market observations and two world controls. Real Actions recovery preserved the market evidence, and the [private control report](docs/census-controls.md) independently verified its normalized inputs and the pinned initial-release announcement. Its two subset checks passed; full world reconciliation, API revision vintage and classification comparability remain unverified. Exact [raw statistical-response archiving](docs/census-archive.md) is now implemented on trusted `main`; authenticated market/world archive acquisition and recovery workflows have passed. Their verification receipts and remaining limits are recorded in the [handoff](docs/handoff.md). The website still uses synthetic data and rejects production builds.

The [private partner-discovery increment](docs/census-partners.md) is reviewed, merged and live-verified for the same month/chapter: 138 import observations and 122 export observations, with exact raw evidence, immutable receipts and byte-identical Actions recovery. Numeric codes remain unreviewed observations until a period-specific additive inventory is approved. The [handoff](docs/handoff.md) records review, integration, authenticated runs, evidence identities and expiry as each task completes.

The [public release boundary](docs/public-release-boundary.md) connects the fixed synthetic fixture to a public-only frozen projection and checksum-pinned loader. JSON, CSV and sample metadata share that validated release. Browser exploration/comparisons now use the same committed pin through bounded credential-free same-origin transport; changed bytes and redirects fail safely before rendering/export, with URL filters retained. Local checks cover HTTP download integrity and browser behavior at root/project paths; review/CI/integration outcomes are recorded separately in the handoff. The [July coverage review](docs/census-coverage-review.md) retains unresolved inventory/vintage/classification gates; official publication remains unsupported.

The [offline coverage diagnostic](docs/partner-coverage-diagnostics.md) generates source-bound private worksheets and exact inclusion/exclusion/unresolved totals from preserved partner evidence. All observed codes default to unresolved; scenario decisions and zero residuals never approve inventory, vintage, reconciliation or publication. Locally verified reports stay under ignored `.local/` and are rejected by the public release boundary. Review, CI and integration outcomes are recorded separately in the handoff.

The [retained acquisition provenance receipt](docs/acquisition-provenance.md) binds complete existing partner evidence, exact response/query/scan/receipt identities and the current operational journal. It separates first retained ingestion time, retry attempts and optional initial-announcement evidence from unknown official API revision generation. It runs offline, writes only ignored private JSON, changes no original evidence and leaves publication gates false. It does not replace the unresolved private ingestion/storage path or activate official website data.

Local contract, recovery, browser and static-output checks are implemented; see the [implementation status](docs/implementation-status.md) and [handoff](docs/handoff.md) for specific evidence and limits. Actual provider logging, production security enforcement, comprehensive accessibility, payment and cross-region hosting tests remain outstanding. Some primary legal pages could not be fully retrieved; those gaps are identified instead of being treated as verified law.

Product search accepts exact chapter codes such as `09` and `HS 09`. A detailed query such as `090111` explains the HS2-only preview boundary and offers broader chapter `09` coverage by explicit choice. The suggestion does not validate the detailed code or represent its trade. Broad name searches retain every match; absent/malformed queries provide clear recovery, and bounded query state survives reload/back/forward. The [handoff](docs/handoff.md) distinguishes local tests from review/CI/integration receipts.

Country-profile exploration and comparisons preserve all included sample chapters through explicit `product=all` URL state. This scope is the pinned release's four chapters, not a national country total. Current and prior-year sums require every included chapter; missing values remain unavailable. The selected CSV contains the underlying chapter observations for the selected month, rather than calculated totals or prior-year rows. Individual chapter views and existing omitted-product defaults remain available.

Undefined year-over-year percentages show a visible explanation on profiles and tables: unavailable current values, a prior-year month absent from the release, unavailable prior values, or a zero baseline. Included-chapter sums identify unavailable required values. Explanations remain readable on static profiles without JavaScript; defined percentages retain their existing calculation, and zero baselines retain exact dollar differences. These presentation details never become source observations or CSV fields.

## Decisions still needed

Supply the operator's legal identity and contact information, domain, actual budget and launch-country order. Confirm provider contracts, retention capabilities and India payment onboarding. Obtain the scoped legal/accounting reviews in the matrix before activating the affected features. Repository visibility stays private unless deliberately changed.
