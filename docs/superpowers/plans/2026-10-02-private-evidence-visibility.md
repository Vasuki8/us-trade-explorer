# Private evidence visibility implementation plan

> **For agentic workers:** Use superpowers:executing-plans for this bounded increment and independent immutable whole-branch review. The owner delegates routine engineering and authorizes tested/reviewed merges.

**Goal:** Prevent workflows intended to retain private Census evidence from running when repository visibility is public or unknown.

**Architecture:** Keep the existing five manually dispatched ingestion/report workflows and protected environment. Evaluate visibility, main branch and manual event at the job boundary before checkout, credentials or evidence generation. Public sample checks/previews continue without claiming their artifacts are private. No service, repository visibility change, evidence deletion or public-data activation.

**Tech stack:** Existing Python pipeline and Node tests; pin the already installed YAML parser as an explicit development dependency for workflow-contract tests.

**Spec:** [Permanent operating instructions](../../../AGENTS.md), sections 2, 13, 17, 27 and repository workflow; [private diagnostic boundary](../../partner-coverage-diagnostics.md). This prerequisite follows direct GitHub verification that the repository is public, contrary to dated handoff assumptions.

## Constraints and review focus

- Check repository visibility through trusted GitHub event metadata; missing/false/nonboolean visibility fails closed. This protects dispatch contexts, not a visibility change while a private job is already running or previously retained artifacts.
- Permit only `workflow_dispatch` on `refs/heads/main` with boolean private=true; retain least privilege, environment, timeouts and pinned Actions.
- Tests parse actual YAML, discover all private evidence jobs and evaluate reviewed condition syntax against public/private/missing metadata and untrusted events/branches. They do not execute workflow code or handle credentials.
- Old evidence stays preserved locally. Existing unexpired remote artifacts may now be accessible to repository readers; identify this limit, without claiming a historical access audit or deleting them.
- Keep all publication gates false. Country-annex agreement and documented revision policy are research findings, not approved additive inventory or exact API-vintage proof.

## One coherent task

- [x] Parse workflow YAML with a pinned explicit dev dependency; write a failing regression that shows public-main evidence jobs currently run.
- [x] Gate all five Census jobs by manual event, main and strict serialized private boolean; clarify preview-artifact label.
- [x] Observe regression GREEN, verify guard truth tables, unchanged private dispatch route, action pins, permissions and no new public data.
- [x] Record current repository visibility, preserved evidence/access limitations and source-research advances in coverage/handoff/status. Prepare an unsent factual Census clarification draft only where primary documents leave material questions.
- [ ] Run applicable Python/Node/Astro/build/production checks; fix introduced failures, review diff, commit and obtain independent immutable review.
- [ ] Pass exact-head CI, merge under standing authorization, inspect main/deployment evidence, safely synchronize owner edit and record final receipts in repository/PR history.

## Execution ledger

- Initial main: `f292ddeed7ee8597f5368b95f94458a06794c9a3`; existing linked worktree reused on `fix/private-ingestion-visibility`. Primary owner edit remains untouched.
- Fresh read-only GitHub API confirms public repository (`private=false`, `visibility=public`); agent made no visibility change. Owner intent asked asynchronously; answer is not required for the reversible workflow safeguard.
- Baseline focused Python: 41 tests pass with one existing Windows capability skip outside sandbox. Sandboxed runs failed creating temporary directories, including in workspace; no pipeline change inferred from this environment limitation.
- Ruling: prioritize visibility safeguards before new private ingestion because actual repository state overrides the old private-development plan; cost if wrong is that existing private-evidence jobs are skipped until private storage is restored or redesigned.
- Regression RED observed 12 failing workflow tests under the existing branch-only conditions and inaccurate private-preview label. GREEN: all12 pass after five job guards and label correction. Full local246 Python (three existing Windows capability skips),104 Node, clean Astro/static build and expected production rejection pass; required Linux CI supplies the hosted runner/browser evidence.
- Existing dependency advisory GHSA-ch52-4w7c-c8xp has no published patched version and was already present in the lock; scoped remote-image cache applicability is documented. No unsafe forced downgrade or claim of full security scan.
