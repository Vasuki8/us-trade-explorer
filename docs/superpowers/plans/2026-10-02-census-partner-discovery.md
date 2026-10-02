# Private Census partner discovery implementation plan

> **For agentic workers:** Use test-driven development and independent whole-branch review. The source adapter, scan/store and bounded restore tasks have separate owners. Update `docs/handoff.md` after each completed task and commit that receipt with its implementation.

**Goal:** Capture and independently revalidate every observed detail partner returned for the reviewed July 2026 / HS2 09 query, without claiming an approved additive inventory or public release.

**Architecture:** Extend the established source adapter with explicit DET and smaller caller limits, preserving default singleton queries/identities. A separate private discovery protocol stores immutable raw responses, sorted observations, receipts, an attempt journal and last successful pointer. A separately trusted main workflow supports bounded fresh acquisition and recovery; existing artifact protocols remain unchanged.

**Tech stack:** Standard-library Python, bounded GitHub Actions, unchanged Astro sample website.

**Spec:** Approved `docs/design/01-architecture.md`, `03-data-model.md`, `04-security.md`, `06-delivery-plan.md`, and `docs/handoff.md` publication gates. This is the next reversible data-foundation increment authorized by the owner's continued-development instruction and standing merge permission.

## Global constraints

- Fixed reviewed plan: schemaVersion 1, basis `census-monthly-goods-nsa-usd-v1`, period `2026-07`, product `09`, summaryLevel `DET`, flows `exports` and `imports`.
- Queries use `CTY_CODE=*`, explicit `SUMMARY_LVL=DET`, disjoint get/predicate fields and established aggregate dimensions. World `-` is DET; four-digit syntax does not approve a country or non-overlapping leaf.
- Maximum 500 rows, 512 KiB per source/JSON object, 2 MiB compressed/unpacked snapshot, 20 files and 24 ZIP entries. All limits reject; none truncate.
- Strict JSON, hashes, scope, dates, dimensions, status, text/known-secret checks and independent raw reparsing precede persistence or restore writes. Credentials remain in trusted main ingestion, never URLs/logs/Git/browser/public artifacts.
- Rows absent from this query are unobserved, never invented zero. Explicit zero remains reported_zero; suppression/unknown value markers fail the existing value contract.
- Numeric DET partners are `unreviewed-detail`; `-` is `world-control`. No approval of leaf inventory, API vintage/revision date, full reconciliation, classification or publication readiness.
- Immutable source/scan IDs exclude ingestion time. Identical refresh preserves first immutable objects; failed attempts retain previous pointer and record a failed current generation. Strict verification cannot mistake that prior pointer for current successful acquisition.
- Existing normalized/singleton raw protocols, source default queries and IDs, source host allowlist, sample/noindex and production guard remain compatible. AWS, spending, integrations and public launch remain deferred.

## Review focus

- Non-DET rows, conflicting dates/dimensions, duplicates, escaped secret reflection, oversized bodies/objects or more than 500 rows fail before evidence persists.
- Cached corrupt/missing historical evidence fails before network access; valid atomic temporaries/orphans from interruption remain recoverable without becoming observations.
- Failed refresh plus an old complete pointer must fail current-generation verification; recovery must finish the current attempt rather than silently use older success.
- Private restore accepts only the exact main discovery workflow/artifact protocol; its larger member limit must not weaken existing singleton restores.
- Mutable reporting aids, territory codes or apparently numeric groups cannot become approved additive leaves through discovery alone.

## Task 1 — Explicit source constraints and strict bounded decoding (primary)

Files: modify `pipeline/census.py`, `pipeline/candidates.py`; create `pipeline/tests/test_partner_source.py`.

- [x] Add failing tests, then extend `fetch_candidate(flow,period,key,*,product='09',partner='1220',capture=None,summary=None,response_limit=None,row_limit=None)`. Only None/DET summary; validate limits before requests. None preserves all established calls/queries. Explicit DET appears in predicates and is required in every row. Smaller response_limit is passed to `fetch_bytes(url,*,maximum=MAX_BYTES)`; enforce row_limit before normalization/capture.
- [x] Extend `decode(raw,secret=None,*,maximum=MAX_FILE_BYTES)` with validated integer bounds up to 2 MiB; default remains 64 KiB. Strict duplicate-field/NaN/escaped-secret behavior stays.
- [x] Verify DET import/export/world/zero fixtures, non-DET/dimension/duplicate rejection, maximum limits and unsupported parameters before network, source transport body bounds and default query/identity compatibility. Run focused source/legacy tests, update handoff, commit. Focused source/legacy suite: 30 tests passed after new tests first failed for missing interfaces.

