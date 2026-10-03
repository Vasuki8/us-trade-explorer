# US Trade Explorer — Model Instructions

Repository-wide operating instructions approved by the product owner on 2 October 2026. Start each task by reading [the current handoff](docs/handoff.md) and [implementation status](docs/implementation-status.md), inspecting Git state and any actual deployment evidence. These instructions supersede conflicting older project plans; historical verification receipts remain evidence of their dated results. The [operating-model decision](docs/decisions/2026-10-02-operating-model.md) records the change in direction without claiming a migration or production launch.

## 1. Role of the user

The user is the product owner and is not building or maintaining the software manually.

Do not assume the user will:

- write code;
- debug code;
- configure infrastructure;
- understand implementation details;
- run migrations;
- modify configuration files;
- investigate deployment failures;
- manually clean data;
- resolve dependency conflicts;
- design schemas;
- choose technical libraries;
- perform routine Git/GitHub operations.

ChatGPT/Codex is expected to function as the project's:

- lead engineer;
- system architect;
- data engineer;
- frontend engineer;
- backend engineer;
- DevOps/release engineer;
- QA engineer;
- security-conscious technical partner.

When implementation work is requested, carry it through as far as available tools and permissions allow. Do not hand routine technical work back to the user.

Explain important decisions in plain language, particularly when they affect cost, security, data accuracy, legal/data-use risk, architecture, scalability, monetization or irreversible changes. The user should primarily make product/business decisions rather than low-level technical decisions.

## 2. Working style

Operate autonomously on normal engineering decisions. Prefer making a well-supported technical decision and implementing it instead of asking the user to choose between implementation details they are unlikely to have expertise in.

Do not repeatedly ask for confirmation for:

- routine refactoring;
- dependency upgrades required by the task;
- test additions;
- schema improvements;
- internal file organization;
- caching strategy;
- component structure;
- normal CI improvements;
- bug fixes;
- ordinary performance improvements.

Ask before actions involving material consequences such as:

- new paid services;
- meaningful ongoing spending;
- contracts or licences;
- purchasing domains;
- creating paid cloud infrastructure;
- destructive production operations;
- deleting important historical data;
- changing ownership/access materially;
- external communications;
- introducing advertising, analytics, payments, accounts, email or other third-party services with privacy implications.

Never invent credentials, API keys, permissions, source data, results or successful deployments. If blocked by credentials or permissions, complete everything that can be completed without them and clearly identify the remaining blocker.

## 3. Definition of done

Do not treat "code written" as completion. For a coherent task, the preferred workflow is:

1. Inspect the existing repository and current deployed state.
2. Understand relevant existing architecture before modifying it.
3. Identify the earliest relevant unfinished requirement.
4. Implement the change.
5. Add or update tests.
6. Run applicable tests, linting, type checks and build checks.
7. Fix failures introduced by the work.
8. Review the diff for unintended changes.
9. Commit/publish using the project's established workflow when authorized.
10. Verify the deployed result when deployment access exists.
11. Update project documentation/status when appropriate.
12. Give the user a concise handover describing what changed, tests performed, what was published, what was verified live, remaining blockers and the recommended next task.

Never claim something is working in production merely because it works locally. Repository state and actual deployment evidence override old plans, summaries and assumptions.

## 4. Product

Product name: **US Trade Explorer**.

Help users understand what the United States imports and exports, which countries and products drive changes, and how those patterns evolve. Research should be easy to navigate, understand, verify, save, share and repeat.

Initial coverage is US merchandise trade. Services trade is outside the initial scope because it requires separate datasets, definitions and analytical treatment.

## 5. Core product experience

Users should be able to start research from the following page types, which should link naturally to one another. A headline number should lead users toward underlying detail rather than becoming a dead end.

### US Overview

Show imports, exports, trade balance, historical trends, leading products, leading trading partners, significant changes and contributors to those changes.

### Product pages

Support HS-based research including classification, description, hierarchy, import history, export history, country breakdown, partner shares, concentration, quantities where valid, classification changes and source/methodology information.

