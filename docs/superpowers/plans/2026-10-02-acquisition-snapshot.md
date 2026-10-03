# Private acquisition snapshot implementation plan

> **For agentic workers:** Use superpowers:executing-plans for this bounded increment, TDD and independent immutable whole-branch review. The owner delegates ordinary engineering decisions and authorizes tested/reviewed merges.

**Goal:** Produce a reproducible private provenance receipt for an already retained, fully validated partner response without pretending to identify its official revision generation.

**Architecture:** A pure companion builder/validator reuses the existing complete partner archive validator and optional initial-announcement verifier. An offline CLI writes only a bounded JSON receipt under ignored `.local/`, outside its input archive. Existing acquisition, scan, receipt, restore, diagnostic and public release contracts stay unchanged.

**Tech stack:** Existing standard-library Python; no dependency or infrastructure addition.

**Spec:** [Permanent instructions](../../../AGENTS.md), sections 7, 13–17, 27 and 32; [coverage review](../../census-coverage-review.md); the bounded in-chat design distinguishing retained collection, operational attempts, initial announcements and unknown API revision generation.

## Constraints and review focus

- Only the existing July 2026, chapter 09, monthly DET partner scope is supported. Flow, general-import/customs versus total-export/FAS basis, USD, nominal values and no seasonal adjustment remain explicit.
- Source URL/query, raw bytes, active scan/object/receipt identities and successful current journal are independently validated; hashes alone cannot approve a receipt. Local archive consistency does not attest original network/source authenticity.
- Candidate/scan identity excludes ingestion time and identical refresh preserves first retained time. Bind the full journal digest and distinguish its operational generation/start time from official data vintage. Do not infer an ordering between first collection and current attempt start.
- Optional announcement evidence stays nested with its initial-monthly-announcement-only claim. Unknown API release/revision/generation/update/publication/detected-revision timestamps remain null. All inventory/comparability/vintage/publication gates remain false.
- Reject tampered/rehashed receipts, nonboolean flags, secrets, unsupported dimensions, incomplete/failed refreshes, oversized/duplicate JSON and unsafe/overlapping/public output paths. Failures preserve previous output. No sockets, credentials, subprocesses, providers, external messages, visibility changes or new private ingestion.
- Receipts and local replay results remain ignored/private; no payloads, amounts or private source text enter Git/CI/browser artifacts. Public sample build and production rejection remain intact.

## One coherent task

- [x] Write meaningful failing tests for derived scope/evidence/collection semantics, nested announcement, revalidation, current-generation completeness and offline/output boundaries.
- [x] Add `pipeline/provenance.py` builder, validator and bounded CLI; observe RED then GREEN without altering existing evidence.
- [x] Replay preserved local imports/exports and announcement evidence with sockets, credential lookups and subprocesses prohibited, printing only bounded identities/counts/gates.
- [x] Update provenance documentation, handoff and status; run complete Python/Node/Astro/build/production checks, inspect diff and commit.
- [ ] Obtain independent immutable review, pass exact-final-head CI, merge under standing authorization, inspect merged-main and preview/deployment results, preserve the owner's exact edit during synchronization and record final receipts.

## Execution ledger

- Initial main `fe6fc5d55e76cda4350b0f11291fa5a854f5d673`; existing clean linked worktree reused on `feat/acquisition-snapshot`. Primary handoff edit is untouched.
- Fresh GitHub metadata confirms public repository. Existing private ingestion guards remain in place; visibility intent/private evidence execution remain unresolved. This offline task is independent of provisioning that path.
- Baseline: 82 focused partner/review/publication tests pass with two existing Windows capability skips outside sandbox. No new acquisition or credential retrieval.
- Pre-flight: the new companion consumes validated active partner state and optional verified announcement proof; it changes no shared historical evidence or public interface. Timestamp semantics match existing first-retained scan behavior and current operational journal.
- TDD: 18 initial tests RED (missing module), then GREEN. Four additional boundary tests pass; focused22 tests have one existing Windows symlink capability limitation. A public-loader regression separately rejects the new private receipt state, including a tampered approval flag, before any payload read.
- Actual offline replay: four retained fresh/recovery snapshots, both flows; source inputs unchanged, fresh/recovery companion identities equal, receipts2,844/2,851 bytes, all gates false. Sockets, credential lookups, subprocesses and publication download routines were prohibited. Private outputs remain ignored.
- Full local268 Python (four Windows capability skips),105 Node, clean50-file Astro checks, unchanged30-page sample build/8,254-byte gzipped JS and expected production rejection pass. Changed documentation: six Markdown files,124 relative links and balanced fences. No workflows/dependencies/source approvals/provider settings/public pin changed.
