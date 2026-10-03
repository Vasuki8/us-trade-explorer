# Local research review implementation plan

> **For agentic workers:** use superpowers:executing-plans for inline implementation and superpowers:requesting-code-review for independent whole-branch review.

**Goal:** review validated July chapter 09 candidate data through complete product/country screens without enabling public publication.

**Architecture:** separate Node/TypeScript loopback-only server outside Astro's application/build tree. Validate and freeze a bounded candidate file once at startup; render semantic HTML on each GET with no client JavaScript, external assets, personal-data collection or API calls. The public sample build and production gate remain unchanged.

**Tech stack:** existing Node 24, TypeScript contract, built-in HTTP/filesystem/crypto, existing Playwright. No dependencies or infrastructure added.

## Design and constraints

The owner has authorized normal implementation and merges after verification/review. This reversible local view follows the accepted next task. No new business/provider/permission decision is needed.

Use `/products/09?flow=imports|exports`, `/countries/{canada|mexico|india|china}?flow=...`, and `/sources?flow=...`; `/` redirects to the product. Each direct entry explains US merchandise trade, July 2026, HS2 chapter 09, flow/basis/valuation/units, selected coverage, data status and source context. Product pages show the world chapter control and the four selected partners without implying global rankings. Country pages show only the included chapter, never a national country total. Links preserve flow; a GET form switches it with no JavaScript. Historical change/quantity/concentration are explicitly unavailable. No invalid value-per-unit, trade balance or causal explanation is added.

Known-good single-month values are the focus, with readable exact dollars and world shares. Missing versus reported zero, partial selected totals, missing/zero denominators, unknown official dates and classification continuity limits remain visible. Source pages expose approved public endpoints/reference URLs and separate reporting/retrieval/publication concepts. Show an unpublished-review banner on every page. A fixture mode is explicitly labelled fabricated on every page; real evidence mode is never called an approved official release.

The chosen approach avoids adding unpublished routes to Astro or generating transferable HTML directories containing retained values. Only a explicitly named file under `.local` may be loaded for real review; reject symlinks/junctions, oversize/extra/duplicate envelope fields and checksum failures before listening. A dedicated fabricated-fixture option is available for CI/browser tests. Do not read credentials, fetch Census, enumerate files or log request URLs/data. Keep the last server snapshot immutable; restarting is explicit.

Bind only `127.0.0.1`, validate the exact loopback Host and same-origin Origin/Fetch-Metadata, permit GET/HEAD only, bound requests/timeouts, no filesystem/API/download routes or CORS. Use CSP, no-store, noindex, nosniff, no-referrer, same-origin resource policy and frame denial. Host validation prevents DNS rebinding; local loopback access is not authentication against other local users/processes. All text is escaped. Unknown routes and invalid filter combinations give proper 404/400 with recovery links. The server is not a deployable production backend.

## Task 1 — working local profile review and its boundary tests

Files: `tools/research-review/{view.ts,server.ts,review.css}`, Node tests, a separate Playwright review config/test directory, npm commands, guide/handoff/status. No `src` routes, sample data/pin or publication workflow changes.

1. Write and run failing tests for product/country/source rendering, status/definition context, direct-entry flow links and bad routes/queries; then implement the view.
2. Write and run failing tests for startup file/manifest validation, loopback/origin/method/path boundaries, fixed failure messages and HTTP headers; then implement the bounded server.
3. Add fixture-only desktop/mobile/no-JavaScript browser checks with request-origin assertions and local screenshot evidence. Run focused tests, full Python/Node/Astro/build and production rejection checks. Revalidate retained source candidates and open the real local review; inspect its mobile/desktop layout without committing actual values or images.
4. Update handoff/guide/status, inspect diff, commit and get independent immutable review. After exact-head CI passes, merge under standing authorization, inspect main/preview evidence and synchronize primary while preserving the owner's exact handoff edit and backups. Record integration receipts without recursive documentation work.

## Review focus

No retained values in public artifacts; file traversal/symlink/oversize/duplicate envelope handling; genuine loopback-only listener and hostile Host/Origin/method rejection; no private fields or arbitrary text rendered; world/country scope and missing/zero denominators; fixed single-period limitations; mobile/table/keyboard/no-JavaScript journeys; fixture versus actual labels; unchanged public release pin and production rejection.

## Execution ledger

- Preflight: clean linked development worktree at `88d6853ba43b8f8e1ad4103db8d4727a42551505`; primary has only the preserved one-line owner handoff edit. Fresh read-only hosting still legacy/errored, preview variable absent. No provider activated.
- A subsequent developer instruction enabled proactive parallel work. Server/Node boundary tests and browser harness/CI checks were delegated with disjoint file ownership; the root owns views, visual review, integration and documentation. This changes execution mechanics only, not scope or approval boundaries.
- View RED observed on missing module; eight focused tests now GREEN, covering direct-entry context, exact values, missing/zero denominators, flow preservation, route recovery and escaping. Server and browser validation are in progress. No rulings or deferred findings.
- Server RED observed on missing module and automatic HTTP Expect responses; seventeen tests now pass (one Windows file-symlink capability skip). Browser startup RED on missing view preceded implementation; 24 desktop/mobile cases now pass with installed Chrome. Full local verification: 143 Node (one skip), 305 Python (four existing skips), clean Astro/sample build and expected production rejection. Actual fresh/recovery replay, exact page values, no external requests, responsive screenshots and unchanged public artifact boundary verified. Ready for independent immutable review; no rulings or deferred findings.
- Task 1 complete: immutable implementation `ece3da7fd5ebc1a387e7c4e543987f21a8dac9d1` passed clean independent review, 25 focused Node tests (one Windows skip), 24 browser checks and seven additional malformed-request probes. Exact-head Checks `37155383681` / job `111297593356` passed 143 Node/305 Python tests without skips, clean Astro/builds, 24 review browser checks, 62 sample browser checks per base path and expected production rejection. PR #42 merged under standing authorization at `cb579e2709a01a12b562ccb417dddb87412aa71b`. No rulings or deferred findings. Preserve actual ignored evidence/screenshots and the primary owner edit during synchronization.
