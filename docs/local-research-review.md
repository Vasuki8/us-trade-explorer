# Local research review

The local review displays the [validated research candidate](public-research-candidate.md) through chapter, selected-country and source pages. It is a separate Node/TypeScript application under `tools/research-review`, not an Astro route or production backend. Actual values stay in ignored local files and memory; the public sample pin, 30-page build and publication gate are unchanged.

## Experience and scope

Open `/products/09?flow=imports` or `/countries/india?flow=exports` directly. Every profile explains July 2026, chapter 09, the selected flow, basis, valuation, nominal USD and monthly/non-seasonally-adjusted treatment. Flow switches use ordinary GET forms; links preserve the selection. The whole research journey works without JavaScript.

The chapter page shows its source world control, the four-country subtotal and selected partner table in Schedule C order, not ranked order. Country pages show this one chapter only, not a country's total trade. Missing observations, reported zero, incomplete selected subtotals and absent/zero share denominators have different explanations. Exact integer formatting never rounds dollars through JavaScript Number.

Each page identifies the view as unpublished. Fixture mode says all values are fabricated; retained-candidate mode says publication is not approved. Reporting period, first retained retrieval, unknown official release/revision and absent publication time remain separate. Collection time does not prove the snapshot is the latest official release. Historical growth, quantities and concentration remain unavailable. There is no inferred causal narrative.