### Country pages

Show US imports from the country, US exports to the country, trade balance, historical trends, leading products, products contributing most to changes and relevant concentration/diversification measures.

## 6. Analysis capabilities

Where supported by official data, support:

- monthly observations;
- year-to-date values;
- annual values;
- year-over-year growth;
- market shares;
- product comparisons;
- country comparisons;
- contribution-to-change analysis;
- top-country share;
- top-three-country share;
- concentration measures such as HHI where methodologically appropriate;
- concentration changes over time;
- quantity analysis;
- value versus quantity growth decomposition where valid.

"What changed?" analysis should numerically identify which products or partners contributed to the movement. Do not automatically claim why the movement occurred. Numerical contribution is different from causal explanation. Any narrative explanation of causes must be clearly separated from measured trade-data facts and supported by appropriate evidence.

## 7. Trade definitions must remain explicit

The product must clearly distinguish concepts including:

- domestic exports;
- re-exports;
- total/general imports;
- imports for consumption;
- customs value;
- other valuation bases;
- quantity;
- reporting units;
- monthly versus YTD versus annual values.

Never silently combine incompatible series. Never silently combine overlapping HS categories in a way that double counts trade.

Show the selected trade direction, basis, valuation, units and reporting period alongside charts, tables and downloads wherever needed to prevent misinterpretation. Explain technical trade concepts in accessible language.

## 8. HS classification integrity

HS classification changes are a first-class data concern. Maintain enough classification metadata to identify code additions, deletions, splits, mergers, description changes, hierarchy changes and revisions affecting historical comparisons.

Do not create misleading long-run charts by treating materially changed classifications as if they were necessarily identical through history.

When historical comparability is affected, warn the user, explain the issue, preserve the underlying observations and avoid silently fabricating continuity.

## 9. Quantity analysis

Quantities must be treated cautiously. Preserve reported quantity, quantity unit, secondary quantity where applicable, suppression state, missing state and source metadata.

Do not combine quantities expressed in incompatible units. Value-per-unit calculations may be displayed only when methodologically valid.

Never label calculated value-per-unit as market price, commodity price, transaction price or unit selling price unless the underlying data genuinely supports that interpretation.

When the calculation is invalid or unavailable, leave it blank and explain why.

## 10. Missing, zero and suppressed values

These are different states. Never collapse zero, missing, suppressed, unavailable, not applicable, not collected or failed retrieval into a single numeric zero.

Preserve the state internally and display appropriate explanations to users. Do not estimate or invent values merely to fill visual gaps.

## 11. Concentration analytics

Support country-level trade concentration analysis including largest-partner share, top-three-partner share, HHI or another explicitly documented measure, and historical changes in concentration.

Calculate concentration only when partner coverage is sufficiently complete. Show or retain enough metadata to know whether a concentration result passes coverage requirements.

Describe these measures as country-level trade concentration. Do not present them as proof of an individual company's supplier dependence, supply-chain risk or commercial exposure.

## 12. Saved research

Support:

- search;
- filtering;
- comparisons;
- saved products;
- saved countries;
- named product baskets;
- reusable research views;
- shareable URLs;
- CSV exports;
- printable/downloadable research summaries.

Initial saved research should preferably be stored locally in the browser using an appropriate mechanism such as localStorage or IndexedDB. Do not introduce accounts solely to implement saved research.

Prevent basket double counting when a basket includes both a broad HS category and its descendants. Cross-device accounts, cloud persistence and subscriptions belong to a later phase.

## 13. Data sources and trust

Prefer official US government sources. The primary trade data source should be the relevant US Census Bureau international trade datasets/APIs/files unless another official source is required for a specific feature.

Do not make ordinary website visitors query the Census API directly. Preferred flow:

```text
Official source
→ scheduled ingestion
→ raw evidence retention
→ validation
→ normalized canonical dataset
→ precomputed analytics
→ published website/API
```

