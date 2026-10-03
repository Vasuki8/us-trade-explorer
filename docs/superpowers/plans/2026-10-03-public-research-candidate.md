# Public research candidate implementation plan

> **For agentic workers:** use superpowers:executing-plans for inline implementation and a fresh independent whole-branch review before merging.

**Goal:** prepare a bounded public-safe July chapter 09 data contract from validated retained evidence, without activating official data on the website.

**Architecture:** Python revalidates both complete archives and their reviewed references, then explicitly projects one import/export bundle. A separate browser-compatible TypeScript reader validates exact structure, definitions, arithmetic and canonical bytes. The existing sample-only site loader stays unchanged.

**Tech stack:** existing standard-library Python, TypeScript, Web Crypto and Node tests; no new dependency or service.

## Design and global constraints

- Version 2 is an unpublished review candidate, not a production release or approval. Bundle `{manifest,data}` contains both flows atomically. Reporting period is July 2026, HS2 09, and countries are Canada, Mexico, India and China in fixed Schedule C order.
- Data includes fixed reviewed product/country names and geographic notes, explicit per-flow statistical basis, values/statuses, world shares, selected subtotals, source/reference URLs and first retained retrieval time. Official release/revision and publication times remain null because this contract cannot infer them from acquisition time. Reference dates do not establish API vintage or historical comparability.
- Omit operational archive identities, query parameters, raw source descriptions, evidence paths, receipt flags, unselected partner codes and raw bytes. Exact field allowlists prevent their reintroduction.
- Preserve reported zero versus unobserved, partial subtotals and missing/zero world denominators. Integer USD and integer half-up share calculations avoid floating point loss. Global rankings, concentration, quantities, growth and fine-code joins remain unsupported.
- Canonical JSON uses Python's existing sorted-key, compact ASCII encoding. TypeScript must independently reproduce it, including accented labels. Hashes prove internal consistency only. Python source replay is required to verify actual values; a hash is not an official signature.
- CLI output stays in ignored `.local`, outside either input archive, and is atomic. Validation failures preserve previous output. No network, credential retrieval, new workflow, actual statistics in Git, sample-pin change or host activation.

## Task 1 — paired-flow public candidate producer and independent consumer

Files: `pipeline/public_candidate.py`, `pipeline/tests/test_public_candidate.py`, `packages/contracts/research-candidate.ts`, `tests/research-candidate.test.ts`, a conspicuously fabricated shared fixture, public-loader boundary regression, and project documentation.

Interfaces: Python `build_bundle(plan, snapshots, annexes, documents, secrets=())` and `validate_bundle(...)`; CLI takes both archive paths plus current plan/reference paths. TypeScript `validateResearchCandidate`, `validateResearchManifest`, `encodeResearchCandidate`, `loadResearchCandidate` accepts unknown/bytes, validates, snapshots and freezes results. No application imports this module yet.

1. Write failing Python and Node tests for allowlisting, source binding, paired atomic output, missing/zero arithmetic, exact scope, manifest/byte validation and sample-loader rejection. Observe RED before implementation.
2. Implement the minimal producer/reader. A shared fabricated fixture checks Python/TypeScript interoperability; it must never be described as verified Census data.
3. Run focused tests, then full Python/Node/Astro/build checks and expected production rejection. Replay actual retained fresh/recovery pairs offline through Python and TypeScript, reporting identities/counts only and preserving evidence.
4. Update handoff/status/guide with verification and limits, review diff and commit. Obtain independent whole-branch review; fix material findings with regression evidence. Run exact-head GitHub checks, merge under standing authorization, inspect merged checks/preview/actual hosting and preserve the owner's primary-checkout edit.

## Review focus

Private/public boundary; integer/status/share consistency; fixed source/flow definitions; both flows validated before atomic output; duplicate keys/noncanonical encoding/oversize rejection; async mutation isolation; no production activation; truthful source provenance and fixture labelling.

## Execution ledger

- Preflight: reused clean linked development worktree at `e4610950b674316a88af645b69d3e6c6363d4ec5`; primary owner edit and ignored evidence retained. Producer/consumer share only the documented DTO and fabricated golden fixture, not validation implementation. No external service or permission decision is needed for this offline task.
- Task 1: RED observed (nine initial Python tests fail on missing producer; Node fails on missing contract module). Added country-reference regression failed on missing geography context before its implementation. GREEN: ten focused Python and thirteen Node tests; full 305 Python tests (four pre-existing Windows skips), 118 Node tests, clean Astro checks, unchanged sample build and expected production rejection. Both actual fresh/recovery pairs pass Python/CLI/TypeScript validation with identical 5,124-byte data, unchanged input evidence and blocked website loading. Documentation and implementation are ready for independent review; no rulings or deferred findings.
- Task 1 complete: implementation committed as `218b96fefc330d10cbcca8364874eab80abcc37f`; independent whole-branch review found no actionable issues, independently passed focused tests/actual replay and 64 additional fabricated cross-language cases. Exact-head Checks `37118925206` / job `111191062409` passed 305 Python tests on Linux, 118 Node tests, clean Astro/build checks, 62 browser checks per base path and expected production rejection. PR #40 merged under standing authorization at `5043ce0d0bbc264eadcf162051b38ccd53dcb564`. No rulings, deviations or deferred findings; retained ignored source evidence and primary owner edit must survive synchronization.