Sources link to the approved Census dataset endpoints, separate HTSUS/Schedule B references and Schedule C annexes. The plain-language import/export and valuation explanations were checked against the [Census statistical guide](https://www.census.gov/foreign-trade/guide/sec2.html) on 3 October 2026. Clicking an external reference navigates to that provider; initial page loads and normal local navigation make no external requests, with referrers suppressed. No tracking, accounts, email, advertisements or payments are added.

The light interface uses semantic headings, labelled controls, table captions/headers, visible keyboard focus and a skip link. Narrow screens stack value cards and provide a labelled keyboard-focusable region for horizontal table scrolling. Important values do not require hovering or scripts.

## Operation

The engineering agent runs these commands; the owner is not expected to configure files or troubleshoot startup.

```sh
# After rebuilding/revalidating the candidate from retained evidence:
npm run review:research -- --candidate .local/public-candidate/fresh.json

# Explicitly fabricated test experience, without actual evidence:
npm run review:research -- --fixture --port 4323
```

Default address: `http://127.0.0.1:4322/products/09?flow=imports`. `/` redirects to the chapter. The server accepts imports/exports only, four named country slugs and `/sources`, with fixed CSV and print variants of profiles described below. Unknown routes return 404; unsupported/duplicate query parameters return 400 with a reset link. There is no data API, directory listing or arbitrary file-serving endpoint. These links work only on the computer running the server. The snapshot is loaded once; restart explicitly to review a newer validated candidate. Startup failure does not serve partial or fallback data.

Actual input must be a bounded regular file beneath the repository's ignored `.local` directory. The loader rejects linked paths (including Windows junctions), oversized files, invalid UTF-8, duplicate keys, extra envelope fields, noncanonical real bytes and checksum/schema violations before listening. The test-only fixture option accepts only the exact labelled fixture wrapper. Schema/checksum validation does not prove official source authenticity; Python source replay and future publication acceptance remain separate requirements.

The server binds only `127.0.0.1`. Host, Origin and Fetch-Metadata checks reject cross-origin requests and DNS-rebinding hostnames. It serves GET/HEAD only, bounds headers/URLs/connections/timeouts, disables caching, scripts and framing, and sends noindex, nosniff, no-referrer and same-origin resource headers. Text is escaped. Logs contain only a loopback startup URL or fixed failure messages, never request URLs, values, file paths or credentials. It does not fetch source data or read secrets. Loopback access is **not authentication against other local users/processes**; do not tunnel, reverse-proxy, deploy or bind this tool to a public interface. Private accounts/workspaces still require a future authorized backend.

## Verification and next step

Initial view/server tests failed on missing implementations before coding. A separate regression for Node's automatic `Expect` responses failed before adding controlled handlers. Local checks pass: eight view tests, seventeen server tests (one Windows file-symlink privilege skip; junction cases pass), full **143 Node tests** (142 pass/one skip), **305 Python tests** (four existing Windows capability skips), zero Astro diagnostics and the unchanged sample build/8,254-byte gzipped JS. Production publication is rejected; local review content is absent from `dist`.

The separate browser suite passes **24 tests** on installed Chrome: 22 desktop/mobile no-JavaScript journeys and two explicit CSP probes. It covers direct entry, flow selection/history, profile cross-links, source context, keyboard/mobile table access, HTTP errors/security headers and no external requests. CI runs this suite with fabricated data only, in addition to existing sample browser tests. No retained data or screenshot is uploaded. The local Playwright default browser cache was missing; the installed Chrome channel was used without downloading another browser.

Both retained fresh/recovery pairs were revalidated unchanged through Python/CLI/TypeScript. Actual desktop/mobile profiles matched local values, preserved flows and avoided page overflow/external requests. Screenshots are ignored under `.local/research-review/actual`; fixture screenshots are separately under `.local/research-review/screenshots`. Visual inspection found no layout issue. Independent review of `ece3da7fd5ebc1a387e7c4e543987f21a8dac9d1` found no actionable issues and separately passed 25 focused Node tests (one Windows capability skip), all 24 Chrome browser tests and seven additional malformed-filter/header/origin probes. Exact-head Linux CI passed all 143 Node/305 Python tests without skips, 24 review browser checks and 62 sample browser checks per base path. No findings were deferred. Integration receipts are in the [handoff](handoff.md) and PR history.

## Local downloads and printable summaries

Profiles offer `Download CSV` and `Printable summary`, preserving the flow. For example, `/products/09.csv?flow=exports` downloads chapter rows; `/countries/india/print?flow=imports` opens a self-contained country summary. Only the existing chapter and four countries are supported. Invalid downloads return a recoverable HTML error without attachment headers. Retry from the profile; a filename or clicked link alone does not prove a download succeeded.

CSV contains one consistent selected flow, world-denominator context and observation status. Chapter files include four selected partners and a complete subtotal, or explicitly identified observed partial sum if selected coverage is incomplete. Country files contain the selected country and world control, without other country amounts. Every row carries basis/valuation/measure/units, reporting month, coverage, source/reference URLs, classification limitations and separate time metadata. Unknown official dates are blank with companion state columns set to `unknown`; publication is blank with `published_at_state=not-published`. Fixture files explicitly identify fabricated data. Retained-candidate files remain unpublished review exports, not an approved release.

Files use UTF-8, CSV quoting and CRLF records. Descriptive cells that might start a spreadsheet formula are prefixed with an apostrophe, including formulas preceded by whitespace/control characters. Exact integer dollars are retained in file bytes; spreadsheet applications may round large numbers when automatically importing numeric cells. Import value columns as **text** when exact large integers matter. Blank unavailable values must be interpreted with their status/reason columns, never converted automatically to zero.

The printable view retains the subject, figures, scope, definitions, geographic notes, visible source URLs, retrieval context and unknown official/publication dates. Use the browser's Print or Save as PDF. Print styles remove navigation and controls, wrap references and preserve review/fixture warnings; no script is needed. These exports are local files under the user's control and may contain actual retained values. They do not authorize redistribution or public publication. The underlying snapshot and all loopback/request protections remain unchanged.

Export increment verification on 3 October 2026: initial generator/view/HTTP and print-layout failures were observed before implementation/correction. Full local verification passed 159 Node tests (one existing Windows symlink skip), 305 Python (four existing skips), zero Astro diagnostics and unchanged sample build/public pin/budget. All 32 desktop/mobile Chrome review tests pass, including actual browser downloads of fabricated CSV and print-media assertions. Retained source replay remains unchanged. Actual local CSV/profile summaries matched selected values and context without external requests or overflow. Four browser-generated three-page A4 PDFs retained text context, and all twelve pages were rendered and visually inspected without clipping/overlap. Actual files/images remain ignored. Independent review and exact-head/main integration receipts are recorded in the handoff and PR history when complete.

Next: prepare a **publication-readiness acceptance checklist and an evidence-backed coverage expansion plan**, prioritizing official ingestion/validation rather than more presentation features. New ingestion awaits an approved private execution/storage path and repository visibility intent. Official public activation also requires source-use, hosting and notices acceptance. This local tool does not bypass those gates or broaden the dataset.
