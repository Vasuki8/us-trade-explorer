# Public MVP implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan.

**Goal:** A working, accessible Astro public preview plus tested ingestion/release foundations. Make sample data unmistakable and prevent its production publication.

**Architecture:** Static HTML and small TypeScript interactions consume a validated, release-pinned public JSON contract. Python isolates source acquisition and candidate storage. GitHub Actions verifies untrusted PRs without secrets; a separate manually dispatched job acquires source candidates from protected main.

**Tech stack:** Astro 7, TypeScript, Node 24 built-in tests, Python standard library, GitHub Actions. Defer DuckDB/Parquet until real backfill volume warrants it.

**Spec:** `docs/design/01-architecture.md` through `06-delivery-plan.md`.

## Global constraints

- No cloud provisioning, subscriptions, third-party tracking or paid deployment in this increment.
- Sample preview is noindex, labelled everywhere including exports, and cannot pass the production build gate.
- Official ingestion needs the user's key in a GitHub environment secret. Never accept keys through query input or log source request URLs.
- Unknown official dates stay null. A fetched candidate is not a verified public release.
- Large history, credentials, runtime state and builds remain outside Git.
- Manual Git worktree used because the app's native worktree tool targets the parent directory and returned `Not a git repository`.

## Review focus

Examine stale/malformed URL state, decimal precision, incomplete comparisons, accidental sample publication, leakage of request credentials, byte/time limits, partial release activation, untrusted descriptive strings, broken base-path links, and production assumptions unsupported by local tests.

## Task 1 — Release and analysis contracts

Files: `packages/contracts/trade.ts`, `tests/contracts.test.ts`, `tests/fixtures/sample-release.json`, `scripts/make-sample.py`.

- [x] Write failing tests for duplicate observations, schema/status/coverage failures, zero/missing baselines, exact large-dollar sums, safe exports and bounded share URLs.
- [x] Implement typed validation, calculations, filtering, CSV encoding and safe URL handling.
- [x] Generate deterministic synthetic data, with release/provenance and explicit scope.
- [x] Run `npm test`; expected all contract tests pass.

Interface: `Release` describes public data only; `validateRelease`, `change`, `sum`, `csv`, `parseQuery` are shared by build and browser. No private account fields accepted.

## Task 2 — Public website

Files: `astro.config.mjs`, `src/layouts/`, `src/components/`, `src/pages/`, `src/lib/`, `src/styles/`, `src/scripts/`.

- [x] Build overview, search, product/country profiles, comparison, changes, sources, methodology, release/status and preview privacy pages.
- [x] Implement URL-preserved flow/period/product/country controls, accessible tables/charts, ambiguous/empty/error states, share and safe CSV downloads.
- [x] Add real 404, canonical/sitemap policies, configurable base path, production release/domain gates and static output verification.
- [x] Run `npm run check` and `npm run build`; inspect desktop/mobile browser and failed download behavior.

Interface: pages consume Task 1 contract; browser fetches an immutable release URL named in the HTML. Production requires separately reviewed live release and configured domain.

## Task 3 — Isolated acquisition and release safety

Files: `pipeline/`, `sources/census.json`, `.github/workflows/`, `infra/cloudfront/`, `docs/operations.md`.

- [x] First test schema validation, rejected sources/redirects/oversized responses, bounded retry, idempotent immutable storage and failed activation retaining last good release.
- [x] Implement fixed Census source adapter and local atomic release store. Acquisition outputs a candidate only; reconciliation and full coverage must be demonstrated before live publication.
- [x] Lock dependencies, pin Actions commits, restrict permissions/timeouts and secrets to manual protected-environment acquisition on main.
- [x] Provide portable host routing/security policy foundation and concrete operational setup instructions; no fabricated deployment evidence.
- [x] Run Python suite plus complete Node/build checks.

Interface: raw candidate is private acquisition evidence, not a `Release`. Release activation requires the validated public contract and immutable digest; production publication stays disabled in this increment.

## Task 4 — Verification and handoff

- [x] Check rendered links/SEO, sample disclosure, bundle size, unsafe rendering, subpath build, failing production gate and browser journeys.
- [x] Fresh whole-branch review; reproduce/fix material findings and rerun affected checks.
- [x] Record verified results and external blockers in `docs/implementation-status.md`; commit and push feature branch, create a draft PR when connector supports it.

Five primary failures and evidence: wrong/missing figures (contract tests), corrupted update (atomic-store tests), exposed key (sanitized fetch tests and artifact canary scan), unsafe text/export (render/CSV tests), broken URL navigation (query tests, output link scan, browser checks).