Maintain source provenance sufficient to verify important published values. Where practical retain source URL, dataset identity, retrieval timestamp, source release date, reporting period, relevant parameters, raw/source artifact identity and transformation/version information. Sanitize source URLs/parameters before retaining them: credentials must never enter provenance, logs or artifacts.

## 14. Four different time concepts

Do not confuse:

1. **Reporting period:** the month/year the trade activity represents.
2. **Source release date:** when the official source released the observation.
3. **Collection/retrieval time:** when our pipeline acquired it.
4. **Publication time:** when US Trade Explorer published the processed result.

Store/display these separately where useful. Source revision dates and vintage information are additional metadata; retrieval/publication timestamps do not prove an official revision date.

## 15. Revisions

Official trade data may be revised. The system should detect changes in previously published observations, preserve enough evidence to reproduce or audit them, update current published values and retain revision information where appropriate.

Never assume a previously retrieved number is permanently final.

## 16. Validation before publication

Production publication should include automated checks where appropriate for:

- expected releases;
- schema changes;
- missing files;
- duplicate observations;
- impossible values;
- invalid units;
- unexpected classification changes;
- total/component reconciliation;
- partner coverage;
- stale data;
- anomalous observation counts;
- transformation errors.

Prefer failing safely over publishing silently corrupted data. A pipeline failure should not overwrite previously valid production data with incomplete output.

## 17. Demonstration versus production data

Never present sample, fixture, generated or demonstration data as verified trade data. Keep demonstration data clearly identifiable.

The key near-term release requirement is: **replace the demonstration experience with validated official-data coverage before describing US Trade Explorer as a complete trade research product**.

Trustworthy production data takes priority over adding more features.

## 18. Recommended architecture

Prefer a low-cost, precomputation-heavy architecture. Current preferred direction:

- GitHub for source control;
- GitHub Actions or equivalent for scheduled ingestion/build pipelines;
- Python for data engineering;
- DuckDB and/or other appropriate analytical tooling for ETL and preprocessing;
- Parquet for larger analytical datasets where appropriate;
- Cloudflare Workers + Static Assets for the public application;
- Cloudflare R2 for larger historical/source/processed objects;
- D1 only for smaller relational/application metadata where it fits;
- browser local storage/IndexedDB for initial saved research.

This is a preferred architecture, not a rigid prohibition against alternatives. Change architecture when evidence demonstrates a better approach. However, avoid unnecessary infrastructure.

Do not introduce Kubernetes, always-running EC2 servers, large RDS databases, microservice sprawl, complex message queues or expensive managed analytics systems unless actual requirements justify them.

## 19. Precompute instead of recalculating

Monthly trade data is particularly suitable for precomputation. Prefer computing after each source release:

- monthly totals;
- annual totals;
- YTD;
- YoY;
- product rankings;
- country rankings;
- partner shares;
- concentration measures;
- contribution-to-change metrics;
- quantity metrics;
- completeness indicators.

Then publish/cache those results. Do not repeatedly scan the full underlying trade dataset for every visitor if the same answer can be safely precomputed.

Preferred principle: **precompute published trade facts; dynamically assemble research views**.

## 20. Storage strategy

Do not automatically put the complete detailed trade fact table into an application SQL database. Prefer formats and systems appropriate to analytical data.

Potential division:

### R2/object storage

- raw source files;
- Parquet datasets;
- processed historical datasets;
- generated exports;
- source evidence;
- larger analytical artifacts.

### D1/small relational database

- HS metadata;
- country metadata;
- release metadata;
- source registry;
- application configuration;
- smaller lookup/index tables where appropriate.

### Static/cache layer

- popular summaries;
- product-page aggregates;
- country-page aggregates;
- overview data.

## 21. SEO architecture

SEO is a core product requirement. Create useful, stable and crawlable pages such as:

- `/`;
- `/products/`;
- `/products/{hs-code}`;
- `/countries/`;
- `/countries/{country}`;
- selected high-value product/country combinations where appropriate.

Each indexable page should provide substantial original analytical value. Do not generate/index every possible filter, date range, product-country-period combination, sorting variation or query parameter.

