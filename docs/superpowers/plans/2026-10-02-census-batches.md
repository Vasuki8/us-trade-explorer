# Resumable Census batches implementation plan

> **For agentic workers:** Use superpowers:executing-plans; delegate the independent artifact transport and review with focused context.

**Goal:** Acquire and recover bounded explicit Census partitions, retaining immutable evidence and assembling only complete private candidate bundles.

**Architecture:** A strict plan pins up to eight singleton queries. A local journal references validated, checksum-addressed candidate objects; a complete bundle references every required slot. A main-only workflow may restore a verified prior batch artifact, then resume without repeating successful requests. This extends the approved isolated ingestion architecture.

**Tech stack:** Python 3.14 standard library; existing Census connector; pinned GitHub Actions. No new dependencies.

**Spec:** `docs/design/01-architecture.md`, `03-data-model.md`, `04-security.md`, `06-delivery-plan.md`. Continued development and reversible implementation are authorized in the conversation. Merge remains a separate concrete PR decision following the prior automatic approval review.

## Global constraints

- Eight requests per plan; one explicit HS2 product, partner, flow and month per slot. No wildcards or overlap. Preserve leading zeroes. This bounds nominal worst-case socket response/retry work below the existing 20-minute job cap; the documented OS DNS limitation remains.
- Fixed basis `census-monthly-goods-nsa-usd-v1`; strict versioned plan, candidate, journal and bundle schemas. No inference of country kind or classification comparability from a code's syntax.
- Complete requested-partition coverage is not global coverage or statistical reconciliation. Unknown official dates remain null. No private evidence enters Astro or `ReleaseStore.publish`.
- Persist objects before journal success, use unique temporary files and atomic replacement, verify existing objects before reuse, serialize local writers, retain last complete bundle after a failed refresh.
- Candidate IDs preserve current query/raw-source identity; canonical object hashes verify stored bytes. Bundle identity excludes attempt timestamps. Resume and deliberate refresh are distinct.
- Secrets only from environment. Reject credential reflections before any write; log only fixed safe categories/statuses. Restored snapshots are validated completely before persistence. No raw source payload, signed URL or credential is retained.
- Restore only completed manual `main` runs of `.github/workflows/census-batch.yml` in the specified repository, using a read-only Actions token. Check ZIP digest, paths, counts, sizes and source provenance. Never forward authorization to artifact storage.
- Private artifacts retain seven days; preserve required evidence outside expiring Actions artifacts. AWS, public official releases, subscriptions and production hosting remain later gates.

## Review focus

1. Partial refresh followed by resume must retain successful new partitions and prior complete bundle while retrying only unfinished slots.
2. A crash after object persistence but before journal success must recover without duplicates or overwriting first-ingestion evidence.
3. Restored provenance does not replace content validation; modified queries, journal references, bytes and reflected secrets must fail closed before output.
4. HTTP 204, missing observations and reported zero must remain distinguishable; only a reported numeric observation satisfies a slot.
5. Different plans or source revisions must never splice incompatible partitions into one complete bundle.

## Task 1 — Explicit contracts and immutable candidate validation

Files: `pipeline/candidates.py`, `pipeline/tests/test_batches.py`.

Interfaces: `canonical(value) -> bytes`, `digest(value) -> str`, `validate_candidate(value, slot) -> dict`; existing `fetch_candidate` output remains v2.

- [x] Write and run failing tests for missing/malformed candidate fields, query/scope/row mismatch, duplicate/extra observations, invalid timestamps, secret reflection and exact singleton outcomes.
- [x] Implement strict candidate revalidation, canonical identities and bounded JSON reading without echoing external strings.
- [x] Run pipeline tests; expected all existing and new tests pass.

## Task 2 — Journal, recovery and complete bundle

Files: `pipeline/batch.py`, `pipeline/tests/test_batches.py`.

Interfaces: `validate_plan(plan) -> canonical plan`, `run_batch(plan, root, key, refresh=False) -> bundle`, `verify_bundle(plan, root) -> bundle`, `restore_snapshot(plan, files, root, key) -> None`.

- [x] Write and run failing tests for duplicate/wildcard/oversized plans, partial failure/resume, verified cache reuse, refresh revisions, failure preserving old bundle, interruption, locks, snapshot tampering and no-results outcomes.
- [x] Implement deterministic plan/slot identities, atomic candidate/journal/bundle writes and strict reference/coverage checks.
- [x] Validate every restored file and reference in memory before creating output files. Preserve first valid object bytes on identical acquisition.
- [x] Run the full Python suite and use the real CLI with fabricated network responses; expected no duplicates, no partial bundle and no secret in output.

## Task 3 — Bounded private artifact transport

Files: `pipeline/restore.py`, `pipeline/tests/test_restore.py`.

Interface: `fetch_snapshot(repository, run_id, token) -> dict[str, bytes]`; performs no filesystem writes.

- [x] Write and run failing tests for trusted run provenance, non-forwarded authorization, archive checksums, malformed paths, duplicate/symlink members and size limits.
- [x] Implement fixed GitHub API metadata requests and a single allowlisted storage redirect, with bounded ZIP parsing and safe errors.
- [x] Run restore tests and the full pipeline suite; expected pass with only fabricated transport.

## Task 4 — Workflow, operations and review

Files: `.github/workflows/census-batch.yml`, `sources/batches/coffee-markets-2026-07.json`, `docs/census-batches.md`, `docs/census-acquisition.md`.

- [x] Add main-only manual workflow, pinned Actions, 20-minute cap, eight-slot plan, optional prior-run resume, explicit private output and failure-evidence upload.
- [x] Document commands, refresh/resume behavior, artifact expiry, recovery, source interpretation and unresolved global reconciliation/classification gates.
- [ ] Run Python suite, `npm run verify`, diff checks and GitHub Checks on the PR; frontend browser journeys remain required by existing CI.
- [x] Obtain independent whole-branch review; address material findings with regression tests.
- [ ] Create and attach a concrete PR; request merge approval only after review and CI pass. Authenticated batch execution waits for merged trusted main.

## Official evidence

The selected partner codes (Canada 1220, Mexico 2010, India 5330, China 5700) are verified in [Schedule C](https://www.census.gov/foreign-trade/schedules/c/countrycodes.html). The [API guide](https://www.census.gov/foreign-trade/reference/guides/Guide_to_International_Trade_Datasets.pdf) distinguishes world `-`, numeric groupings, explicit zeros and HTTP 204 no-record outcomes. An exact selected query avoids treating wildcard output as an exhaustive leaf inventory. See [program definitions](https://www.census.gov/foreign-trade/guide/sec2.html) for low-value statistical classifications and territory/valuation caveats. None establishes world equality from this selected market plan.

## Local verification

65 Python tests passed, including the real batch CLI with an eight-slot fabricated source. 9 Node contract tests passed; Astro reported zero errors/warnings/hints; the 30-page build passed links, sample noindex, secret-pattern and size checks. The batch tests failed before implementation. Additional regression tests demonstrated that missing ingestion credentials must block restore and that JSON-escaped GitHub token reflections must never persist; both passed after correction. No authenticated batch run is claimed. Native Windows test execution required ordinary sandbox escalation for temporary-directory access. Runtime bookkeeping remains in ignored `.local/`.

Independent whole-branch review found no runtime defects. It found that the crash test interrupted the initial pending journal rather than the post-object success write. A nonempty-object assertion reproduced the gap, then the injection was corrected to the successful journal boundary; recovery preserved the already-persisted bytes. Live Actions archive interoperability, source-vintage reconciliation and provider settings remain explicitly unverified until the corresponding systems run. Those are later gates, not inferred local passes.