## Task 2 — Discovery contracts, immutable store, attempt state and CLI (independent)

Files: create `pipeline/partners.py`, `pipeline/tests/test_partners.py`, `sources/scans/coffee-partners-2026-07.json`.

Interfaces: `validate_plan(plan)`; `normalize_scan(candidate,raw,*,plan,flow,secrets=())`; `validate_snapshot(plan,flow,files,secrets=(),require_complete=False)`; `run_partner_scan(plan,flow,root,key,refresh=False,evidence_secrets=())`; `verify_partner_scan(plan,flow,root,secrets=())`; `restore_partner_snapshot(plan,flow,files,root,key,evidence_secrets=())`.

- [ ] Test first: raw/candidate/schema/query/scope/row/hash mismatch, larger strict JSON bounds, sorted observed roles, absent world/unknown numeric codes preserved, zero and no-results distinctions, idempotence, corruption before networking, interruption/orphan/temp recovery, failed refresh, generation mismatch, immutable history and restore-before-write limits.
- [ ] Store `raw/{sourceHash}.json`, `scans/{scanId}.json`, `receipts/{receiptId}.json`, `progress.json`, `complete.json` (receiptId). Use controlled local writer locks/atomic writes. Every historical scan requires its raw evidence. Validate unreferenced raw scope/hash/secrets but never count it as a completed observation. Ignore/retain regular `.pending-*` temporaries after rejecting symlinks.
- [ ] Normalize validated schema-v2 source candidate into a versioned private discovery scan: canonical query/source identity excluding ingestion time, sorted rows, observed `(code,name,role)` list, null official dates, basis and fixed publication blockers. `state=private-partner-discovery`, `coverage=observed-partners-only`, `leafInventoryApproved=false`, `apiVintageVerified=false`, `publicationReady=false`. Receipt binds plan/scan/object/raw hashes and counts. No source amounts appear in diagnostics.
- [ ] Journal pending/successful/failed attempts with safe category/status/time, and scan/receipt refs only on success. Current verification requires successful journal matching the pointed receipt; failed refresh preserves earlier pointer but cannot verify as new success. Recoverable complete objects without a journal success are revalidated and retried safely.
- [ ] CLI `--plan`, `--flow`, `--output`, `--refresh`, `--resume-run`, `--repository`; validates trusted snapshot via `pipeline.restore.fetch_partner_snapshot` before restore. Output fixed counts/private-blocked state, sanitized failures. Root records focused verification and handoff completion before task commit.

## Task 3 — Separate trusted artifact transport (independent)

Files: narrowly modify `pipeline/restore.py`; create `pipeline/tests/test_partner_restore.py`.

- [ ] Failing tests then `fetch_partner_snapshot(repository,run_id,token)` trusting only completed manual main `.github/workflows/census-partners.yml` and `census-partners-{runId}`. Failure artifacts remain selectable for recovery; core validators decide complete generation.
- [ ] New mode allows only raw/scans/receipts hash JSON, progress.json and complete.json, 512 KiB members, 20 files/24 ZIP entries, 2 MiB total. Existing normalized/archived modes retain exactly their bounds, paths and trust.
- [ ] Cover metadata, digest, redirects/authorization, traversal, symlink/type, oversized/duplicate/extra entries, protocol confusion, prior modes still rejecting new paths/large members. Update handoff and commit after root integration verification.

## Task 4 — Workflow, operator guide, review and live receipt (primary)

- [ ] Add main-only manual `.github/workflows/census-partners.yml` with flow choice, validated refresh/resume env inputs, fixed plan, shared concurrency, pinned Actions, read-only permissions, protected repository secret, twenty-minute job cap and seven-day private partial artifacts excluding locks/temporaries.
- [ ] Write `docs/census-partners.md` with definitions, bounded operation/restore, failure recovery, source evidence and unresolved inventory/vintage gates. Link README/status/handoff; record completed task receipts as they occur.
- [ ] Full Python suite, web contracts/check/build, documentation links/whitespace and one fresh whole-branch review. Fix material findings test-first. Create/attach PR, final-head CI, merge under standing permission and verify merged-main checks. No new permission request.
- [ ] Fresh authenticated import/export discovery and Actions recovery on trusted main; independently inspect raw/candidate/receipt/generation and every-byte recovery. Preserve verified private evidence; update handoff with exact results before task completion. Do not claim live verification before successful runs and independent checks.