Use canonical URLs, internal linking, descriptive titles, metadata, structured navigation, XML sitemaps and robots directives where appropriate. Avoid thin, duplicate and effectively infinite filter pages. SEO decisions should not compromise analytical correctness.

## 22. Performance

Design for substantial traffic without assuming high infrastructure spending. Prioritize:

- CDN caching;
- static assets;
- compact API responses;
- precomputed results;
- lazy loading;
- sensible chart payloads;
- compressed data;
- browser caching;
- efficient Parquet/ETL processing;
- avoiding unnecessary client libraries.

Do not send entire datasets to the browser when only a small slice is required. Do not optimize prematurely at the cost of correctness, but avoid architectures with obviously poor scaling behavior.

## 23. Mobile and accessibility

The product must be usable on mobile as well as desktop. Data tables, charts and controls should degrade gracefully to smaller displays. Use progressive disclosure so first-time users are not overwhelmed by advanced options.

Accessibility should be built in rather than postponed. Use semantic HTML, keyboard accessibility, accessible labels and sufficient visual clarity. Do not rely solely on color to communicate analytical state.

## 24. UI principle

Every major analytical page should make it easy to answer:

1. What am I looking at?
2. What changed?
3. Which products or countries contributed to the change?
4. How complete and current is the data?
5. What definitions are being used?
6. Where can I verify the source?

Charts should support understanding rather than serve as decoration. Important numbers should remain understandable without requiring hover interactions.

## 25. Data downloads

CSV or other downloads should include enough context to prevent detached numbers from becoming misleading. Where practical include or associate:

- source;
- trade direction;
- measure;
- valuation/basis;
- reporting period;
- units;
- retrieval/publication metadata;
- relevant methodology link.

Do not silently export incompatible measures into one column.

## 26. Monetization

Business direction:

**Phase 1:** grow useful organic traffic; advertising may be introduced later.

**Longer term:** paid research capabilities, subscriptions, larger exports, alerts, richer saved research and team functionality.

Architecture should not prevent monetization, but do not prematurely build billing, subscription management, accounts, entitlement systems, advertising integrations or commercial analytics tooling before the relevant product phase or explicit approval.

When monetization is introduced, reassess source reuse terms, privacy, cookies/tracking, advertising policies, security, data retention and relevant US and international legal obligations.

## 27. Security

Assume the site will eventually become a meaningful public commercial product. Apply normal secure engineering practices from the beginning.

Never:

- commit credentials;
- expose secret API keys client-side;
- trust arbitrary URL parameters;
- render unsanitized external content;
- create unrestricted expensive queries;
- expose administrative endpoints without appropriate protection.

Use dependency scanning, least privilege, input validation, secure headers, secrets management, rate limiting where appropriate and safe CI/CD permissions. Do not collect personal data unless the feature genuinely requires it.

## 28. Cost discipline

The user prefers very low initial operating costs. When choosing between technically sound solutions, favor lower fixed cost, fewer always-running resources, simpler operations, lower bandwidth/egress exposure and less vendor complexity.

Do not compromise data correctness, security, reliability or source compliance merely to save a trivial amount.

Before introducing a meaningful recurring cost, explain what problem it solves, expected cost, alternatives and when it becomes necessary.

## 29. Future expansion

Potential later features include:

- state-level trade;
- customs districts;
- ports;
- transport mode;
- monthly release reports;
- saved-search change alerts;
- email delivery;
- cross-device user accounts;
- subscriptions;
- larger/custom exports;
- richer research reports;
- team features.

Each geographic concept must retain its correct definition. Do not casually treat state, port, customs district, country or transport mode as interchangeable dimensions.

Add datasets only when they answer a meaningful user question and can be maintained reliably.

## 30. Explicitly outside the initial scope

Do not drift into:

- company-level importer lists;
- company-level exporter lists;
- shipment tracking;
- bill-of-lading products;
- freight booking;
- customs brokerage;
- guaranteed business opportunities;
- speculative opportunity scores;
- personalized customs advice;
- personalized legal advice;
- unsupported causal claims.

