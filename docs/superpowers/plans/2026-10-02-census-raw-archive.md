# Census raw-response archive implementation plan

> **For agentic workers:** Use test-driven development and independent whole-branch review. Independent archive and handoff tasks can run in parallel; shared acquisition contracts remain with the primary implementer.

**Goal:** Preserve and independently revalidate exact private Census response bytes for the existing bounded singleton plans, while updating a durable development handoff.

**Architecture:** Add a separately named archived-batch protocol around the established candidate/bundle contracts. Raw objects are content-addressed and checked against candidate source hashes, query scope and independently reparsed rows before an archive receipt is activated. Established normalized-only workflows and artifacts remain compatible.

**Tech stack:** Python standard library, existing Astro/TypeScript website, bounded GitHub Actions.

**Spec:** Approved data-foundation requirements in `docs/design/01-architecture.md`, `03-data-model.md`, `04-security.md`, `06-delivery-plan.md`, and public release gates in `docs/operations.md`.

## Global constraints

- Existing sample/noindex website, production guard, private repository and AWS deferral remain.
- Maximum eight explicit plan slots, 64 KiB per singleton JSON/raw object, 2 MiB total snapshot and 48 archive entries; reject oversize rather than silently truncate.
- Source credentials stay in trusted main ingestion jobs, outside browser code, Git and artifacts. Known Census/GitHub reflections are rejected in raw and decoded bytes before persistence.
- Legacy candidate identities, queries, normalized-only batch restore and control-report semantics remain unchanged.
- Raw payloads and runtime evidence remain outside Git. Seven-day Actions artifacts are development evidence, not durable backups.
- Full leaf inventory, API revision vintage, exact full-world reconciliation, classification comparability and public-release projection remain separate publication gates.

## Review focus

- Escaped credential reflection, malformed JSON and incorrect hashes must fail before any raw file is saved.
- A checksum alone cannot establish a normalized observation: reparse dimensions, period, values and status from the archived raw bytes.
- Successful cached slots missing or corrupt raw objects must fail before new source requests; normalized-only historical artifacts cannot be silently upgraded.
- Failed refreshes and interrupted archive receipts preserve prior evidence, but verification must reject mismatched generation pointers until recovery.
- Private raw artifacts must not be accepted from untrusted PR/workflow sources or included in public build output.

## Task 1 — Source capture and pure snapshot validation (primary implementer)

- [x] Add failing tests for validated response capture, raw/hash/row/scope relationships, size and escaped secret checks.
- [x] Add `capture=None` to `census.fetch_candidate`: invoke `capture(raw)` once after validation, never expose credential-bearing URLs.
- [x] Add `acquire=None` to `batch.run_batch`: default uses the established fetcher; injection allows an archival wrapper without global monkeypatching.
- [x] Extract `batch.validate_snapshot(plan, files, secrets=())` from existing restore's pure checks. It validates all normalized files in memory and returns no filesystem mutations; `restore_snapshot` retains the existing empty-destination, lock and atomic-write behavior.
- [x] Implement `pipeline/raw.py`: `validate_raw_response(raw, candidate, slot, secrets=())`, `raw_bytes(root, source_hash)`, `acquire_with_raw(flow, period, key, *, product, partner, root, evidence_secrets=())`. Raw persistence occurs only after independent validation; immutable reuse rechecks bytes.

## Task 2 — Archived batches and bounded restore (independent implementer)

- [x] Add failing tests before implementing `pipeline/archive.py` and narrowly extending `pipeline/restore.py` with a separate `fetch_archived_snapshot` entry point.
- [x] Implement `run_archived_batch(plan, root, key, refresh=False, evidence_secrets=())`, `verify_archived_bundle(plan, root, secrets=())`, and `restore_archived_snapshot(plan, files, root, key, evidence_secrets=())`.
- [x] Preserve `raw/{sourceHash}.json`, normalized objects/bundles/journals and immutable `archive/{receiptId}.json` plus `archive/complete.json`. Receipt records its plan/bundle and exact verified raw references; publication remains blocked.
- [x] Cached reuse checks all stored candidates and raw objects before network access. A missing raw object cannot fall back to normalized evidence. Fresh archived acquisition must refetch historical normalized-only inputs.
- [x] In-memory restore validates every normalized/raw/receipt relationship before any destination write; reject extra/missing/path-traversal files and wrong plans. Retain narrowly validated raw orphans from interrupted writes only when their hash, secret-safe JSON, aggregate dimensions and singleton scope match an authorized plan slot. They cannot satisfy a normalized observation and are recorded without candidate IDs. Existing legacy restore still rejects raw artifact paths.
- [x] Reuse bounded HTTPS/ZIP controls with fixed main workflow `.github/workflows/census-archive.yml` and artifact `census-archive-{runId}`; no arbitrary workflow trust or authorization on signed storage redirects.
- [x] CLI mirrors the reviewed plans, resume/refresh and sanitized diagnostic conventions.

## Task 3 — Workflow, operations and handoff (primary plus independent documentation task)

- [x] Add a main-only manual archived-acquisition workflow selecting the fixed market/world plans, read-only permissions, pinned Actions, protected credentials, 20-minute cap and seven-day private artifacts including partial failures.
- [x] Document bounds, recovery, legacy migration, corruption handling and remaining publication gates in `docs/census-archive.md`.
- [x] Create/update `docs/handoff.md` with project purpose, business facts, paths, current main/review commits, live receipts, exact test commands, secret boundaries, provider limits, merge authorization and next steps. Link from README and correct stale live-verification statements.

## Task 4 — Verification and review

- [x] Run the complete pipeline suite and web contracts/check/build. Existing CI verifies both base paths, browser journeys and production rejection.
- [x] Perform one fresh read-only whole-branch review; reproduce material findings with failing tests, fix, and run the relevant suite. Review of `3b0f42d..6775535` found no findings; no fix pass was required.
- [x] Commit, push, create/attach a concrete reviewable PR, verify final CI and update handoff with its exact state. PR #13 final head `a1cb7effcd7e70af329f1bcfac76b78ff25f3901` passed Checks 37034560955; main merge `b7e470ba749679f93c026afedf916dad531e05f8` passed Checks 37035527230.
- [x] Integrate after verified implementation/review/CI under the owner's explicit standing merge permission. The owner superseded the earlier per-PR permission restriction with “from now onward you dont have to ask me for merge permission”; no further merge question is required.
- [x] Verify authenticated archived acquisition and real Actions recovery on trusted main, independently compare preserved file/receipt identities and update durable documentation with actual live receipts. Fresh market/world runs 37035812076 and 37035816019 and recovery runs 37035964431 and 37035998991 succeeded at main `b7e470ba749679f93c026afedf916dad531e05f8`. Independent bounded download/digest/inventory checks, raw reparsing and offline archive verification passed for all four copies. Markets contain 21 files/8 raw responses/8 candidates per snapshot; world contains 9 files/2 raw responses/2 candidates. Every member byte and immutable receipt identity matches within each fresh/recovery pair. Exact receipts and 9 October expiries are in `docs/handoff.md`; private development copies remain ignored and are not durable backups.
