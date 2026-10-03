# Local research exports implementation plan

> **For agentic workers:** use superpowers:executing-plans or superpowers:subagent-driven-development, and superpowers:requesting-code-review before integration.

**Goal:** download and print a selected local research view without losing its statistical meaning or enabling public publication.

**Architecture:** extend the existing immutable, validated loopback review with fixed profile CSV and print routes. Generate small responses from the loaded candidate; no filesystem download endpoint, external requests, scripts, dependencies or public build changes.

**Tech stack:** existing Node 24/TypeScript HTTP server, semantic HTML/CSS and Playwright.

**Spec:** [permanent product instructions](../../../AGENTS.md), sections 7, 10, 14, 17, 25 and 27, and the accepted next task in [local review](../../local-research-review.md).

## Design and constraints

Existing profiles gain `Download CSV` and `Printable summary` links that preserve the flow. Routes append `.csv` or `/print` to `/products/09` and the four existing country paths. All other parameters/routes retain their existing 400/404 behavior. CSV errors return a normal error response, never a misleading attachment. Printable summaries support browser Print/Save as PDF with no JavaScript.

Each transferable result identifies fixture versus retained candidate, unpublished status, chapter-only scope, reporting month, trade basis, valuation, measure, nominal USD, classification, coverage and missing/zero states. Shares retain their world denominator and unavailable reasons. Retrieval, unknown official release/revision and absent publication remain distinct. Source and methodology URLs, classification vintage and historical limitations remain usable after a download/print is detached from its page. Country downloads exclude unrelated country observations. No new historical, quantity, concentration or causal analysis.

CSV preserves exact integer dollar strings and protects descriptive cells from spreadsheet formula injection, including leading whitespace/control characters. Fixed attachment filenames contain no request-derived header text. UTF-8/CRLF and quoting preserve commas, quotes and line breaks. Large integers remain exact in the file; spreadsheet software can round them when automatically importing numeric cells, so the guide must explain importing those columns as text.

Print layout uses a single readable column, preserves labels/definitions/source references, wraps long fields, and avoids the screen table's minimum width and scroll clipping. Browser-generated PDF is a user-controlled local export, not a published artifact. Local access remains unauthenticated against local processes; these files are unpublished and should not be redistributed as an approved release.

## Task 1 — complete local exports

Files: `tools/research-review/download.ts`, `view.ts`, `server.ts`, `review.css`; focused Node/view/server and browser tests; local guide/handoff/status.

Interfaces: `createReviewDownload(data, flowName, countryIndex|null, mode)` returns `{csv, filename}`; `renderReview` optionally returns `download` only for a valid CSV request. The server retains its existing request checks and sends attachment headers only for that result.

- [x] Write and observe failing generator, view and HTTP tests; implement CSV quoting/context, fixed routes and server response.
- [x] Add and verify printable summaries, mobile/desktop downloads and print-media readability with fabricated CI data.
- [x] Run full verification, retained evidence replay and actual local download/print checks without committing or logging actual values.
- [ ] Update continuity documents, inspect diff, commit, get independent immutable review and exact-head CI, merge under standing authorization, verify main/preview and preserve the owner's primary handoff edit.

## Review focus

- A missing world/partner or incomplete subtotal must stay blank/unavailable, distinct from reported zero.
- A country export needs its world denominator and chapter qualification without unrelated country figures.
- Hostile URL/header/formula text must not become an attachment path, response header or spreadsheet formula.
- Large exact dollar values and long visible source references must survive CSV/print without truncation.
- Public artifacts and publication guards must remain unchanged; downloads must never imply approval or freshness.

## Execution ledger

- Preflight: clean linked worktree at `d3de522d4237d02d01b3d506b82e5aef9f7fd264`; primary owner's one-line edit remains untouched. Live Pages remains legacy/errored, preview variable absent, configured site HTTP404. No new service or visibility change.
- CSV generation and UI/print implementation use disjoint agent-owned files; root owns HTTP integration, verification and documentation. No rulings or deferred findings.
- Generator/view/HTTP RED preceded implementation. Forty-one focused Node tests pass (one existing Windows symlink capability skip); full verification passes 159 Node tests with the same skip, 305 Python with four existing Windows skips, zero Astro diagnostics and unchanged 30-page/8,254-byte public build. All 32 desktop/mobile Chrome browser checks pass. Print navigation and compressed heading clipping regressions were observed and corrected. A new test's header union type was narrowed after the type check exposed it. Production rejection passes with the expected message; an earlier sandbox invocation failed before reaching the guard and was not counted as proof.
- Actual fresh/recovery Python/CLI/TypeScript replay matches at 5,124 bytes with input bytes unchanged. Actual desktop/mobile CSV and summaries preserve values, flow, source context and unpublished labels without external requests or overflow. Four three-page A4 PDFs retain context, and all twelve rendered pages were visually inspected with no clipping/overlap; evidence stays ignored. Ready for independent immutable review and exact-head CI; no rulings or deferred findings.
- Task feature complete: immutable head `5405b9bb65b657c25f8bc4f07e830c83f276f67e` passed clean independent review (40 focused Node passes/one existing Windows skip, 32 browser checks, twelve additional request probes) and exact-head Checks `37157721945` / job `111304528064`. PR #44 merged under standing authorization at `3d98da730aec45552e8357ec8faec7ce7bbaae67`; main Checks `37157926294` / job `111305130802` passed all 159 Node/305 Python tests without skips, zero diagnostics, 32 review/62 sample browser checks per path and expected production rejection. Sample preview built with deployment skipped; legacy Pages unchanged/failed and public URL HTTP404. Handoff receipt integration and exact owner-edit preservation follow under the established workflow; no rulings or deferred findings.