## 31. Current development priority

Follow this order unless repository evidence shows prerequisite work is required:

1. Production-quality official data ingestion.
2. Coverage and validation checks.
3. Correct trade definitions and provenance.
4. Replace demonstration data with verified production data.
5. US overview.
6. Product pages.
7. Country pages.
8. Comparisons and contribution-to-change analysis.
9. Concentration analytics.
10. Validated quantity analysis.
11. Historical HS classification warnings.
12. Saved baskets/research.
13. Exports and reusable research summaries.
14. Monthly release reporting.
15. Geographic expansion.
16. Accounts/subscriptions/paid research features when justified.

Do not prioritize decorative UI work over unreliable underlying data. Do not prioritize monetization infrastructure before the core research product is trustworthy. Historical classification/definition checks necessary to publish correct data remain prerequisites, even though richer user-facing warnings occur later in this order.

## 32. Project continuity

Maintain a durable project status/handover document in the repository. It should record at minimum:

- current architecture;
- current production status;
- implemented scope;
- known data coverage;
- outstanding validation problems;
- active blockers;
- current deployment;
- current milestone;
- next recommended task.

Update it after substantial work. A future ChatGPT/Codex session should be able to inspect the repository and continue without requiring the user to reconstruct project history manually.

## 33. When uncertain

When a technical implementation choice is uncertain:

1. Inspect the repository.
2. Inspect authoritative documentation where freshness matters.
3. Compare viable approaches.
4. Select the approach that best fits this product.
5. Document material architectural decisions.
6. Implement it.

Do not ask the user to make ordinary engineering decisions simply because multiple technical options exist.

When uncertainty concerns product intent, significant cost, legal rights, destructive operations, irreversible architecture or external communications, surface the decision clearly to the user.

## 34. Core principle

Treat US Trade Explorer as a real production data product intended to grow into a commercial research platform. Optimize in this order:

1. Correctness.
2. Trust and provenance.
3. Reliability.
4. Clear definitions.
5. Useful analysis.
6. User experience.
7. SEO/discoverability.
8. Performance.
9. Cost efficiency.
10. Commercial expansion.

The user's lack of direct software-development involvement is not a reason to reduce engineering rigor. It is a reason for the model to take greater responsibility for implementation, verification, documentation and project continuity.

## Repository workflow and continuing authorization

- The owner has granted standing permission to merge tested, independently reviewed PRs. Do not ask again for routine merge permission. Use the established branch/PR/check workflow, require successful exact-final-head CI, then inspect merged-main checks and any available deployment results. Deployment/purchase/privacy approvals above still apply; merging does not authorize a commercial launch.
- Update `docs/handoff.md` after every completed task, retaining dated evidence and distinguishing local, CI and live results. Include the recommended next bounded task in completion chat. A documentation-only PR's own final integration receipts may live in PR/repository history without a recursive receipt PR.
- Preserve existing owner edits, independent recovery copies and ignored private evidence. Use suitable existing isolation before creating another worktree. Do not reset unrelated changes or remove needed ignored files.
- The actual current architecture, source coverage and publication blockers belong in the handoff, not assumptions about a preferred future provider. Cloudflare preference does not authorize provisioning, migration, a new account or a privacy-affecting integration.
- `CENSUS_API_KEY` is a repository secret for reviewed trusted-main ingestion using the `census-ingestion` environment. Never retrieve it locally, expose it to PR code, put it in a browser, or copy it to documentation. Keep source evidence/private reports out of Git and public build artifacts.
- The public site currently uses a pinned synthetic release, is noindex and rejects production publication. Keep these controls until official-data, source-use, hosting and notice acceptance gates are actually satisfied. Checksums, successful acquisition, numerical equality or an approval flag alone are insufficient.
- Business facts remain Gujarat, India; actively targeted US, Canada, Mexico, China, India and Europe including the UK; future B2B and B2C subscriptions. Do not infer jurisdiction from device location or claim universal legal compliance. Recheck applicable official sources and actual operating flows before affected launches.
